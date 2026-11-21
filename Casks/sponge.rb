cask "sponge" do
  version "1.8.1"
  sha256 "a6a3c1f0b68fcd67f052690dc23087e134cf4bc44c7583fbde5ba066f994faa9"

  url "https://sponge.computer/downloads/a6a3c1f0b68fcd67f052690dc23087e134cf4bc44c7583fbde5ba066f994faa9/Sponge-#{version}.zip"
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
