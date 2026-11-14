import { createSign } from "node:crypto";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const need = (value, message) => { if (!value) throw new Error(message); };
export const identities = Object.freeze({
  distribution: { id: 5762098, slug: "hraness-distribution", installation: 182021237 },
  mirror: { id: 5164973, slug: "hraness-release-tagger", installation: 167254589 },
});
const OWNER = { id: 307125679, login: "hraness" };

export function validateApp(app, expected) {
  need(app?.id === expected.id && app.slug === expected.slug && app.owner?.id === OWNER.id && app.owner.login === OWNER.login && app.owner.type === "Organization", "GitHub App authority does not match the approved Hraness identity");
}
export function validateInstallation(installation, expected) {
  need(installation?.id === expected.installation && installation.app_id === expected.id && installation.app_slug === expected.slug && installation.target_id === OWNER.id && installation.target_type === "Organization" && installation.account?.id === OWNER.id && installation.account.login === OWNER.login && installation.suspended_at === null, "GitHub App installation authority differs or is suspended");
}
export function validateScope(access) {
  need(access?.total_count === 1 && Array.isArray(access.repositories) && access.repositories.length === 1, "App token must select exactly one repository");
  const repo = access.repositories[0];
  need(repo.id === 1382935233 && repo.full_name === "hraness/homebrew-tap" && repo.private === false && repo.owner?.id === OWNER.id && repo.owner.login === OWNER.login, "App token must select only the exact public Hraness tap");
}

async function read(path, token) {
  const response = await fetch(`https://api.github.com${path}`, { redirect: "error", signal: AbortSignal.timeout(20000), headers: { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2026-03-10", "User-Agent": "Hraness-distribution-authority/1" } });
  need(response.ok, `GitHub authority read returned HTTP ${response.status}`);
  const chunks = []; let size = 0;
  for await (const chunk of response.body) { size += chunk.length; need(size <= 131072, "GitHub authority metadata exceeds its limit"); chunks.push(chunk); }
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

export async function main(kind = process.argv[2], env = process.env) {
  const expected = identities[kind]; need(expected, "Select the distribution or mirror authority");
  need(env.GITHUB_REPOSITORY_ID === "1382935233" && env.GITHUB_REPOSITORY === "hraness/homebrew-tap" && env.GITHUB_REF === "refs/heads/main", "Publishing requires the exact tap and protected main ref");
  need(env.APP_ID === String(expected.id) && env.APP_SLUG === expected.slug && env.INSTALLATION_ID === String(expected.installation), "Token action resolved an unexpected App or installation");
  need(env.APP_PRIVATE_KEY && env.GH_TOKEN, "The approved App credentials and scoped installation token are required");
  const now = Math.floor(Date.now() / 1000);
  const base = (value) => Buffer.from(JSON.stringify(value)).toString("base64url");
  const unsigned = `${base({ alg: "RS256", typ: "JWT" })}.${base({ iat: now - 30, exp: now + 120, iss: String(expected.id) })}`;
  const signer = createSign("RSA-SHA256"); signer.update(unsigned); signer.end();
  const jwt = `${unsigned}.${signer.sign(env.APP_PRIVATE_KEY).toString("base64url")}`;
  validateApp(await read("/app", jwt), expected);
  validateInstallation(await read(`/app/installations/${expected.installation}`, jwt), expected);
  validateScope(await read("/installation/repositories", env.GH_TOKEN));
  process.stdout.write(`Verified ${expected.slug}, Hraness installation and exact one-tap token; no publication attempted.\n`);
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) await main();
