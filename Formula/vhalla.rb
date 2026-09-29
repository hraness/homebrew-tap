# frozen_string_literal: true

# Binary distribution of the vhalla CLI from immutable GitHub release
# archives. Regenerate checksums/versions with: node tools/brew-formula.mjs
class Vhalla < Formula
  desc "Peer-to-peer rooms for AI agents and the people who own them"
  homepage "https://vhalla.com"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/hraness/valhalla/releases/download/v0.2.8/valhalla-v0.2.8-aarch64-apple-darwin.tar.gz"
      sha256 "ffb083ac7643a3db616ab0388607a8240dee837c72fb89815ea3f16a08a82e98"
    end
  end

  on_linux do
    on_intel do
      url "https://github.com/hraness/valhalla/releases/download/v0.2.8/valhalla-v0.2.8-x86_64-unknown-linux-gnu.tar.gz"
      sha256 "f36f33628827db3e70b6816eb96242957bff779ded5a51bf0a3beb42476ba99a"
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
