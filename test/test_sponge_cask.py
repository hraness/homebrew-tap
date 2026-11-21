import base64
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest
from zipfile import ZipFile

path = Path(__file__).resolve().parents[1] / "tools/sponge-cask.py"
spec = importlib.util.spec_from_file_location("sponge_cask", path)
sponge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sponge)


def feed(record):
    return f'''<rss xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle"><channel><item>
<sparkle:version>{record["build"]}</sparkle:version><sparkle:shortVersionString>{record["version"]}</sparkle:shortVersionString>
<sparkle:minimumSystemVersion>15.0</sparkle:minimumSystemVersion>
<enclosure url="{sponge.archive_url(record)}" type="application/octet-stream" length="{record["length"]}" sparkle:edSignature="{record["signature"]}"/>
</item></channel></rss>'''.encode()


class SpongeCask(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.work.cleanup)
        work = Path(cls.work.name)
        def openssl(*args):
            return subprocess.check_output(["openssl", *args], cwd=work, timeout=20)
        openssl("genpkey", "-algorithm", "ED25519", "-out", "private.pem")
        der = openssl("pkey", "-in", "private.pem", "-pubout", "-outform", "DER")
        cls.key = base64.b64encode(der[-32:]).decode()
        buf = io.BytesIO()
        with ZipFile(buf, "w") as archive:
            archive.writestr("Sponge.app/Contents/Info.plist", plistlib.dumps(dict(
                CFBundleIdentifier="com.hraness.sponge.mac", CFBundleShortVersionString="1.2.5", CFBundleVersion="13",
                LSMinimumSystemVersion="15.0", SUPublicEDKey=cls.key, SUFeedURL=sponge.FEED)))
        cls.data = buf.getvalue()
        (work / "archive").write_bytes(cls.data)
        signature = openssl("pkeyutl", "-sign", "-rawin", "-inkey", "private.pem", "-in", "archive")
        cls.record = dict(version="1.2.5", build="13", length=len(cls.data), sha256=hashlib.sha256(cls.data).hexdigest(),
                          minimumSystemVersion="15.0", signature=base64.b64encode(signature).decode())
        cls.previous = dict(cls.record, version="1.2.4", build="12", sha256="a"*64)

    def test_two_public_surfaces_and_exact_signed_bundle(self):
        record = self.record
        self.assertEqual(sponge.CASK.name, "sponge-app.rb")
        self.assertEqual(sponge.CATALOG.name, "sponge-app.json")
        self.assertTrue(sponge.render(record).startswith('cask "sponge-app" do\n'))
        self.assertEqual(record, sponge.release_record({**record, "published": "2026-10-21"}, feed(record)))
        sponge.verify_archive(self.data, record, self.key)
        for changed in (dict(version="1.2.6"), dict(build="14")):
            with self.assertRaisesRegex(ValueError, "Signed app identity"):
                sponge.verify_archive(self.data, {**record, **changed}, self.key)
        with self.assertRaisesRegex(ValueError, "signature"):
            sponge.verify_archive(self.data, record)
        with self.assertRaisesRegex(ValueError, "digest"):
            sponge.verify_archive(self.data+b"x", record, self.key)

    def test_mismatched_scope_or_metadata_fails_closed(self):
        body = feed(self.record)
        for invalid in (body.replace(b"sponge.computer/downloads", b"another.example/downloads"),
                        body.replace(b"<sparkle:version>13</", b"<sparkle:version>12</"),
                        body.replace(b'length="', b'length="99'),
                        body.replace(b"<item>", b"<item/><item>"),
                        b"<!DOCTYPE rss>"+body):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                sponge.release_record(self.record, invalid)

    def test_both_version_and_build_advance(self):
        sponge.admit(self.previous, self.record)
        sponge.admit(self.record.copy(), self.record)
        for changed in (dict(version="1.2.4"), dict(version="1.2.5", build="14"), dict(build="12", version="1.3.0"),
                        dict(version="1.2.5", sha256="b"*64), dict(version="1.3.0", build="14")):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                sponge.admit(self.record, {**self.record, **changed})

    def test_refresh_requires_stable_feed_and_checks_changed_bytes_before_returning(self):
        calls = []
        release = sponge.ORIGIN + "/mac/release.json"
        def fetcher(url, limit):
            calls.append(url)
            return {release: json.dumps(self.record).encode(), sponge.FEED: feed(self.record), sponge.archive_url(self.record): self.data}[url]
        verifier = lambda data, record: sponge.verify_archive(data, record, self.key)
        self.assertEqual(sponge.refresh(self.previous, fetcher, verifier), self.record)
        self.assertEqual(calls, [release, sponge.FEED, sponge.archive_url(self.record), release, sponge.FEED])
        calls.clear()
        self.assertEqual(sponge.refresh(self.record, fetcher, verifier), self.record)
        self.assertEqual(calls, [release, sponge.FEED])
        calls.clear()
        def racing(url, limit):
            result = fetcher(url, limit)
            if calls.count(release) > 1:
                other = dict(self.record, build="14", version="1.3.0")
                return json.dumps(other).encode() if url == release else feed(other)
            return result
        with self.assertRaisesRegex(ValueError, "changed during"):
            sponge.refresh(self.previous, racing, verifier)
