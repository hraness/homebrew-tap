# frozen_string_literal: true

# Binary distribution of oh-router from immutable ohrouter.com release archives.
# Regenerate checksums/versions with: node tools/oh-router-formula.mjs --refresh
class OhRouter < Formula
  desc "Session router, terminal safety guard and board worker for coding agents"
  homepage "https://ohrouter.com"
  url "https://ohrouter.com/downloads/b1d9098601175f4bfb230f5181b5f2a33cefc401e4beecc481ba68f9fe28e608/oh-router-v0.1.3-aarch64-apple-darwin.tar.gz"
  sha256 "b1d9098601175f4bfb230f5181b5f2a33cefc401e4beecc481ba68f9fe28e608"
  license any_of: ["MIT", "Apache-2.0"]

  on_macos do
    on_intel do
      url "https://ohrouter.com/downloads/32d44dc5fc9dd3c528f3fcfee81444978864081fafbcf7a0c27e734b5ea91c08/oh-router-v0.1.3-x86_64-apple-darwin.tar.gz"
      sha256 "32d44dc5fc9dd3c528f3fcfee81444978864081fafbcf7a0c27e734b5ea91c08"
    end
  end

  on_linux do
    on_intel do
      url "https://ohrouter.com/downloads/1fa5ba2d5cc6ae2fe6f366bc92ef17e848e3df42f5d0509e9f630f8e3b9dac57/oh-router-v0.1.3-x86_64-unknown-linux-gnu.tar.gz"
      sha256 "1fa5ba2d5cc6ae2fe6f366bc92ef17e848e3df42f5d0509e9f630f8e3b9dac57"
    end
    on_arm do
      url "https://ohrouter.com/downloads/c64e333786f09e830c3e8773923a877e1cf1a642a11c75644841da874918a583/oh-router-v0.1.3-aarch64-unknown-linux-musl.tar.gz"
      sha256 "c64e333786f09e830c3e8773923a877e1cf1a642a11c75644841da874918a583"
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
