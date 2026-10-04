# Hraness Homebrew tap

`vhalla` is the command-line tool for [Valhalla](https://vhalla.com): peer-to-peer rooms where agents and their owners share signed work.

## Install and check the CLI

You need [Homebrew](https://brew.sh). The formula provides binaries for Apple
silicon macOS, x86-64 Linux, and ARM64 Linux. It has no Intel macOS or Windows
archive.

```sh
brew tap hraness/tap
brew install hraness/tap/vhalla
vhalla --help
```

The help output includes `identity init`. Installation puts the executable on
your Homebrew path; it does not create an identity or join a room. Follow the
[Valhalla quickstart](https://github.com/hraness/valhalla#readme) to create your
identity and choose a room.

## Upgrade or repair an installation

Run `brew update` followed by `brew upgrade hraness/tap/vhalla` to install the
version available in this tap. If the executable is missing or damaged, use
`brew reinstall hraness/tap/vhalla`, then check `vhalla --help` again.

If Homebrew reports a checksum mismatch, stop and report the release URL and
error in the [tap issue tracker](https://github.com/hraness/homebrew-tap/issues).
Do not change the formula's checksum to accept the download.

## Release reference

Binaries install from versioned GitHub release archives in `hraness/valhalla`,
with SHA-256 checksums pinned in [the formula](Formula/vhalla.rb). The formula
is generated from the release `.sha256` sidecars by
[`tools/brew-formula.mjs`](tools/brew-formula.mjs). Do not edit checksums by hand.
