import time
from dataclasses import dataclass
from pathlib import Path
from random import randint

from youtube_up import AllowCommentsEnum, Metadata, PrivacyEnum, YTUploaderSession

from .BaseYoutubeUploader import BasePrivacyEnum, BaseUploader, VideoInfo
from .Logger import BaseLogger, Logger


@dataclass
class CookiesUploaderSettings:
    cookies_folder_path: Path
    cookies_validation_retries: int


class YoutubeUploaderViaCookies(BaseUploader):
    def __init__(
        self,
        cookies_path: Path,
        retries: int | None = None,
        logger: BaseLogger | None = None,
    ) -> None:
        self.logger = logger if logger else Logger()
        self.cookies_path = str(cookies_path)
        self.retries = retries if retries else 3
        self.uploader = self._get_uploader()

    def _get_uploader(self) -> YTUploaderSession:
        for retry in range(self.retries):
            try:
                uploader = YTUploaderSession.from_cookies_txt(
                    cookies_txt_path=self.cookies_path
                )
                return uploader
            except Exception:
                self.logger.log(
                    "Failed to get Cookie-Uploader. "
                    f"Attempt: {retry + 1}/{self.retries}"
                )
        raise RuntimeError(
            f"Failed to get Cookie-Uploader after {self.retries} attempts"
        )

    def has_valid_cookies(self) -> bool:
        """Checks if the provided cookies file is valid."""
        self.logger.log("Validating cookies...")
        is_valid = False
        for retry in range(self.retries):
            if not self.uploader.has_valid_cookies():
                self.logger.log(
                    "Invalid cookies provided, or cookies file not found. "
                    f"Attempt: {retry + 1}/{self.retries}"
                )
                is_valid = False
                time.sleep(randint(0, 2))
                continue
            is_valid = True
            break
        if not is_valid:
            return False
        self.logger.log("Cookies validated!")
        return True

    def upload(
        self,
        video_info: VideoInfo,
    ) -> None:
        privacy_status = PrivacyEnum.PUBLIC

        description = video_info.description or ""

        tags = video_info.tags or []

        if video_info.privacy is None:
            privacy_status = PrivacyEnum.PUBLIC
        if video_info.privacy is not None:
            if video_info.privacy == BasePrivacyEnum.PRIVATE:
                privacy_status = PrivacyEnum.PRIVATE
            if video_info.privacy == BasePrivacyEnum.PUBLIC:
                privacy_status = PrivacyEnum.PUBLIC

        self.logger.log(f"Uploading video: {video_info.title}")
        video_metadata = Metadata(
            title=video_info.title,
            description=description,
            privacy=privacy_status,
            made_for_kids=False,
            allow_comments_mode=AllowCommentsEnum.HOLD_INAPPROPRIATE,
            tags=tags,
        )
        try:
            self.uploader.upload(
                file_path=str(video_info.video_path), metadata=video_metadata
            )
            self.logger.log(f"Video uploaded: {video_info.title}")
        except Exception as e:
            raise RuntimeError(
                f"Error uploading video: {video_info.title} ({e})"
            ) from e
