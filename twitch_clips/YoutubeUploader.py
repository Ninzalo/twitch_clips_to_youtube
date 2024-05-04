from pathlib import Path

from youtube_up import AllowCommentsEnum, Metadata, PrivacyEnum, YTUploaderSession

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

    def upload(
        self,
        title: str,
        video_path: str | Path,
        description: str | None = None,
        privacy: PrivacyEnum | None = None,
        allow_comments: AllowCommentsEnum | None = None,
    ) -> None:
        if description is None:
            description = ""
        if privacy is None:
            privacy = PrivacyEnum.PUBLIC
        if allow_comments is None:
            allow_comments = AllowCommentsEnum.HOLD_INAPPROPRIATE
        if not isinstance(video_path, str):
            video_path = str(video_path)

        self.logger.log(f"Uploading video: {title}")
        video_metadata = Metadata(
            title=title,
            description=description,
            privacy=privacy,
            made_for_kids=False,
            allow_comments_mode=allow_comments,
        )
        self.uploader.upload(file_path=video_path, metadata=video_metadata)
        self.logger.log(f"Video uploaded: {title}")
