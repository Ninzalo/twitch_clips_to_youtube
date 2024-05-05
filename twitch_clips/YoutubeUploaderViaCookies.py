from pathlib import Path
from typing import List

from youtube_up import AllowCommentsEnum, Metadata, PrivacyEnum, YTUploaderSession

from .BaseYoutubeUploader import BasePrivacyEnum, BaseUploader
from .Logger import BaseLogger, Logger


class YoutubeUploaderViaCookies(BaseUploader):
    def __init__(
        self,
        cookies_path: str,
        logger: BaseLogger | None = None,
    ) -> None:
        self.logger = logger if logger else Logger()
        self.cookies_path = cookies_path
        self.uploader = YTUploaderSession.from_cookies_txt(
            cookies_txt_path=cookies_path
        )

    def has_valid_cookies(self) -> bool:
        """Checks if the provided cookies file is valid."""
        self.logger.log("Validating cookies...")
        if not self.uploader.has_valid_cookies():
            self.logger.log("Invalid cookies provided, or cookies file not found")
            return False
        self.logger.log("Cookies validated!")
        return True

    def upload(
        self,
        video_path: str | Path,
        title: str,
        description: str | None = None,
        tags: List[str] | None = None,
        privacy: BasePrivacyEnum | None = None,
    ) -> None:
        privacy_status = PrivacyEnum.PUBLIC
        if description is None:
            description = ""
        if privacy is None:
            privacy_status = PrivacyEnum.PUBLIC
        if not isinstance(video_path, str):
            video_path = str(video_path)
        if tags is None:
            tags = []
        if privacy is not None:
            if privacy == BasePrivacyEnum.PRIVATE:
                privacy_status = PrivacyEnum.PRIVATE
            if privacy == BasePrivacyEnum.PUBLIC:
                privacy_status = PrivacyEnum.PUBLIC

        self.logger.log(f"Uploading video: {title}")
        video_metadata = Metadata(
            title=title,
            description=description,
            privacy=privacy_status,
            made_for_kids=False,
            allow_comments_mode=AllowCommentsEnum.HOLD_INAPPROPRIATE,
            tags=tags,
        )
        try:
            self.uploader.upload(file_path=video_path, metadata=video_metadata)
            self.logger.log(f"Video uploaded: {title}")
        except Exception as e:
            raise RuntimeError(f"Error uploading video: {title}") from e
