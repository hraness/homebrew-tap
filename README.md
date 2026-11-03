# Hraness Homebrew tap

The `vhalla` formula is retired and disabled, effective 2026-11-03. Homebrew
refuses new installations of `hraness/tap/vhalla`. This tap remains active.

`vhalla` was the command-line tool for
[Valhalla](https://github.com/hraness/valhalla): peer-to-peer rooms where agents
and their owners shared signed work. The formula and its release references
remain available as a historical record. Disabling the formula does not remove
existing installations or their data.

## Release reference

The formula preserves versioned GitHub release URLs and SHA-256 checksums for
Apple silicon macOS, x86-64 Linux and ARM64 Linux. It has no Intel macOS or
Windows archive. See [the formula](Formula/vhalla.rb) for the pinned release.

[`tools/brew-formula.mjs`](tools/brew-formula.mjs) generates the formula from the
release `.sha256` sidecars and retains its disabled status. Do not edit checksums
by hand or re-enable the formula while regenerating it.
