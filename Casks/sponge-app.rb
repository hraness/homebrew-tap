cask "sponge-app" do
  version "1.10.0"
  sha256 "7bda41b4a0d91febf1fd0e2364b79cfc06d615dfc3caa39e2f2d04d8105c2694"

  url "https://sponge.computer/downloads/7bda41b4a0d91febf1fd0e2364b79cfc06d615dfc3caa39e2f2d04d8105c2694/Sponge-#{version}.zip"
  name "Sponge"
  desc "Reading library with share-menu, menu bar and shortcut saving"
  homepage "https://sponge.computer/mac"

  livecheck do
    url "https://sponge.computer/mac/appcast.xml"
    strategy :sparkle, &:short_version
  end

  auto_updates true
  depends_on macos: :sequoia

  app "Sponge.app"
end
