from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List


class BasePrivacyEnum(str, Enum):
    PRIVATE = "private"
    PUBLIC = "public"


class BaseLanguageEnum(str, Enum):
    NOT_APPLICABLE = "zxx"
    RUSSIAN = "ru"
    ENGLISH = "en"
    ENGLISH_INDIA = "en-IN"
    ENGLISH_UNITED_KINGDOM = "en-GB"
    ENGLISH_UNITED_STATES = "en-US"


class BaseLicenseEnum(str, Enum):
    STANDARD = "standard"
    CREATIVE_COMMONS = "creative_commons"


@dataclass
class VideoInfo:
    video_path: Path
    title: str
    description: str | None = None
    tags: List[str] | None = None
    made_for_kids: bool | None = None
    privacy: BasePrivacyEnum | None = None
    language: BaseLanguageEnum | None = None
    license_: BaseLicenseEnum | None = None


class BaseUploader(ABC):
    @abstractmethod
    def upload(
        self,
        video_info: VideoInfo,
    ) -> None:
        """Upload video to YouTube."""

    @abstractmethod
    def close_session(self) -> None:
        """Close session with YouTube."""
