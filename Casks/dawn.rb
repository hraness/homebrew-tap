cask "dawn" do
  version "0.67.2"
  sha256 "e9ab25e3b759a085dc86d58d990c1555cad57ad693153dfc8b68c0a691750b38"

  url "https://publish.dawnav.com/mac/e9ab25e3b759a085dc86d58d990c1555cad57ad693153dfc8b68c0a691750b38/DAWN-#{version}.zip"
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
