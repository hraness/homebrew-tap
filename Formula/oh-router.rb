# frozen_string_literal: true

# Binary distribution of oh-router from immutable ohputer.com/router release archives.
# Regenerate checksums/versions with: node tools/oh-router-formula.mjs --refresh
class OhRouter < Formula
  desc "Session router, terminal safety guard and board worker for coding agents"
  homepage "https://ohputer.com/router"
  url "https://ohputer.com/router/downloads/6cdd46f26580b50eecaa23c25c1646645534bc1423a90e277abdb538c7344d4e/oh-router-v0.1.13-aarch64-apple-darwin.tar.gz"
  sha256 "6cdd46f26580b50eecaa23c25c1646645534bc1423a90e277abdb538c7344d4e"
  license any_of: ["MIT", "Apache-2.0"]

  on_macos do
    on_intel do
      url "https://ohputer.com/router/downloads/75425636e750f481f774fb58cef01f0d9b3018ce7a4b96466ac5ee410fa437c8/oh-router-v0.1.13-x86_64-apple-darwin.tar.gz"
      sha256 "75425636e750f481f774fb58cef01f0d9b3018ce7a4b96466ac5ee410fa437c8"
    end
  end

  on_linux do
    on_intel do
      url "https://ohputer.com/router/downloads/29aa5167148ab754cedfdcbc833b42398fa29764a3680aa3ec8a1cac965628eb/oh-router-v0.1.13-x86_64-unknown-linux-gnu.tar.gz"
      sha256 "29aa5167148ab754cedfdcbc833b42398fa29764a3680aa3ec8a1cac965628eb"
    end
    on_arm do
      url "https://ohputer.com/router/downloads/8c264fd2e0a335b5152463cd6b253859a22bb90733ac40989a51e3daa2ca0f76/oh-router-v0.1.13-aarch64-unknown-linux-musl.tar.gz"
      sha256 "8c264fd2e0a335b5152463cd6b253859a22bb90733ac40989a51e3daa2ca0f76"
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
