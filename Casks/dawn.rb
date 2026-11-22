cask "dawn" do
  version "0.66.2"
  sha256 "7627355c1c58c9af8ca163a1868ef40ea716c9f64210cbdee6452ffc1f5dce22"

  url "https://publish.dawnav.com/mac/7627355c1c58c9af8ca163a1868ef40ea716c9f64210cbdee6452ffc1f5dce22/DAWN-#{version}.zip"
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
