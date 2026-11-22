# frozen_string_literal: true

# Binary distribution of oh-router from immutable ohrouter.com release archives.
# Regenerate checksums/versions with: node tools/oh-router-formula.mjs --refresh
class OhRouter < Formula
  desc "Session router, terminal safety guard and board worker for coding agents"
  homepage "https://ohrouter.com"
  url "https://ohrouter.com/downloads/edd5ac052b7c01cf8b76492c535aa97ce9f9e6eae8fdf0533dffac556af2cffe/oh-router-v0.1.4-aarch64-apple-darwin.tar.gz"
  sha256 "edd5ac052b7c01cf8b76492c535aa97ce9f9e6eae8fdf0533dffac556af2cffe"
  license any_of: ["MIT", "Apache-2.0"]

  on_macos do
    on_intel do
      url "https://ohrouter.com/downloads/6cad6d7c9d85cc410e3f02ed1ed1180978e37504b99fb37a7de48a8142339d2d/oh-router-v0.1.4-x86_64-apple-darwin.tar.gz"
      sha256 "6cad6d7c9d85cc410e3f02ed1ed1180978e37504b99fb37a7de48a8142339d2d"
    end
  end

  on_linux do
    on_intel do
      url "https://ohrouter.com/downloads/1593c216ecd96165f94b63be7ee990443d822e3d2067082a4ae01a5429e72ed0/oh-router-v0.1.4-x86_64-unknown-linux-gnu.tar.gz"
      sha256 "1593c216ecd96165f94b63be7ee990443d822e3d2067082a4ae01a5429e72ed0"
    end
    on_arm do
      url "https://ohrouter.com/downloads/3ff9afc3aebed9e889a4e33baaab9ad678a95ddf6f7f9930695e40e941ebc816/oh-router-v0.1.4-aarch64-unknown-linux-musl.tar.gz"
      sha256 "3ff9afc3aebed9e889a4e33baaab9ad678a95ddf6f7f9930695e40e941ebc816"
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
