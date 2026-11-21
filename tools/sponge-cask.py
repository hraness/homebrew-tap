"""Maintain the Sponge Mac cask from its public release and Sparkle appcast."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import plistlib
import re
import subprocess
import tempfile
from urllib.request import build_opener, HTTPRedirectHandler, Request
from xml.etree import ElementTree
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog/sponge-app.json"
CASK = ROOT / "Casks/sponge-app.rb"
ORIGIN = "https://sponge.computer"
FEED = ORIGIN + "/mac/appcast.xml"
PUBLIC_KEY = "TQzSqF7YLQJplO0GRURw+7HySDcrtm8gk5m8vfX/jWc="
SPARKLE = "{http://www.andymatuschak.org/xml-namespaces/sparkle}"
FIELDS = ("version", "build", "length", "sha256", "minimumSystemVersion", "signature")
ARCHIVE_LIMIT = 16 * 1024**2


def need(value, message):
    if not value:
        raise ValueError(message)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(url, limit):
    request = Request(url, headers={"Accept-Encoding": "identity", "Cache-Control": "no-cache",
                                   "User-Agent": "Hraness-Homebrew-Tap/1 (+https://github.com/hraness/homebrew-tap)"})
    with build_opener(NoRedirect).open(request, timeout=40) as response:
        length = response.headers.get("Content-Length")
        need(length is None or (length.isdecimal() and int(length) <= limit), "Response exceeds size limit")
        data = response.read(limit + 1)
        need(len(data) <= limit and (length is None or int(length) == len(data)), "Oversized or incomplete response")
        return data


def archive_url(record):
    return f"{ORIGIN}/downloads/{record['sha256']}/Sponge-{record['version']}.zip"


def validate(record):
    need(isinstance(record, dict) and set(record) == set(FIELDS), "Incomplete Sponge catalog entry")
    version = record["version"]
    need(isinstance(version, str) and re.fullmatch(r"(0|[1-9][0-9]{0,8})(\.(0|[1-9][0-9]{0,8})){2}", version), "Invalid app version")
    need(isinstance(record["build"], str) and re.fullmatch(r"[1-9][0-9]{0,8}", record["build"]), "Invalid build")
    need(type(record["length"]) is int and 0 < record["length"] <= ARCHIVE_LIMIT, "Invalid archive length")
    need(isinstance(record["sha256"], str) and re.fullmatch(r"[a-f0-9]{64}", record["sha256"]), "Invalid archive digest")
    need(record["minimumSystemVersion"] == "15.0", "Update the cask's platform requirement for this release")
    signature = base64.b64decode(record["signature"], validate=True)
    need(len(signature) == 64 and base64.b64encode(signature).decode() == record["signature"], "Invalid Sparkle signature")
    return record


def release_record(manifest, appcast):
    record = validate({key: manifest.get(key) for key in FIELDS})
    need(len(appcast) <= 131072, "Unsupported appcast")
    xml = appcast.decode("utf-8")
    need(not re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", xml, re.IGNORECASE), "Unsupported appcast")
    channel = ElementTree.fromstring(xml)
    items = channel.findall("./channel/item")
    need(channel.tag == "rss" and len(items) == 1, "Expected one active appcast item")
    item = items[0]
    for tag, key in (("version", "build"), ("shortVersionString", "version"), ("minimumSystemVersion", "minimumSystemVersion")):
        values = item.findall(SPARKLE + tag)
        need(len(values) == 1 and values[0].text == record[key], f"Appcast {tag} differs from the release")
    enclosures = item.findall("enclosure")
    need(len(enclosures) == 1, "Expected one archive enclosure")
    expected = {"url": archive_url(record), "length": str(record["length"]),
                "type": "application/octet-stream", SPARKLE + "edSignature": record["signature"]}
    need(all(enclosures[0].get(key) == value for key, value in expected.items()), "Appcast archive differs from the release")
    return record


def admit(previous, candidate):
    validate(previous)
    validate(candidate)
    if candidate != previous:
        old_version = tuple(map(int, previous["version"].split(".")))
        new_version = tuple(map(int, candidate["version"].split(".")))
        need(new_version > old_version and int(candidate["build"]) > int(previous["build"]),
             "Version and build must both advance; a published release cannot change")
        need(candidate["sha256"] != previous["sha256"], "Reusing an earlier archive is not an update")


def verify_archive(data, record, public_key=PUBLIC_KEY):
    validate(record)
    need(len(data) == record["length"] and hashlib.sha256(data).hexdigest() == record["sha256"], "Archive digest or length mismatch")
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory)
        key = bytes.fromhex("302a300506032b6570032100") + base64.b64decode(public_key, validate=True)
        (path / "key.der").write_bytes(key)
        (path / "signature").write_bytes(base64.b64decode(record["signature"]))
        (path / "Sponge.zip").write_bytes(data)
        verified = subprocess.run(["openssl", "pkeyutl", "-verify", "-rawin", "-pubin", "-keyform", "DER",
                                   "-inkey", "key.der", "-sigfile", "signature", "-in", "Sponge.zip"],
                                  cwd=path, timeout=20, capture_output=True)
        need(verified.returncode == 0, "Archive signature does not match the Sponge update key")
    with ZipFile(io.BytesIO(data)) as archive:
        entries = [entry for entry in archive.infolist() if entry.filename == "Sponge.app/Contents/Info.plist"]
        need(len(entries) == 1 and 0 < entries[0].file_size <= 262144, "Expected one bounded app Info.plist")
        plist = plistlib.loads(archive.read(entries[0]))
    identity = {"CFBundleIdentifier": "com.hraness.sponge.mac", "CFBundleShortVersionString": record["version"],
                "CFBundleVersion": record["build"], "LSMinimumSystemVersion": record["minimumSystemVersion"],
                "SUPublicEDKey": public_key, "SUFeedURL": FEED}
    need(all(plist.get(key) == value for key, value in identity.items()), "Signed app identity differs from the catalog")


def render(record):
    validate(record)
    return f'''cask "sponge-app" do
  version "{record["version"]}"
  sha256 "{record["sha256"]}"

  url "{ORIGIN}/downloads/{record["sha256"]}/Sponge-#{{version}}.zip"
  name "Sponge"
  desc "Reading library with share-menu, menu bar and shortcut saving"
  homepage "{ORIGIN}/mac"

  livecheck do
    url "{FEED}"
    strategy :sparkle, &:short_version
  end

  auto_updates true
  depends_on macos: :sequoia

  app "Sponge.app"
end
'''


def active(fetcher):
    manifest = json.loads(fetcher(ORIGIN + "/mac/release.json", 131072))
    return release_record(manifest, fetcher(FEED, 131072))


def refresh(previous, fetcher=fetch, verifier=verify_archive):
    record = active(fetcher)
    admit(previous, record)
    if record != previous:
        verifier(fetcher(archive_url(record), record["length"]), record)
        need(active(fetcher) == record, "Active release changed during verification; retry")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--refresh", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--previous", type=Path, help="Compare with the base branch's catalog record")
    parser.add_argument("--archive", action="store_true", help="Verify the immutable archive named in the catalog")
    args = parser.parse_args()
    record = validate(json.loads(CATALOG.read_text()))
    if args.previous:
        admit(json.loads(args.previous.read_text()), record)
    need(CASK.read_text() == render(record), "Cask differs from the admitted Sponge catalog entry")
    if args.archive:
        verify_archive(fetch(archive_url(record), record["length"]), record)
    if args.refresh:
        next_record = refresh(record)
        if next_record != record:
            CATALOG.write_text(json.dumps(next_record, indent=2) + "\n")
            CASK.write_text(render(next_record))
            record = next_record
    print(f"Sponge {record['version']} cask verified")


if __name__ == "__main__":
    main()
