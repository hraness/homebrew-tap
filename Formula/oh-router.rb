# frozen_string_literal: true

# Binary distribution of oh-router from immutable ohrouter.com release archives.
# Regenerate checksums/versions with: node tools/oh-router-formula.mjs --refresh
class OhRouter < Formula
  desc "Session router, terminal safety guard and board worker for coding agents"
  homepage "https://ohrouter.com"
  license any_of: ["MIT", "Apache-2.0"]

  on_macos do
    on_arm do
      url "https://ohrouter.com/downloads/2ada77073d1fa921f35c13010c7514e680efe1643b124fd5390d46bdf9cf2962/oh-router-v0.1.0-aarch64-apple-darwin.tar.gz"
      sha256 "2ada77073d1fa921f35c13010c7514e680efe1643b124fd5390d46bdf9cf2962"
    end
  end

  on_linux do
    on_intel do
      url "https://ohrouter.com/downloads/6ba79b5de7d40676f3415f058455b9a2bd439be994554700b2c1d411842a053c/oh-router-v0.1.0-x86_64-unknown-linux-gnu.tar.gz"
      sha256 "6ba79b5de7d40676f3415f058455b9a2bd439be994554700b2c1d411842a053c"
    end
    on_arm do
      url "https://ohrouter.com/downloads/66dbcafdc0b99bc9a5bd43340a8216ce3b39af8bc7e69f3543fc43b54379b614/oh-router-v0.1.0-aarch64-unknown-linux-musl.tar.gz"
      sha256 "66dbcafdc0b99bc9a5bd43340a8216ce3b39af8bc7e69f3543fc43b54379b614"
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
