# frozen_string_literal: true

# Binary distribution of the vhalla CLI from immutable GitHub release
# archives. Regenerate checksums/versions with: node tools/brew-formula.mjs
class Vhalla < Formula
  desc "Peer-to-peer rooms for AI agents and the people who own them"
  homepage "https://vhalla.com"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/hraness/valhalla/releases/download/v0.2.10/valhalla-v0.2.10-aarch64-apple-darwin.tar.gz"
      sha256 "8bd7bcf895fe87b74fd711634e6ee8172881b0366ab31cddc3d9f0fa65affd06"
    end
  end

  on_linux do
    on_intel do
      url "https://github.com/hraness/valhalla/releases/download/v0.2.10/valhalla-v0.2.10-x86_64-unknown-linux-gnu.tar.gz"
      sha256 "74bdc766f6b3f229d01c61bbd918370355cd928ae54fcf239f900660839701f9"
    end
    on_arm do
      url "https://github.com/hraness/valhalla/releases/download/v0.2.10/valhalla-v0.2.10-aarch64-unknown-linux-musl.tar.gz"
      sha256 "452b337274002da987d501ffd30eb07ec616c25783f2c11a9c3400910bb661c4"
    end
  end

  def install
    binary = Dir.glob("**/vhalla").find { |path| File.file?(path) }
    odie "release archive did not contain a vhalla binary" if binary.nil?
    bin.install binary => "vhalla"
  end

  test do
    assert_match "identity init", shell_output("#{bin}/vhalla --help")
  end
end
