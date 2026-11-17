cask "sponge" do
  version "1.0.1,278"
  sha256 "b6e02b59190f63bd3d713cec0ed10a096504559d0747349acdca3ba66b282e4c"

  url "https://sponge.computer/downloads/b6e02b59190f63bd3d713cec0ed10a096504559d0747349acdca3ba66b282e4c/Sponge-#{version.csv.first}.zip"
  name "Sponge"
  desc "Reading library with share-menu, menu bar and shortcut saving"
  homepage "https://sponge.computer/mac"

  livecheck do
    url "https://sponge.computer/mac/appcast.xml"
    strategy :sparkle
  end

  auto_updates true
  depends_on macos: :sequoia

  app "Sponge.app"
end
