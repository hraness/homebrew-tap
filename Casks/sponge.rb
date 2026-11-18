cask "sponge" do
  version "1.0.2"
  sha256 "33c09e06d69ed8a0ccf0e3565931665876c58fdf91cfb131fdd9ace898624dce"

  url "https://sponge.computer/downloads/33c09e06d69ed8a0ccf0e3565931665876c58fdf91cfb131fdd9ace898624dce/Sponge-#{version}.zip"
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
