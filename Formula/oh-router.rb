# frozen_string_literal: true

# Binary distribution of oh-router from immutable ohrouter.com release archives.
# Regenerate checksums/versions with: node tools/oh-router-formula.mjs --refresh
class OhRouter < Formula
  desc "Session router, terminal safety guard and board worker for coding agents"
  homepage "https://ohrouter.com"
  url "https://ohrouter.com/downloads/a530ebdf104f94efd651e2f1193904cf52ce45544f3b65b81731befc6c60892b/oh-router-v0.1.5-aarch64-apple-darwin.tar.gz"
  sha256 "a530ebdf104f94efd651e2f1193904cf52ce45544f3b65b81731befc6c60892b"
  license any_of: ["MIT", "Apache-2.0"]

  on_macos do
    on_intel do
      url "https://ohrouter.com/downloads/a39a5ffdac45be086ee4ce922f19584c63a6fd570abdea444afbb760abdde6d0/oh-router-v0.1.5-x86_64-apple-darwin.tar.gz"
      sha256 "a39a5ffdac45be086ee4ce922f19584c63a6fd570abdea444afbb760abdde6d0"
    end
  end

  on_linux do
    on_intel do
      url "https://ohrouter.com/downloads/9ba79b40f9c9150614a0af083b7cdc601a3c076c66efa4eb6f29be1e00667156/oh-router-v0.1.5-x86_64-unknown-linux-gnu.tar.gz"
      sha256 "9ba79b40f9c9150614a0af083b7cdc601a3c076c66efa4eb6f29be1e00667156"
    end
    on_arm do
      url "https://ohrouter.com/downloads/55ca95defb5ccc6de116ee9665b2e54572e1a10b501b1e6e06dba7d257eca286/oh-router-v0.1.5-aarch64-unknown-linux-musl.tar.gz"
      sha256 "55ca95defb5ccc6de116ee9665b2e54572e1a10b501b1e6e06dba7d257eca286"
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
