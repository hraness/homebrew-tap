#!/usr/bin/env node
// Regenerate Formula/oh-router.rb from https://ohrouter.com/release.json
// (or a local release.json file via --from <path>), verifying each target's
// immutable content-addressed URL and SHA-256 digest.
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const ORIGIN = "https://ohrouter.com";
const TARGETS = [
  "aarch64-apple-darwin",
  "x86_64-unknown-linux-gnu",
  "aarch64-unknown-linux-musl",
];

const need = (value, message) => { if (!value) throw new Error(message); };
const json = (value) => `${JSON.stringify(value, null, 2)}\n`;

export function validateRouterRelease(manifest) {
  need(manifest?.schemaVersion === 1 && typeof manifest.version === "string" && /^(0|[1-9]\d{0,8})\.(0|[1-9]\d{0,8})\.(0|[1-9]\d{0,8})$/.test(manifest.version), "Invalid oh-router release version");
  need(manifest.targets && typeof manifest.targets === "object", "Missing oh-router release targets");
  const v = manifest.version;
  const out = { schemaVersion: 1, product: "oh-router", version: v, targets: {} };
  for (const target of TARGETS) {
    const entry = manifest.targets[target];
    need(entry && typeof entry.sha256 === "string" && /^[a-f0-9]{64}$/.test(entry.sha256), `Missing valid sha256 for ${target}`);
    const expectedName = `oh-router-v${v}-${target}.tar.gz`;
    const expectedUrl = `${ORIGIN}/downloads/${entry.sha256}/${expectedName}`;
    need(entry.url === expectedUrl, `Unexpected archive URL for ${target}: ${entry.url}`);
    out.targets[target] = { sha256: entry.sha256, url: entry.url };
  }
  return out;
}

// A refresh may only move forward, and an admitted version keeps its exact
// archive identities.
export function admitRouterUpdate(previous, next) {
  const admitted = validateRouterRelease(next);
  if (!previous) return admitted;
  const current = validateRouterRelease(previous);
  const a = current.version.split(".").map(Number);
  const b = admitted.version.split(".").map(Number);
  const first = a.findIndex((part, index) => part !== b[index]);
  need(first < 0 || b[first] > a[first], "Version rollback refused");
  if (first < 0) need(json(current) === json(admitted), "An admitted version cannot change its archive identity");
  return admitted;
}

async function readRelease() {
  const res = await fetch(`${ORIGIN}/release.json`, { redirect: "error", signal: AbortSignal.timeout(20000), headers: { "cache-control": "no-cache" } });
  need(res.ok, `HTTP ${res.status} fetching ${ORIGIN}/release.json`);
  const chunks = []; let size = 0;
  for await (const chunk of res.body) { size += chunk.length; need(size <= 131072, "Release metadata exceeds limit"); chunks.push(chunk); }
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

export function renderFormula(record) {
  validateRouterRelease(record);
  const mac = record.targets["aarch64-apple-darwin"];
  const linuxX64 = record.targets["x86_64-unknown-linux-gnu"];
  const linuxArm = record.targets["aarch64-unknown-linux-musl"];
  return `# frozen_string_literal: true

# Binary distribution of oh-router from immutable ohrouter.com release archives.
# Regenerate checksums/versions with: node tools/oh-router-formula.mjs --refresh
class OhRouter < Formula
  desc "Session router, terminal safety guard and board worker for coding agents"
  homepage "https://ohrouter.com"
  license any_of: ["MIT", "Apache-2.0"]

  on_macos do
    on_arm do
      url "${mac.url}"
      sha256 "${mac.sha256}"
    end
  end

  on_linux do
    on_intel do
      url "${linuxX64.url}"
      sha256 "${linuxX64.sha256}"
    end
    on_arm do
      url "${linuxArm.url}"
      sha256 "${linuxArm.sha256}"
    end
  end

  def install
    %w[oh-router ohd oh-holder].each do |tool|
      found = Dir.glob("**/\#{tool}").find { |path| File.file?(path) }
      odie "release archive did not contain \#{tool}" if found.nil?
      bin.install found => tool
    end
  end

  test do
    assert_match "oh-router #{version}", shell_output("\#{bin}/oh-router --version")
  end
end
`;
}

export async function main(args = process.argv.slice(2)) {
  const mode = args[0] ?? "--check";
  const recordPath = resolve("catalog/oh-router.json");
  if (mode === "--refresh" || mode === "--from") {
    let raw;
    if (mode === "--from") {
      need(args.length === 2, "Use --from <release.json>");
      raw = JSON.parse(await readFile(args[1], "utf8"));
    } else {
      need(args.length === 1, "Use --refresh");
      raw = await readRelease();
    }
    const existing = await readFile(recordPath, "utf8").then(JSON.parse).catch((error) => { if (error.code === "ENOENT") return null; throw error; });
    const next = admitRouterUpdate(existing, raw);
    await mkdir(dirname(recordPath), { recursive: true });
    await mkdir("Formula", { recursive: true });
    await writeFile(recordPath, json(next));
    await writeFile("Formula/oh-router.rb", renderFormula(next));
  } else {
    need(mode === "--check" && args.length <= 1, "Use --check, --refresh or --from <release.json>");
    const existing = validateRouterRelease(JSON.parse(await readFile(recordPath, "utf8")));
    need(await readFile("Formula/oh-router.rb", "utf8") === renderFormula(existing), "Formula/oh-router.rb differs from catalog/oh-router.json");
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) await main();
