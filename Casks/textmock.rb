cask "textmock" do
  version "1.0.20"
  sha256 "d8f18b2d16a02030aaa6709387ea960f72b97807d06beeedcc7dbf312bb44c05"

  url "https://textmock.com/downloads/d8f18b2d16a02030aaa6709387ea960f72b97807d06beeedcc7dbf312bb44c05/Textmock-#{version}.zip"
  name "Textmock"
  desc "Private AI chats and iMessage-style conversation mockups"
  homepage "https://textmock.com/mac"

  livecheck do
    url "https://textmock.com/appcast.xml"
    strategy :sparkle, &:short_version
  end

  auto_updates true
  depends_on macos: :sonoma

  app "Textmock.app"
  binary "#{appdir}/Textmock.app/Contents/Helpers/textmock"
end
