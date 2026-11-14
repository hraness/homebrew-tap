import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { admitUpdate, readCurrent, releaseRecord, renderCask, verifyArchive } from "../tools/yaptake-cask.mjs";

const record = { schemaVersion: 1, product: "yaptake", version: "0.1.0", build: "225", url: `https://yaptake.com/downloads/${"a".repeat(64)}/Yaptake-0.1.0-private.zip`, sha256: "a".repeat(64), length: 42, architecture: "arm64", minimumMacOS: "26.0", edSignature: Buffer.alloc(64).toString("base64") };
const manifest = { schemaVersion: 1, release: { ...record, channel: "preview", notarization: { status: "Accepted", stapleValidated: true, gatekeeperAccepted: true }, sparkle: { length: record.length, edSignature: record.edSignature } } };
const feed = `<rss><channel><item><sparkle:version>225</sparkle:version><sparkle:shortVersionString>0.1.0</sparkle:shortVersionString><sparkle:minimumSystemVersion>26.0</sparkle:minimumSystemVersion><sparkle:hardwareRequirements>arm64</sparkle:hardwareRequirements><enclosure url="${record.url}" length="42" sparkle:edSignature="${record.edSignature}"/></item></channel></rss>`;

test("the cask version uses both app version and build, with user data outside uninstall effects", () => {
  assert.deepEqual(releaseRecord(manifest, feed), record);
  const text = renderCask(record);
  assert(text.includes('version "0.1.0,225"'));
  assert(text.includes('depends_on arch: :arm64')); assert(text.includes('depends_on macos: :tahoe'));
  assert(text.includes('Contents/Helpers/yaptake')); assert(!/zap |uninstall |delete|rmdir|rm_rf/.test(text));
  assert(!text.includes("github.com/hraness/yaptake"));
});

test("the Ruby cask resolves the canonical URL and detects builds sharing an app version", () => {
  const ruby = String.raw`
require "json"
require "rexml/document"
class CaskProbe
  attr_reader :download, :check, :strategy_name
  Version = Struct.new(:value) do
    def csv
      value.split(",")
    end
  end
  def version(value = nil)
    value ? @version = Version.new(value) : @version
  end
  def url(value)
    @download = value unless @in_livecheck
  end
  def appdir
    "/Applications"
  end
  def livecheck(&block)
    @in_livecheck = true
    instance_eval(&block)
  ensure
    @in_livecheck = false
  end
  def strategy(name, &block)
    @strategy_name = name
    @check = block
  end
  def method_missing(*)
    nil
  end
end
input = JSON.parse(STDIN.read)
probe = CaskProbe.new
define_singleton_method(:cask) { |_name, &block| probe.instance_eval(&block) }
eval(input.fetch("cask"), TOPLEVEL_BINDING)
puts JSON.generate({ url: probe.download, strategy: probe.strategy_name, versions: input.fetch("feeds").map { |xml| probe.check.call(REXML::Document.new(xml)) } })
`;
  const namespaced = feed.replace("<rss>", '<rss xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle">');
  const result = spawnSync("ruby", ["-e", ruby], { encoding: "utf8", input: JSON.stringify({ cask: renderCask(record), feeds: [namespaced, namespaced.replace("<sparkle:version>225", "<sparkle:version>226"), namespaced.replace("<sparkle:version>225", "<sparkle:version>bad"), namespaced.replace("<sparkle:shortVersionString>0.1.0", "<sparkle:shortVersionString>")] }) });
  assert.equal(result.status, 0, result.stderr || String(result.error));
  assert.deepEqual(JSON.parse(result.stdout), { url: record.url, strategy: "xml", versions: [["0.1.0,225"], ["0.1.0,226"], [], []] });
});

test("runtime updates refuse a rollback and replacement of an admitted version/build", () => {
  assert.equal(admitUpdate(record, { ...record, build: "226" }).build, "226");
  assert.throws(() => admitUpdate(record, { ...record, build: "224" }), /rollback/);
  const older = { ...record, version: "0.0.9", build: "226", url: record.url.replace("Yaptake-0.1.0", "Yaptake-0.0.9") };
  assert.throws(() => admitUpdate(record, older), /rollback/);
  assert.throws(() => admitUpdate(record, { ...record, length: 43 }), /cannot change/);
});

test("release and appcast must agree on archive, signature, platform and exact build", () => {
  for (const changed of [feed.replace("<sparkle:version>225", "<sparkle:version>bad"), feed.replace('length="42"', 'length="41"'), feed.replace("arm64", "x86_64"), feed.replace(record.url, "https://example.com/app.zip"), feed.replace("</item>", "</item><item></item>"), "<!DOCTYPE rss>" + feed]) assert.throws(() => releaseRecord(manifest, changed));
  assert.throws(() => releaseRecord({ schemaVersion: 1, release: null }, feed), /No active/);
  assert.throws(() => releaseRecord({ ...manifest, release: { ...manifest.release, notarization: { status: "Accepted" } } }, feed), /admission/);
});

test("a changed upstream release cannot be mixed into a refresh", async () => {
  let reads = 0;
  const fake = async (url) => { const value = url.endsWith("release.json") ? JSON.stringify(manifest) : (++reads > 1 ? feed + "\n" : feed); return new Response(value); };
  await assert.rejects(readCurrent(fake), /changed during/);
});

test("archive verification refuses wrong bytes before native installation", async () => {
  const root = await mkdtemp(join(tmpdir(), "yaptake-cask-"));
  try { const path = join(root, "app.zip"); await writeFile(path, "not an admitted app"); await assert.rejects(verifyArchive(path, record), /bounded regular/); }
  finally { await rm(root, { recursive: true, force: true }); }
});
