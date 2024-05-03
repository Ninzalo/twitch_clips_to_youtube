from youtube_up import YTUploaderSession

from .Logger import BaseLogger, Logger


class YoutubeUploader:
    def __init__(self, cookies_path: str, logger: BaseLogger | None = None) -> None:
        self.logger = logger if logger else Logger()
        self.cookies_path = cookies_path
        self.uploader = YTUploaderSession.from_cookies_txt(
            cookies_txt_path=cookies_path
        )

    def has_valid_cookies(self) -> bool:
        self.logger.log("Validating cookies...")
        if not self.uploader.has_valid_cookies():
            self.logger.log("Invalid cookies provided, or cookies file not found")
            return False
        self.logger.log("Cookies validated!")
        return True
