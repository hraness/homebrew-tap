cask "dawn" do
  version "0.61.0"
  sha256 "47e24a793be3ce804b958d8a1e893c6881ab81eccacaf271f81e7788bbfe93ff"

  url "https://publish.dawnav.com/mac/47e24a793be3ce804b958d8a1e893c6881ab81eccacaf271f81e7788bbfe93ff/DAWN-#{version}.zip"
  name "DAWN"
  desc "Make a loop from a prompt and shape it into a song while it plays"
  homepage "https://dawnav.com/desktop"

  livecheck do
    url "https://dawnav.com/appcast.xml"
    strategy :sparkle, &:short_version
  end

  auto_updates true
  depends_on arch: :arm64
  depends_on macos: :ventura

  app "DAWN.app"
  binary "#{appdir}/DAWN.app/Contents/Resources/bin/dawn"
end
