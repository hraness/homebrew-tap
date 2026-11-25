# frozen_string_literal: true

# Binary distribution of oh-router from immutable ohrouter.com release archives.
# Regenerate checksums/versions with: node tools/oh-router-formula.mjs --refresh
class OhRouter < Formula
  desc "Session router, terminal safety guard and board worker for coding agents"
  homepage "https://ohrouter.com"
  url "https://ohrouter.com/downloads/4010a9b36cff7f7d5d5ca494ad4656da1b3e00e6bf1de7668a0bd6b998ccc6bb/oh-router-v0.1.9-aarch64-apple-darwin.tar.gz"
  sha256 "4010a9b36cff7f7d5d5ca494ad4656da1b3e00e6bf1de7668a0bd6b998ccc6bb"
  license any_of: ["MIT", "Apache-2.0"]

  on_macos do
    on_intel do
      url "https://ohrouter.com/downloads/fff3b7e223d919a2e7a567a21ccab2c5e65df39a6dde62099f4838f396ddaf26/oh-router-v0.1.9-x86_64-apple-darwin.tar.gz"
      sha256 "fff3b7e223d919a2e7a567a21ccab2c5e65df39a6dde62099f4838f396ddaf26"
    end
  end

  on_linux do
    on_intel do
      url "https://ohrouter.com/downloads/25dc284fcb2f0583e415a1c140df34572668b53550c34b3e967fb8cf84a2be33/oh-router-v0.1.9-x86_64-unknown-linux-gnu.tar.gz"
      sha256 "25dc284fcb2f0583e415a1c140df34572668b53550c34b3e967fb8cf84a2be33"
    end
    on_arm do
      url "https://ohrouter.com/downloads/1023c9635999f17b2fe118106d340c512bb439b01f855f0618c7b043c941d98d/oh-router-v0.1.9-aarch64-unknown-linux-musl.tar.gz"
      sha256 "1023c9635999f17b2fe118106d340c512bb439b01f855f0618c7b043c941d98d"
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
