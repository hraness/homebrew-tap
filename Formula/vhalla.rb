# frozen_string_literal: true

# Binary distribution of the vhalla CLI from immutable GitHub release
# archives. Regenerate checksums/versions with: node tools/brew-formula.mjs
class Vhalla < Formula
  desc "Peer-to-peer rooms for AI agents and the people who own them"
  homepage "https://vhalla.com"
  version "0.2.3"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/hraness/valhalla/releases/download/v0.2.3/valhalla-v0.2.3-aarch64-apple-darwin.tar.gz"
      sha256 "b84c14ca2c522bd149a4de10ff9b5fe7f95cb852dc50a73d46bde0d1c22e5c44"
    end
  end

  on_linux do
    on_intel do
      url "https://github.com/hraness/valhalla/releases/download/v0.2.3/valhalla-v0.2.3-x86_64-unknown-linux-gnu.tar.gz"
      sha256 "6860d8b3f9f14f54c9a918a14d369cd18d176a1f8ff3bd906892c64bd4ae127c"
    end
  end

  def install
    binary = Dir.glob("**/vhalla").find { |path| File.file?(path) }
    odie "release archive did not contain a vhalla binary" if binary.nil?
    bin.install binary => "vhalla"
  end

  test do
    assert_match "vhalla identity", shell_output("#{bin}/vhalla --help")
  end
end
