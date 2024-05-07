from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List


class BasePrivacyEnum(str, Enum):
    PRIVATE = "private"
    PUBLIC = "public"


@dataclass
class VideoInfo:
    video_path: str | Path
    title: str
    description: str | None = None
    tags: List[str] | None = None
    privacy: BasePrivacyEnum | None = None


class BaseUploader(ABC):
    @abstractmethod
    def upload(
        self,
        video_info: VideoInfo,
    ) -> None:
        """Upload video to YouTube."""
