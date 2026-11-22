cask "sponge-app" do
  version "1.9.0"
  sha256 "c7d12dd8637cb8e6f6a69e915796dd4d78ffff9aa30f7cca1e6756dfd4bf7e09"

  url "https://sponge.computer/downloads/c7d12dd8637cb8e6f6a69e915796dd4d78ffff9aa30f7cca1e6756dfd4bf7e09/Sponge-#{version}.zip"
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
