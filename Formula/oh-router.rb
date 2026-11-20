# frozen_string_literal: true

# Binary distribution of oh-router from immutable ohrouter.com release archives.
# Regenerate checksums/versions with: node tools/oh-router-formula.mjs --refresh
class OhRouter < Formula
  desc "Session router, terminal safety guard and board worker for coding agents"
  homepage "https://ohrouter.com"
  url "https://ohrouter.com/downloads/0b9709f70c47e8785c893cdf47559d78440b7a3c7f8df0da5c8cb7bda0afc507/oh-router-v0.1.1-aarch64-apple-darwin.tar.gz"
  sha256 "0b9709f70c47e8785c893cdf47559d78440b7a3c7f8df0da5c8cb7bda0afc507"
  license any_of: ["MIT", "Apache-2.0"]

  on_macos do
    depends_on arch: :arm64
  end

  on_linux do
    on_intel do
      url "https://ohrouter.com/downloads/c0962ffb19b31eda5bf45760f18aa159503d58bf8f60d2006ba58cc9db941e81/oh-router-v0.1.1-x86_64-unknown-linux-gnu.tar.gz"
      sha256 "c0962ffb19b31eda5bf45760f18aa159503d58bf8f60d2006ba58cc9db941e81"
    end
    on_arm do
      url "https://ohrouter.com/downloads/a0b6b3dd4d0b160c87c0fd4af5e8bec5a2ed1595b8aedaaee3621823f4a40da7/oh-router-v0.1.1-aarch64-unknown-linux-musl.tar.gz"
      sha256 "a0b6b3dd4d0b160c87c0fd4af5e8bec5a2ed1595b8aedaaee3621823f4a40da7"
    end
  end

  def install
    %w[oh-router ohd oh-holder].each do |tool|
      found = Dir.glob("**/#{tool}").find { |path| File.file?(path) }
      odie "release archive did not contain #{tool}" if found.nil?
      bin.install found => tool
    end
  end

  test do
    assert_match "oh-router #{version}", shell_output("#{bin}/oh-router --version")
  end
end
