# Maintain Yaptake distribution

Yaptake's website selects the app release. This tap distributes that selection
through Homebrew and preserves exact copies of archives that Yaptake has already
published. Publishing an archive here does not select a new version for the app
or its updater.

## Automatic cask updates

`tools/yaptake-cask.mjs` reads `https://yaptake.com/release.json` and
`https://yaptake.com/appcast.xml`. They must agree on the archive URL, checksum,
length, signature, platform, app version and build. The generator refuses version
or build rollback and refuses a changed archive for an existing version/build.
It reads the release and feed again to detect a concurrent update.

Homebrew livecheck reads both version fields from that appcast with its
[XML strategy](https://docs.brew.sh/Brew-Livecheck#xml-strategy-block). Builds
can share the same app version while their download hash paths differ, so the
cask retains the build number when checking for updates.

The daily **Update Yaptake** workflow updates `catalog/yaptake.json` and generates
`Casks/yaptake.rb`. It opens a pull request and requests protected auto-merge for
that exact head. Required checks validate the generators, download and verify
the archive and its Sparkle signature, then exercise normal Homebrew installation,
the signed command and uninstall on a disposable macOS 26 Apple Silicon runner.
Synthetic projects and preferences must remain after uninstall. A change runs
the strict online Homebrew audit only for the casks it updates, so a new release
of another app in this tap cannot block a Yaptake update.

Configure the organization-owned distribution GitHub App once, selecting only
this repository for its installation token. The workflow uses
`DISTRIBUTION_APP_ID` and `DISTRIBUTION_APP_PRIVATE_KEY`, with Contents:write and
Pull requests:write. It has no personal-token or `GITHUB_TOKEN` fallback.

Both writing workflows run only on this exact repository's protected `main`
ref. Before a write, `tools/check-app-authority.mjs` uses a two-minute in-memory
App JWT to read the App and installation authority, verifies the approved
Hraness owner, App ID, slug and installation, then reads the minted token's
repository scope and requires this one public tap. It stores no token. The
App-token action revokes its installation token at job cleanup. Pinned Actions
have a weekly Dependabot update path.

A manual refresh uses Node 24 and the same generator. The focused cask tests
also use Ruby with REXML:

```sh
node tools/yaptake-cask.mjs --refresh
node --test test/*.test.mjs
node tools/yaptake-cask.mjs --check
```

Review and deliver the generated changes through the normal pull request path.
Never edit a cask checksum by hand.

## Immutable archive mirrors

The **Mirror Yaptake archives** workflow runs every two hours and accepts the
`yaptake-release-active` repository event. It copies the active public archive
and its checksum and package manifest. The first migration also uses the
reviewed `catalog/yaptake-history.json` seed, which accounts for every historical
public download path. The seed contains public content hashes and lengths;
it contains no provider file or deployment identifiers.

To preserve a signed candidate before activation, copy its full lowercase archive
SHA-256 from `https://yaptake.com/downloads.json`. With workflow dispatch access
to the tap, run:

```sh
gh workflow run mirror-yaptake.yml --repo hraness/homebrew-tap --ref main -f staged-sha256="$sha256"
```

The same selection is available locally as
`python3 tools/yaptake-mirrors.py --staged-sha256 "$sha256"` with the scoped
App token described below. This selection admits exactly the matching public ZIP,
checksum and package manifest. The publisher checks their hashes and lengths
against the public inventory and verifies the signing and notarization receipt.
An identical catalog entry completes immediately, including after the
website redirects these addresses to the immutable release. The active
website download, updater and cask continue to follow the active signed feed.

A release tag includes the full app version, build number and archive SHA-256:
`yaptake-VERSION-BUILD-SHA256`. It has exactly three assets. Existing Yapwing
filenames remain unchanged. The `private` suffix on archives finalized before
2026-11-16 describes their Developer ID signing channel; these files were
already public downloads and keep their names. Later archives are named
`Yaptake-VERSION.zip` (with matching `.sha256` and `.manifest.json`), and the
cask generator accepts both forms.

The publisher streams one file at a time in 64 KiB chunks. It checks the source
Content-Length, SHA-256 and, when supplied by the history seed, SHA-1 content
hash. It stages no ZIP on disk. It uploads only to an owned draft, checks the
remote asset digest and size, publishes, then requires `immutable: true` and a
second exact asset readback before recording the release. It never uses a
`latest` URL, replaces a published asset or chooses the app's active release.

The existing release-tagger App supplies a token scoped to this one public tap
with Contents:read for workflow preflight and Contents:write for publishing. Configure `RELEASE_TAGGER_APP_ID` and
`RELEASE_TAGGER_PRIVATE_KEY` for the workflow. A preflight verifies that the
installation token selects this exact public repository, without publishing:

```sh
python3 tools/yaptake-mirrors.py --preflight
```

Supply the short-lived App token in `YAPTAKE_RELEASE_TOKEN`; do not print it or
put it in a command argument. The repository owner enables and verifies GitHub
immutable releases once before running the migration. Checking that setting
requires administrator access; the publisher does not request that scope.
Every actual release must independently return `immutable: true` before use.

The first migration is the **Mirror Yaptake archives** workflow with
`include-history` selected. It is safe to repeat. The publisher resumes verified draft assets, rehashes a source after a lost
acknowledgement and retries only an exact empty starter asset in its owned draft.
A conflicting source hash stops publication; an interruption never changes the
active website download. Inspect conflicting evidence before retrying. Do not
delete or replace any published asset.

Verified records are conditionally appended to `yaptake-downloads.json` on the
`yaptake-downloads` data branch. Each file records its original path, hashes,
length, exact asset URL and GitHub asset ID. Concurrent writers reread and merge
on conflict; an identical record is a stable no-op. The publisher never forces
a branch, removes a record or writes to protected `main`.

After the first migration, Yaptake's site build reads this bounded catalog and
verifies the published immutable release and asset identities. It keeps every existing
`/downloads/SHA256/FILENAME` address as a permanent redirect to its exact asset
in this tap. The archive bytes, native signatures and updater signatures stay
the same. The site independently checks that its active release and full live
download history did not change before production promotion. GitHub and its
asset CDN serve the download; the website's privacy notice names that host.

GitHub documents [immutable release behavior](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)
and its [release asset limits](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases#storage-and-bandwidth-quotas).
These mirrors contain compiled app distributions under
[Yaptake's terms](https://yaptake.com/terms); they do not publish the app's source.
