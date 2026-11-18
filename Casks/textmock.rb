cask "textmock" do
  version "1.0.19"
  sha256 "c681d65d0fd64a713ab9b553831bfb19e3f79aff7955236c39d142a5c1380f4b"

  url "https://textmock.com/downloads/c681d65d0fd64a713ab9b553831bfb19e3f79aff7955236c39d142a5c1380f4b/Textmock-#{version}.zip"
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
