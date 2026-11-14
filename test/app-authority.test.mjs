import { test } from "node:test";
import assert from "node:assert/strict";
import { identities, validateApp, validateInstallation, validateScope, main } from "../tools/check-app-authority.mjs";
const owner = { id: 307125679, login: "hraness", type: "Organization" };

test("both writers bind the approved App owner, exact App ID, slug and installation", () => {
  for (const expected of Object.values(identities)) {
    const app = { id: expected.id, slug: expected.slug, owner };
    const installation = { id: expected.installation, app_id: expected.id, app_slug: expected.slug, target_id: owner.id, target_type: owner.type, account: owner, suspended_at: null };
    validateApp(app, expected); validateInstallation(installation, expected);
    assert.throws(() => validateApp({ ...app, owner: { ...owner, id: 1 } }, expected), /authority/);
    assert.throws(() => validateApp({ ...app, id: 1 }, expected), /authority/);
    assert.throws(() => validateApp({ ...app, slug: "other" }, expected), /authority/);
    assert.throws(() => validateInstallation({ ...installation, id: 1 }, expected), /authority/);
    assert.throws(() => validateInstallation({ ...installation, suspended_at: "2026-01-01" }, expected), /authority/);
  }
});
test("installation token readback must select exactly the public owner tap", () => {
  const repo = { id: 1382935233, full_name: "hraness/homebrew-tap", private: false, owner };
  validateScope({ total_count: 1, repositories: [repo] });
  for (const access of [{ total_count: 2, repositories: [repo, repo] }, { total_count: 1, repositories: [{ ...repo, id: 1 }] }, { total_count: 1, repositories: [{ ...repo, private: true }] }, { total_count: 1, repositories: [{ ...repo, owner: { ...owner, id: 1 } }] }]) assert.throws(() => validateScope(access));
});
test("a branch, fork or mismatched configured App is refused before authority reads", async () => {
  const env = { GITHUB_REPOSITORY_ID: "1382935233", GITHUB_REPOSITORY: "hraness/homebrew-tap", GITHUB_REF: "refs/heads/main", APP_ID: "5762098", APP_SLUG: "hraness-distribution", INSTALLATION_ID: "182021237" };
  for (const changed of [{ GITHUB_REF: "refs/heads/other" }, { GITHUB_REPOSITORY_ID: "1" }, { GITHUB_REPOSITORY: "other/homebrew-tap" }, { APP_ID: "1" }, { APP_SLUG: "other" }, { INSTALLATION_ID: "1" }]) await assert.rejects(main("distribution", { ...env, ...changed }));
});
