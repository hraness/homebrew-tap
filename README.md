# Hraness Homebrew tap

This tap installs five Mac apps ([OH](#oh), [Yaptake](#yaptake),
[Sponge for Mac](#sponge-for-mac), [Textmock for Mac](#textmock-for-mac) and
[DAWN](#dawn)) and the standalone [OH Router](#oh-router) command-line tool.
You need [Homebrew](https://brew.sh).

If an app is already in your Applications folder from its website,
`brew install --cask` stops rather than replace it. Add `--adopt` to keep that
copy and let Homebrew manage it, for example
`brew install --cask --adopt hraness/tap/oh`.

## OH

Install [OH](https://oh.computer), a Mac app for supervising Claude Code and
Codex sessions across providers, models and machines, sharing one Vercel Board,
and pairing remote machines over Cloudflare Tunnel. The app includes the
`oh-router` command.

OH requires an Apple Silicon Mac with macOS 15 or later and
[Homebrew](https://brew.sh).

```sh
brew install --cask hraness/tap/oh
oh-router --version
open -a Oh
```

The cask links the `oh-router` command inside the app, so you can skip
**Help → Use with Coding Agents… → Install `oh-router` Command**. Follow
[Use with coding agents](https://oh.computer/docs/agents) to supervise sessions
and connect a coding agent, or [Multi-machine Cloudflare Tunnels](https://oh.computer/docs/devices)
to pair a remote workstation. The [CLI reference](https://oh.computer/docs/cli)
covers every subcommand.

OH can update itself. To request an update through Homebrew:

```sh
brew update
brew upgrade --cask --greedy hraness/tap/oh
```

To remove the app and its command:

```sh
brew uninstall --cask hraness/tap/oh
```

Uninstalling leaves your session state, profiles and settings in place. The
cask has no `zap` step.

## OH Router

Install [OH Router](https://ohrouter.com) (`oh-router`, `ohd` and `oh-holder`)
without the desktop app on macOS (Apple Silicon) or Linux (`x86_64` and `arm64`):

```sh
brew install hraness/tap/oh-router
oh-router --version
```

Follow the [quickstart](https://ohrouter.com/docs/quickstart) to start `ohd`,
spawn or steer sessions through the 2D VT limit-dialog safety guard, and run a
`@vercel/board` worker. On a Mac where `hraness/tap/oh` is already installed,
`oh-router` is already linked by the cask.

## Yaptake

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
brew install --cask hraness/tap/sponge-app
open -a Sponge
```

The app updates itself. If you installed the earlier `hraness/tap/sponge` cask,
run `brew update` and `brew migrate --cask hraness/tap/sponge-app` to move its
Homebrew record to the new name. `brew uninstall --cask hraness/tap/sponge-app`
removes the app and leaves your library and settings in place.

The standalone Sponge CLI has a separate [release archive policy](docs/sponge-cli-distribution.md).

## Textmock for Mac

[Textmock](https://textmock.com/mac) makes iMessage-style conversations. Write
both sides, or let a fictional character reply with AI that runs on your Mac,
then save an image or video. It needs macOS 14 or later. AI replies need Apple
Intelligence on macOS 26, or the Gemma 4 model on Apple silicon with at least
8 GB of memory; without either, you can still write both sides.

```sh
brew install --cask hraness/tap/textmock
textmock --help
open -a Textmock
```

The cask links the `textmock` command, so you don't need **Install Command-Line
Tool…**. The command runs one method of Textmock's agent API in the open app.
Follow [Use a coding agent](https://textmock.com/docs/agents) to create, edit and
export a conversation from Terminal or a coding agent.

The app updates itself, and the command updates with it.
`brew uninstall --cask hraness/tap/textmock` removes the app and the command and
leaves your conversations and settings in place.

## DAWN

[DAWN](https://dawnav.com/desktop) makes music from a prompt or a score. In the
app, a sentence starts a loop that keeps playing while you edit it. The `dawn`
command checks and renders songs written as TypeScript scores. DAWN needs an
Apple Silicon Mac with macOS 13 or later. Composing, checking and rendering work
offline and need no account.

```sh
brew install --cask hraness/tap/dawn
dawn --version
open -a DAWN
```

The cask links the `dawn` command inside the app, so you can skip **Install dawn
command**. Follow [Make your first song](https://dawnav.com/docs/first-song) to
write an eight-bar song and render it to WAV and MIDI. The
[CLI reference](https://dawnav.com/docs/cli) describes the other commands.

The app updates itself, and the command updates with it.
`brew uninstall --cask hraness/tap/dawn` removes the app and the command and
leaves your projects and settings in place.

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
