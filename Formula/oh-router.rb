# frozen_string_literal: true

# Binary distribution of oh-router from immutable ohrouter.com release archives.
# Regenerate checksums/versions with: node tools/oh-router-formula.mjs --refresh
class OhRouter < Formula
  desc "Session router, terminal safety guard and board worker for coding agents"
  homepage "https://ohrouter.com"
  url "https://ohrouter.com/downloads/c236cdf58e8c95f797a2ca9b079399a3c2bac1f800529ecca5d060e91b37e9dd/oh-router-v0.1.7-aarch64-apple-darwin.tar.gz"
  sha256 "c236cdf58e8c95f797a2ca9b079399a3c2bac1f800529ecca5d060e91b37e9dd"
  license any_of: ["MIT", "Apache-2.0"]

  on_macos do
    on_intel do
      url "https://ohrouter.com/downloads/f3a5619a7182a641dde58f715bf342d47d1f78e054c83b12ecd99cd0295b9cda/oh-router-v0.1.7-x86_64-apple-darwin.tar.gz"
      sha256 "f3a5619a7182a641dde58f715bf342d47d1f78e054c83b12ecd99cd0295b9cda"
    end
  end

  on_linux do
    on_intel do
      url "https://ohrouter.com/downloads/2134d3a5bed0d8bbcd52143bc034c64357bfbfd17064878d73640c154db3a1c7/oh-router-v0.1.7-x86_64-unknown-linux-gnu.tar.gz"
      sha256 "2134d3a5bed0d8bbcd52143bc034c64357bfbfd17064878d73640c154db3a1c7"
    end
    on_arm do
      url "https://ohrouter.com/downloads/7b32aaf9ff0865e69f86c4ead7034bbb8be0fdc368f19bb74409b84f23f58762/oh-router-v0.1.7-aarch64-unknown-linux-musl.tar.gz"
      sha256 "7b32aaf9ff0865e69f86c4ead7034bbb8be0fdc368f19bb74409b84f23f58762"
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
