# frozen_string_literal: true

# Universal macOS binary from presence's GitHub release.
# Regenerate with: node tools/presence-formula.mjs --refresh
class Presence < Formula
  desc "Tell if someone is using this Mac: away, idle, typing, video or call"
  homepage "https://github.com/hraness/presence"
  url "https://github.com/hraness/presence/releases/download/v0.1.0/presence-0.1.0-macos-universal.tar.gz"
  sha256 "4296bf56b5afdcd6c9267f6b871239462e062ea2172d0d40d580a07e93dd6d30"
  license "MIT"

  depends_on macos: :ventura

  def install
    bin.install "presence"
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/presence --version")
    (testpath/"call.json").write('{"camera": true}')
    ENV["PRESENCE_FIXTURE"] = testpath/"call.json"
    assert_match "call", shell_output("#{bin}/presence")
  end
end
