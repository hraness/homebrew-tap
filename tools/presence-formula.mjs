#!/usr/bin/env node
// Keep Formula/presence.rb on the latest hraness/presence GitHub release.
//   --check                 the formula is exactly what the generator renders
//   --refresh [--archive-out <path>]
//                           admit the latest release: exact tag and asset name,
//                           GitHub's asset digest matches the downloaded bytes
//                           and the .sha256 sidecar; no rollback, and an
//                           admitted version never changes its archive
// The workflow verifies the downloaded archive's build provenance separately.
import { createHash } from "node:crypto";
import { appendFile, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

export const FORMULA = "Formula/presence.rb";
const REPO = "hraness/presence";
const VERSION = /^(0|[1-9]\d{0,8})\.(0|[1-9]\d{0,8})\.(0|[1-9]\d{0,8})$/;
const SHA = /^[a-f0-9]{64}$/;
const MAX_ARCHIVE = 64 * 1024 * 1024;

const need = (value, message) => { if (!value) throw new Error(message); };
export const assetName = (version) => `presence-${version}-macos-universal.tar.gz`;
export const assetUrl = (version) => `https://github.com/${REPO}/releases/download/v${version}/${assetName(version)}`;

export function renderFormula({ version, sha256 }) {
  need(VERSION.test(version) && SHA.test(sha256), "Invalid presence version or sha256");
  return `# frozen_string_literal: true

# Universal macOS binary from presence's GitHub release.
# Regenerate with: node tools/presence-formula.mjs --refresh
class Presence < Formula
  desc "Tell if someone is using this Mac: away, idle, typing, video or call"
  homepage "https://github.com/${REPO}"
  url "${assetUrl(version)}"
  sha256 "${sha256}"
  license "MIT"

  depends_on macos: :ventura

  def install
    bin.install "presence"
  end

  test do
    assert_match version.to_s, shell_output("\#{bin}/presence --version")
    (testpath/"call.json").write('{"camera": true}')
    ENV["PRESENCE_FIXTURE"] = testpath/"call.json"
    assert_match "call", shell_output("\#{bin}/presence")
  end
end
`;
}

export function parseFormula(text) {
  const url = text.match(/^ {2}url "([^"]+)"$/m)?.[1];
  const sha256 = text.match(/^ {2}sha256 "([a-f0-9]{64})"$/m)?.[1];
  const version = url?.match(/\/download\/v([^/]+)\//)?.[1];
  need(version && VERSION.test(version) && url === assetUrl(version) && sha256, "Formula/presence.rb has no recognizable presence release");
  const record = { version, sha256 };
  need(text === renderFormula(record), "Formula/presence.rb differs from the generator output");
  return record;
}

// Pick the archive from a GitHub release object and return what the formula needs.
export function releaseRecord(release) {
  need(release && release.draft === false && release.prerelease === false, "The latest presence release must be published and not a prerelease");
  const version = typeof release.tag_name === "string" && release.tag_name.startsWith("v") ? release.tag_name.slice(1) : "";
  need(VERSION.test(version), `Unexpected presence tag ${release.tag_name}`);
  const named = (name) => (release.assets ?? []).filter((asset) => asset.name === name);
  const archive = named(assetName(version));
  need(archive.length === 1, `Release v${version} must carry exactly one ${assetName(version)}`);
  need(archive[0].browser_download_url === assetUrl(version), `Unexpected archive URL ${archive[0].browser_download_url}`);
  const digest = /^sha256:([a-f0-9]{64})$/.exec(archive[0].digest ?? "")?.[1];
  need(digest, `Release v${version} has no sha256 digest for its archive`);
  const sidecar = named(`${assetName(version)}.sha256`);
  need(sidecar.length === 1, `Release v${version} must carry ${assetName(version)}.sha256`);
  return { version, sha256: digest, sidecarUrl: sidecar[0].browser_download_url };
}

// The sidecar is `shasum -a 256` output: "<digest>  <name>".
export function sidecarDigest(text, version) {
  const [sum, name, ...rest] = text.trim().split(/\s+/);
  need(rest.length === 0 && name === assetName(version) && SHA.test(sum ?? ""), "Malformed presence .sha256 sidecar");
  return sum;
}

export function admit(current, next) {
  if (!current) return next;
  const a = current.version.split(".").map(Number);
  const b = next.version.split(".").map(Number);
  const first = a.findIndex((part, index) => part !== b[index]);
  need(first < 0 || b[first] > a[first], `Version rollback refused: ${current.version} -> ${next.version}`);
  if (first < 0) need(current.sha256 === next.sha256, `presence ${next.version} changed its archive; refusing the new digest`);
  return { version: next.version, sha256: next.sha256 };
}

async function fetchBytes(url, limit, headers = {}) {
  const res = await fetch(url, { signal: AbortSignal.timeout(60000), headers: { "User-Agent": "hraness-homebrew-tap", ...headers } });
  need(res.ok, `HTTP ${res.status} fetching ${url}`);
  const chunks = []; let size = 0;
  for await (const chunk of res.body) { size += chunk.length; need(size <= limit, `${url} exceeds ${limit} bytes`); chunks.push(chunk); }
  return Buffer.concat(chunks);
}

async function latestRelease(env) {
  const headers = { Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28" };
  if (env.GH_TOKEN) headers.Authorization = `Bearer ${env.GH_TOKEN}`;
  return JSON.parse((await fetchBytes(`https://api.github.com/repos/${REPO}/releases/latest`, 1 << 20, headers)).toString("utf8"));
}

export async function main(args = process.argv.slice(2), env = process.env) {
  const mode = args[0] ?? "--check";
  const current = parseFormula(await readFile(FORMULA, "utf8"));
  if (mode === "--check") {
    need(args.length <= 1, "Use --check");
    process.stdout.write(`${FORMULA} renders presence ${current.version}\n`);
    return;
  }
  need(mode === "--refresh", "Use --check or --refresh [--archive-out <path>]");
  const out = args[1] === "--archive-out" ? args[2] : undefined;
  need(args.length === 1 || (args.length === 3 && out), "Use --refresh [--archive-out <path>]");

  const found = releaseRecord(await latestRelease(env));
  const archive = await fetchBytes(assetUrl(found.version), MAX_ARCHIVE);
  const actual = createHash("sha256").update(archive).digest("hex");
  need(actual === found.sha256, `Downloaded archive ${actual} differs from GitHub's digest ${found.sha256}`);
  need(sidecarDigest((await fetchBytes(found.sidecarUrl, 4096)).toString("utf8"), found.version) === actual, "The .sha256 sidecar differs from the archive");
  const next = admit(current, found);
  if (out) await writeFile(out, archive);

  const changed = next.version !== current.version;
  if (changed) await writeFile(FORMULA, renderFormula(next));
  process.stdout.write(changed
    ? `Updated presence ${current.version} -> ${next.version} (${next.sha256})\n`
    : `presence ${current.version} is current (${current.sha256}); no change\n`);
  if (env.GITHUB_OUTPUT) await appendFile(env.GITHUB_OUTPUT, `version=${next.version}\nchanged=${changed}\n`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) await main();
