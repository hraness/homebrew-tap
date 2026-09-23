# frozen_string_literal: true

# Binary distribution of the vhalla CLI from immutable GitHub release
# archives. Regenerate checksums/versions with: node tools/brew-formula.mjs
class Vhalla < Formula
  desc "Peer-to-peer rooms for AI agents and the people who own them"
  homepage "https://vhalla.com"
  version "0.2.2"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/hraness/valhalla/releases/download/v0.2.2/valhalla-v0.2.2-aarch64-apple-darwin.tar.gz"
      sha256 "5b67dd283465e316b0dea8aab9e54ec334190b00cfd655cbdf1163542c158ac1"
    end
  end

  on_linux do
    on_intel do
      url "https://github.com/hraness/valhalla/releases/download/v0.2.2/valhalla-v0.2.2-x86_64-unknown-linux-gnu.tar.gz"
      sha256 "cf22495e7d116aa85946ad0bb0a250b252a32dcd3ac767be999a3db8e3666194"
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
