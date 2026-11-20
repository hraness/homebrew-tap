# Maintain OH distribution

OH's website selects the app release and ohrouter.com selects the command-line
release. This tap distributes those selections through Homebrew. Publishing
here does not select a new version for the app or its updater.

## The OH cask

`tools/oh-cask.mjs` reads `https://oh.computer/release.json` and
`https://oh.computer/appcast.xml`. They must agree on the archive URL, checksum,
length, Sparkle signature, platform, app version and build. The release must
also record Apple's `Accepted` notarization, a validated staple and a
Gatekeeper pass. The generator refuses version or build rollback and refuses a
changed archive for an existing version and build. It reads the release and
feed again to detect a concurrent update.

`--archive PATH` checks a downloaded archive against the admitted record: its
size, SHA-256 and Sparkle signature under the app's update key.

The cask installs `Oh.app` and links the `oh-router` command from
`Oh.app/Contents/Helpers/`. Livecheck reads both version fields from the
appcast, so builds that share an app version still update.

## The oh-router formula

`tools/oh-router-formula.mjs` reads `https://ohrouter.com/release.json` and
generates `Formula/oh-router.rb` for macOS on Apple Silicon and for Linux on
`x86_64` and `arm64`. Each archive URL must be the content-addressed
`https://ohrouter.com/downloads/<sha256>/oh-router-v<version>-<target>.tar.gz`
path for its own checksum. The generator refuses version rollback and refuses
changed archives for an admitted version.

## Automatic updates

The daily **Update OH** workflow runs both generators and opens one pull
request for any change, then requests protected auto-merge for that exact head.
Required checks validate the generators, run the strict Homebrew audits,
install, test and uninstall the formula on macOS and Linux, and install, adopt
and uninstall the cask on a disposable Apple Silicon runner. A synthetic
preference must remain after uninstall. The workflow uses the same
distribution GitHub App and authority check as **Update Yaptake**; see
[Maintain Yaptake distribution](yaptake-distribution.md#automatic-cask-updates).

A manual refresh uses Node 24:

```sh
node tools/oh-cask.mjs --refresh
node tools/oh-router-formula.mjs --refresh
node --test test/*.test.mjs
node tools/oh-cask.mjs --check
node tools/oh-router-formula.mjs --check
```

Deliver the generated changes through the normal pull request path. Never edit
a checksum by hand.

A Mac with the OH cask installed already has `oh-router` linked from the app.
Install the formula only where the app is not installed, such as Linux hosts
and Macs that run `ohd` without the app.
