import assert from "node:assert/strict";
import test from "node:test";
import { admitUpdate, releaseRecord, renderCask } from "../tools/oh-cask.mjs";
import { admitRouterUpdate, renderFormula, validateRouterRelease } from "../tools/oh-router-formula.mjs";

const SAMPLE_SHA = "a".repeat(64);
const SAMPLE_SIG = "A".repeat(86) + "==";

test("oh-cask validates release.json and appcast.xml and renders Casks/oh.rb", () => {
  const manifest = {
    schemaVersion: 1,
    release: {
      version: "0.1.0",
      build: "2",
      channel: "stable",
      architecture: "arm64",
      minimumMacOS: "15.0",
      sha256: SAMPLE_SHA,
      url: `https://oh.computer/downloads/${SAMPLE_SHA}/OH-0.1.0.zip`,
      notarization: {
        status: "Accepted",
        stapleValidated: true,
        gatekeeperAccepted: true,
      },
      sparkle: {
        length: 10485760,
        edSignature: SAMPLE_SIG,
      },
    },
  };
  const appcast = `<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle">
  <channel>
    <title>OH</title>
    <item>
      <title>OH 0.1.0</title>
      <sparkle:version>2</sparkle:version>
      <sparkle:shortVersionString>0.1.0</sparkle:shortVersionString>
      <sparkle:minimumSystemVersion>15.0</sparkle:minimumSystemVersion>
      <sparkle:hardwareRequirements>arm64</sparkle:hardwareRequirements>
      <enclosure url="https://oh.computer/downloads/${SAMPLE_SHA}/OH-0.1.0.zip" length="10485760" type="application/octet-stream" sparkle:edSignature="${SAMPLE_SIG}"/>
    </item>
  </channel>
</rss>`;

  const record = releaseRecord(manifest, appcast);
  assert.equal(record.product, "oh");
  assert.equal(record.version, "0.1.0");
  assert.equal(record.build, "2");

  const cask = renderCask(record);
  assert.match(cask, /cask "oh" do/);
  assert.match(cask, /app "Oh\.app"/);
  assert.doesNotMatch(cask, /^\s*binary\s/m);
  assert.throws(() => admitUpdate(record, { ...record, build: "1" }), /rollback/i);
});

test("oh-router-formula validates multi-platform release manifest and renders Formula/oh-router.rb", () => {
  const s1 = "1".repeat(64);
  const s2 = "2".repeat(64);
  const s3 = "3".repeat(64);
  const manifest = {
    schemaVersion: 1,
    version: "0.1.0",
    targets: {
      "aarch64-apple-darwin": {
        sha256: s1,
        url: `https://ohrouter.com/downloads/${s1}/oh-router-v0.1.0-aarch64-apple-darwin.tar.gz`,
      },
      "x86_64-unknown-linux-gnu": {
        sha256: s2,
        url: `https://ohrouter.com/downloads/${s2}/oh-router-v0.1.0-x86_64-unknown-linux-gnu.tar.gz`,
      },
      "aarch64-unknown-linux-musl": {
        sha256: s3,
        url: `https://ohrouter.com/downloads/${s3}/oh-router-v0.1.0-aarch64-unknown-linux-musl.tar.gz`,
      },
    },
  };
  const record = validateRouterRelease(manifest);
  const formula = renderFormula(record);
  assert.match(formula, /class OhRouter < Formula/);
  assert.match(formula, /%w\[oh-router ohd oh-holder\]/);
  assert.match(formula, /license any_of: \["MIT", "Apache-2\.0"\]/);
  assert.match(formula, /on_macos do[\s\S]*?depends_on arch: :arm64\s+end/);
  assert.throws(() => validateRouterRelease({ ...manifest, targets: { ...manifest.targets, "x86_64-unknown-linux-gnu": { sha256: s2, url: `https://example.com/downloads/${s2}/oh-router-v0.1.0-x86_64-unknown-linux-gnu.tar.gz` } } }), /Unexpected archive URL/);

  const release = (version, digest) => ({
    schemaVersion: 1,
    version,
    targets: Object.fromEntries(Object.keys(manifest.targets).map((target) => [target, {
      sha256: digest,
      url: `https://ohrouter.com/downloads/${digest}/oh-router-v${version}-${target}.tar.gz`,
    }])),
  });
  assert.equal(admitRouterUpdate(null, manifest).version, "0.1.0");
  assert.equal(admitRouterUpdate(record, manifest).version, "0.1.0");
  assert.equal(admitRouterUpdate(record, release("0.1.1", "4".repeat(64))).version, "0.1.1");
  assert.throws(() => admitRouterUpdate(release("0.2.0", s1), manifest), /rollback/i);
  assert.throws(() => admitRouterUpdate(record, release("0.1.0", "5".repeat(64))), /cannot change/);

  const intelRelease = release("0.1.1", "4".repeat(64));
  const intelChecksum = "5".repeat(64);
  const intelUrl = `https://ohrouter.com/downloads/${intelChecksum}/oh-router-v0.1.1-x86_64-apple-darwin.tar.gz`;
  intelRelease.targets["x86_64-apple-darwin"] = { sha256: intelChecksum, url: intelUrl };
  const intelFormula = renderFormula(admitRouterUpdate(record, intelRelease));
  assert.ok(intelFormula.includes(`on_intel do\n      url "${intelUrl}"`));
  assert.doesNotMatch(intelFormula, /depends_on arch: :arm64/);
  assert.throws(() => admitRouterUpdate(intelRelease, release("0.1.1", "4".repeat(64))), /cannot change/);
});

test("oh-router accepts the ohputer.com/router origin and the former ohrouter.com origin", () => {
  const targets = ["aarch64-apple-darwin", "x86_64-unknown-linux-gnu", "aarch64-unknown-linux-musl"];
  const release = (version, origin, digest = (target) => String(targets.indexOf(target) + 6).repeat(64)) => ({
    schemaVersion: 1,
    version,
    targets: Object.fromEntries(targets.map((target) => [target, {
      sha256: digest(target),
      url: `${origin}/downloads/${digest(target)}/oh-router-v${version}-${target}.tar.gz`,
    }])),
  });
  const NEW = "https://ohputer.com/router";
  const OLD = "https://ohrouter.com";
  assert.equal(validateRouterRelease(release("0.1.13", NEW)).targets["aarch64-apple-darwin"].url, `${NEW}/downloads/${"6".repeat(64)}/oh-router-v0.1.13-aarch64-apple-darwin.tar.gz`);
  assert.equal(validateRouterRelease(release("0.1.9", OLD)).version, "0.1.9");

  // A real update from an old-origin record to a new-origin manifest.
  const moved = admitRouterUpdate(release("0.1.9", OLD), release("0.1.13", NEW));
  assert.equal(moved.version, "0.1.13");
  const formula = renderFormula(moved);
  assert.ok(formula.includes(`url "${NEW}/downloads/`));
  assert.ok(formula.includes(`homepage "${NEW}"`));
  assert.doesNotMatch(formula, /ohrouter\.com/);

  // Same version moving origin keeps identity; a changed digest or rollback does not pass.
  assert.equal(admitRouterUpdate(release("0.1.13", OLD), release("0.1.13", NEW)).version, "0.1.13");
  assert.throws(() => admitRouterUpdate(release("0.1.13", OLD), release("0.1.13", NEW, () => "f".repeat(64))), /cannot change/);
  assert.throws(() => admitRouterUpdate(release("0.1.13", NEW), release("0.1.9", OLD)), /rollback/i);

  // Look-alike origins, a digest that differs from the path, and plain http stay refused.
  for (const origin of ["https://ohputer.com", "https://ohputer.com/router/x", "https://evil.ohputer.com/router", "http://ohputer.com/router", "https://ohrouter.com.evil.test"]) {
    assert.throws(() => validateRouterRelease(release("0.1.13", origin)), /Unexpected archive URL/, origin);
  }
  const mismatched = release("0.1.13", NEW);
  mismatched.targets["aarch64-apple-darwin"].sha256 = "e".repeat(64);
  assert.throws(() => validateRouterRelease(mismatched), /Unexpected archive URL/);
});
