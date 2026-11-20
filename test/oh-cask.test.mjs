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
  assert.match(cask, /binary "#\{appdir\}\/Oh\.app\/Contents\/Helpers\/oh-router"/);
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
});
