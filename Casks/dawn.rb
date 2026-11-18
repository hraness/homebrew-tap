cask "dawn" do
  version "0.62.0"
  sha256 "a8fbabb0813ae96271de5c27c9d2b15c0e9844d07fb81415ff0276234c2aea22"

  url "https://publish.dawnav.com/mac/a8fbabb0813ae96271de5c27c9d2b15c0e9844d07fb81415ff0276234c2aea22/DAWN-#{version}.zip"
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
