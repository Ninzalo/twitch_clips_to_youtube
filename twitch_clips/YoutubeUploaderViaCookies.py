import time
from dataclasses import dataclass
from pathlib import Path
from random import randint

from youtube_up import (
    AllowCommentsEnum,
    LanguageEnum,
    LicenseEnum,
    Metadata,
    PrivacyEnum,
    YTUploaderSession,
)

from .BaseYoutubeUploader import (
    BaseLanguageEnum,
    BaseLicenseEnum,
    BasePrivacyEnum,
    BaseUploader,
    VideoInfo,
)
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
                return YTUploaderSession.from_cookies_txt(
                    cookies_txt_path=self.cookies_path,
                )

            except Exception:
                self.logger.log(
                    "Failed to get Cookie-Uploader. "
                    f"Attempt: {retry + 1}/{self.retries}",
                )
        get_uploader_error = (
            f"Failed to get Cookie-Uploader after {self.retries} attempts"
        )
        raise RuntimeError(get_uploader_error)

    def has_valid_cookies(self) -> bool:
        """Check if the provided cookies file is valid."""
        self.logger.log("Validating cookies...")
        is_valid = False
        for retry in range(self.retries):
            if not self.uploader.has_valid_cookies():
                self.logger.log(
                    "Invalid cookies provided, or cookies file not found. "
                    f"Attempt: {retry + 1}/{self.retries}",
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

        language = LanguageEnum.RUSSIAN
        if video_info.language is None:
            language = LanguageEnum.RUSSIAN
        if video_info.language is not None:
            if video_info.language == BaseLanguageEnum.NOT_APPLICABLE:
                language = LanguageEnum.NOT_APPLICABLE
            if video_info.language == BaseLanguageEnum.RUSSIAN:
                language = LanguageEnum.RUSSIAN
            if video_info.language == BaseLanguageEnum.ENGLISH:
                language = LanguageEnum.ENGLISH
            if video_info.language == BaseLanguageEnum.ENGLISH_INDIA:
                language = LanguageEnum.ENGLISH_INDIA
            if video_info.language == BaseLanguageEnum.ENGLISH_UNITED_KINGDOM:
                language = LanguageEnum.ENGLISH_UNITED_KINGDOM
            if video_info.language == BaseLanguageEnum.ENGLISH_UNITED_STATES:
                language = LanguageEnum.ENGLISH_UNITED_STATES

        license_ = LicenseEnum.STANDARD
        if video_info.license_ is None:
            license_ = LicenseEnum.STANDARD
        if video_info.license_ is not None:
            if video_info.license_ == BaseLicenseEnum.STANDARD:
                license_ = LicenseEnum.STANDARD
            if video_info.license_ == BaseLicenseEnum.CREATIVE_COMMONS:
                license_ = LicenseEnum.CREATIVE_COMMONS

        self.logger.log(f"Uploading video: {video_info.title}")
        video_metadata = Metadata(
            title=video_info.title,
            description=description,
            tags=tags,
            allow_comments_mode=AllowCommentsEnum.HOLD_INAPPROPRIATE,
            can_view_ratings=True,
            privacy=privacy_status,
            audio_language=language,
            license=license_,
            made_for_kids=video_info.made_for_kids or False,
        )

        for attempt in range(self.retries):
            try:
                self.uploader.upload(
                    file_path=str(video_info.video_path),
                    metadata=video_metadata,
                )
                self.logger.log(f"Video uploaded: {video_info.title}")
                return
            except Exception as e:
                if attempt < self.retries - 1 and "Daily limit" not in str(e):
                    self.logger.log(
                        f"Error uploading video: {video_info.title}. "
                        f"Retrying... ({e})",
                    )
                    time.sleep(randint(3, 10))
                    continue
                upload_error = (
                    f"Failed to upload video: {video_info.title} ({e})"
                )
                raise RuntimeError(upload_error) from e

    def close_session(self) -> None:
        self.uploader._session.close()
