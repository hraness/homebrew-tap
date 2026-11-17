# Hraness Homebrew tap

This tap installs two Mac apps: Yaptake and [Sponge for Mac](#sponge-for-mac).

Install [Yaptake](https://yaptake.com), a Mac video editor with transcript cuts,
editable captions and a timeline. The app includes the `yaptake` command for
working with a local project from a coding agent.

Yaptake requires an Apple Silicon Mac with macOS 26 or later and
[Homebrew](https://brew.sh).

```sh
brew install --cask hraness/tap/yaptake
yaptake --help
open -a Yaptake
```

Follow [Make a first cut](https://yaptake.com/docs/first-cut) to import a recording,
cut it by its words and export a video. To connect a coding agent, follow
[Use a coding agent](https://yaptake.com/docs/agents). The
[CLI reference](https://yaptake.com/docs/cli) covers commands and their effects.

Yaptake can update itself. To request an update through Homebrew:

```sh
brew update
brew upgrade --cask --greedy hraness/tap/yaptake
```

To remove the app and its command:

```sh
brew uninstall --cask hraness/tap/yaptake
```

Uninstalling leaves your projects, preferences and other app data in place.
The cask has no `zap` step.

The cask follows Yaptake's active signed release and checks the archive's
SHA-256. Its version includes both the app version and build number. The
[maintenance guide](docs/yaptake-distribution.md) explains automatic updates and
the mirror workflow for preserving existing download addresses.

## Sponge for Mac

[Sponge](https://sponge.computer) is a reading library. The Mac app reads your
library in a window and saves links from the Share menu, the menu bar or a
keyboard shortcut. It needs macOS 15 or later and a Sponge account; capture
runs on a computer with the [Sponge CLI](https://sponge.computer/download).

```sh
brew install --cask hraness/tap/sponge
open -a Sponge
```

The app updates itself. `brew uninstall --cask hraness/tap/sponge` removes the
app and leaves your library and settings in place. This cask is named for the
app; the `sponge` formula in Homebrew core is a different tool (moreutils).

## Retired Valhalla formula

The `vhalla` formula is retired and disabled, effective 2026-11-03. Homebrew
refuses new installations of `hraness/tap/vhalla`.

`vhalla` was the command-line tool for
[Valhalla](https://github.com/hraness/valhalla): peer-to-peer rooms where agents
and their owners shared signed work. The formula and its versioned GitHub
release URLs and SHA-256 checksums remain available as a historical record.
Disabling the formula does not remove existing installations or their data.

[`tools/brew-formula.mjs`](tools/brew-formula.mjs) generates the formula from the
release checksum files and retains its disabled status. Do not re-enable the
formula while regenerating it.
