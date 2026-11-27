# frozen_string_literal: true

# Binary distribution of oh-router from immutable ohputer.com/router release archives.
# Regenerate checksums/versions with: node tools/oh-router-formula.mjs --refresh
class OhRouter < Formula
  desc "Session router, terminal safety guard and board worker for coding agents"
  homepage "https://ohputer.com/router"
  url "https://ohputer.com/router/downloads/1f99819ac9c9d445c1815d9692b753bda095a799198c8cad93faa262b09d4e5a/oh-router-v0.1.14-aarch64-apple-darwin.tar.gz"
  sha256 "1f99819ac9c9d445c1815d9692b753bda095a799198c8cad93faa262b09d4e5a"
  license any_of: ["MIT", "Apache-2.0"]

  on_macos do
    on_intel do
      url "https://ohputer.com/router/downloads/6798a1e3180e708cb028ecd970df86b16a9ee60ff2339f27aea0fdfa79a3dd19/oh-router-v0.1.14-x86_64-apple-darwin.tar.gz"
      sha256 "6798a1e3180e708cb028ecd970df86b16a9ee60ff2339f27aea0fdfa79a3dd19"
    end
  end

  on_linux do
    on_intel do
      url "https://ohputer.com/router/downloads/e03a3032af00b718536d73a5113f698a13be53601a423042e410d443e05fdadc/oh-router-v0.1.14-x86_64-unknown-linux-gnu.tar.gz"
      sha256 "e03a3032af00b718536d73a5113f698a13be53601a423042e410d443e05fdadc"
    end
    on_arm do
      url "https://ohputer.com/router/downloads/a4ee8a197f3b41e100b327325d9a232f253124db78437a91456a3d16714e6fc5/oh-router-v0.1.14-aarch64-unknown-linux-musl.tar.gz"
      sha256 "a4ee8a197f3b41e100b327325d9a232f253124db78437a91456a3d16714e6fc5"
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
