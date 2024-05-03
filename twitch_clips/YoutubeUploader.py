from youtube_up import YTUploaderSession


class YoutubeUploader:
    def __init__(self, cookies_path: str) -> None:
        self.uploader = YTUploaderSession.from_cookies_txt(
            cookies_txt_path=cookies_path
        )
        self._validate_cookies()

    def _validate_cookies(self) -> None:
        if not self.uploader.has_valid_cookies():
            raise Exception("Invalid cookies provided")
        else:
            print("Cookies validated")
