# Sponge CLI distribution

Starting at 0.99.0, the tap reserves tags of the form
`sponge-cli-vMAJOR.MINOR.PATCH` for the exact `hraness-sponge-MAJOR.MINOR.PATCH.tgz`
package built for the public npm registry. A release can appear here before npm
lists that version. The Sponge Mac app continues to use its own cask and
update feed.

The distributor checks the annotated stable tag against the protected source
history. Main CI, the release build, package verification, installation on
macOS and Linux, and immutable artifact publication must all pass for that
commit. It checks the package name and version, inspects the tarball's file
list and packaged native helpers, and compares its SHA-256 with the canonical
immutable release.

Each public release contains two assets. The tarball is the original file.
`SHA256SUMS` contains its lowercase SHA-256, two spaces, the filename and a
newline. A retry checks existing assets before publishing. Once published,
the release is immutable. Readers can verify a download on macOS by saving
both assets in an empty directory and running `shasum -a 256 -c SHA256SUMS`
there. A valid file prints its name followed by `: OK`.
