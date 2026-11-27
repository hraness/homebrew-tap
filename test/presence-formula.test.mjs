import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { admit, assetName, assetUrl, parseFormula, releaseRecord, renderFormula, sidecarDigest } from "../tools/presence-formula.mjs";

const A = "a".repeat(64);
const B = "b".repeat(64);
const release = (version, digest = A, extra = {}) => ({
  tag_name: `v${version}`,
  draft: false,
  prerelease: false,
  assets: [
    { name: assetName(version), digest: `sha256:${digest}`, browser_download_url: assetUrl(version) },
    { name: `${assetName(version)}.sha256`, digest: `sha256:${B}`, browser_download_url: `${assetUrl(version)}.sha256` },
  ],
  ...extra,
});

test("the checked-in formula is the generator output", () => {
  const record = parseFormula(readFileSync("Formula/presence.rb", "utf8"));
  assert.match(record.version, /^\d+\.\d+\.\d+$/);
});

test("render and parse round-trip", () => {
  const record = { version: "1.2.3", sha256: A };
  const text = renderFormula(record);
  assert.deepEqual(parseFormula(text), record);
  assert.ok(text.includes(`url "https://github.com/hraness/presence/releases/download/v1.2.3/presence-1.2.3-macos-universal.tar.gz"`));
  assert.throws(() => parseFormula(text.replace("license", "license  ")), /differs/);
});

test("releaseRecord takes the exact archive and its GitHub digest", () => {
  assert.deepEqual(releaseRecord(release("0.2.0")), { version: "0.2.0", sha256: A, sidecarUrl: `${assetUrl("0.2.0")}.sha256` });
  assert.throws(() => releaseRecord(release("0.2.0", A, { prerelease: true })), /prerelease/);
  assert.throws(() => releaseRecord(release("0.2.0", A, { draft: true })), /published/);
  assert.throws(() => releaseRecord(release("0.2.0", A, { tag_name: "0.2.0" })), /tag/);
  const noDigest = release("0.2.0"); delete noDigest.assets[0].digest;
  assert.throws(() => releaseRecord(noDigest), /digest/);
  const noSidecar = release("0.2.0"); noSidecar.assets.pop();
  assert.throws(() => releaseRecord(noSidecar), /sha256/);
});

test("sidecar must name the archive", () => {
  assert.equal(sidecarDigest(`${A}  ${assetName("0.2.0")}\n`, "0.2.0"), A);
  assert.throws(() => sidecarDigest(`${A}  other.tar.gz\n`, "0.2.0"), /Malformed/);
});

test("admit moves forward only and keeps an admitted archive", () => {
  const current = { version: "0.1.0", sha256: A };
  assert.deepEqual(admit(current, { version: "0.1.0", sha256: A }), current);
  assert.deepEqual(admit(current, { version: "0.10.0", sha256: B }), { version: "0.10.0", sha256: B });
  assert.throws(() => admit({ version: "0.2.0", sha256: A }, { version: "0.1.9", sha256: B }), /rollback/);
  assert.throws(() => admit(current, { version: "0.1.0", sha256: B }), /changed its archive/);
});
