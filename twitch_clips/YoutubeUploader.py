from youtube_up import YTUploaderSession

from .Logger import BaseLogger, Logger


class YoutubeUploader:
    def __init__(self, cookies_path: str, logger: BaseLogger | None = None) -> None:
        self.logger = logger if logger else Logger()
        self.uploader = YTUploaderSession.from_cookies_txt(
            cookies_txt_path=cookies_path
        )
        self.logger.log("Validating cookies...")
        self._validate_cookies()
        self.logger.log("Cookies validated!")

    def _validate_cookies(self) -> None:
        if not self.uploader.has_valid_cookies():
            raise Exception("Invalid cookies provided")
