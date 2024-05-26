import json
import os
import subprocess
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import emoji

from .Logger import BaseLogger, Logger


class PeriodEnum(str, Enum):
    LAST_DAY = "last_day"
    LAST_WEEK = "last_week"
    LAST_MONTH = "last_month"
    ALL = "all"


@dataclass
class TwitchData:
    channels_urls: list[str]
    clips_folder_path: Path
    clips_period: PeriodEnum | None = None
    clips_per_channel_limit: int | None = None
    unsupported_words_for_title: list[str] | None = None
    used_titles: list[str] | None = None


@dataclass
class ClipInfo:
    id: str
    slug: str
    title: str
    viewCount: int
    durationSeconds: int
    broadcaster: str
    quality: str
    framerate: int


class TwitchClipsDownloader:
    def __init__(
        self,
        twitch_urls: list[str],
        clips_folder_path: Path,
        logger: BaseLogger | None = None,
    ):
        self.clips_folder_path = clips_folder_path
        self.logger = logger if logger else Logger()
        self.twitch_urls = twitch_urls

    def get_clips(
        self, clips_limit: int | None = None, period: PeriodEnum | None = None
    ) -> list[dict]:
        self.logger.log("Getting clips...")
        all_clips_json = []
        for twitch_url in self.twitch_urls:
            twitch_username = twitch_url.split(r"/")[-1]
            self.logger.log(f"Getting clips from {twitch_username}")
            command = [
                "twitch-dl",
                "clips",
                twitch_username,
                "--json",
            ]
            if clips_limit is None or clips_limit == 0:
                command.append("--all")
            else:
                command.append("--limit")
                command.append(str(clips_limit))

            if period is None:
                command.append("--period")
                command.append("all_time")
            else:
                command.append("--period")
                command.append(period)

            try:
                clips_json_str = subprocess.check_output(command)
                clips_json = json.loads(clips_json_str)
                for clip_json in clips_json:
                    if clip_json not in all_clips_json:
                        all_clips_json.append(clip_json)
            except Exception as e:
                self.logger.log(
                    f"Failed to parse "
                    f"{'all' if clips_limit is None else clips_limit} "
                    f"clips from {twitch_username}"
                )
                self.logger.log(str(e))
        self.logger.log(f"Got {len(all_clips_json)} clips")
        return all_clips_json

    def generate_clip_info_dcls(self, clip_dict: dict) -> ClipInfo:
        default_quality_dict = {
            "videoQualities": [
                {
                    "frameRate": 30,
                    "quality": "360",
                }
            ]
        }
        return ClipInfo(
            id=clip_dict["id"],
            slug=clip_dict["slug"],
            title=clip_dict["title"],
            viewCount=clip_dict["viewCount"],
            durationSeconds=clip_dict["durationSeconds"],
            broadcaster=clip_dict["broadcaster"]["login"],
            quality=clip_dict.get(
                "videoQualities", default_quality_dict.get("videoQualities")
            )[0].get("quality"),
            framerate=int(
                clip_dict.get(
                    "videoQualities",
                    default_quality_dict.get("videoQualities"),
                )[0].get("frameRate")
            ),
        )

    def generate_clips_info(self, clips_json: list[dict]) -> list[ClipInfo]:
        self.logger.log("Generating clips info...")
        clips_info = []
        for clip_dict in clips_json:
            clip_info = self.generate_clip_info_dcls(clip_dict=clip_dict)
            if clip_info not in clips_info:
                clips_info.append(clip_info)
        self.logger.log("Generating clips info is done!")
        return clips_info

    def filter_clips_by_unsupported_words(
        self, clips_info: list[ClipInfo], unsupported_words: list[str]
    ) -> list[ClipInfo]:
        self.logger.log("Filtering clips by unsupported words...")

        def filter_unsupported_words(clip_info: ClipInfo) -> bool:
            for word in unsupported_words:
                if word.lower() in clip_info.title.lower():
                    return False
            return True

        filtered_clips_info = list(
            filter(filter_unsupported_words, clips_info)
        )
        reduced_by = len(clips_info) - len(filtered_clips_info)
        self.logger.log(
            "Filtering clips by unsupported words is done! "
            f"({reduced_by} clips removed)"
        )
        return filtered_clips_info

    def _demojize_clip_title(self, clip_info: ClipInfo) -> ClipInfo:
        clip_info_dict_without_title = deepcopy(clip_info.__dict__)
        clip_info_dict_without_title.pop("title", None)
        return ClipInfo(
            **clip_info_dict_without_title,
            title=str(emoji.demojize(clip_info.title)),
        )

    def demojize_clips(self, clips_info: list[ClipInfo]) -> list[ClipInfo]:
        self.logger.log("Demojizing clips titles...")
        demojized_clips = [
            self._demojize_clip_title(clip_info) for clip_info in clips_info
        ]
        self.logger.log("Demojizing clips is done!")
        return demojized_clips

    def filter_clips_by_used_titles(
        self, clips_info: list[ClipInfo], used_titles: list[str]
    ) -> tuple[list[ClipInfo], list[str]]:
        self.logger.log("Filtering clips by used titles...")
        new_used_titles = []

        def is_used_title(clip_info: ClipInfo) -> bool:
            if clip_info.title.lower() in [
                used_title.lower() for used_title in used_titles
            ]:
                return False
            if clip_info.title.lower() in [
                new_used_title.lower() for new_used_title in new_used_titles
            ]:
                return False
            new_used_titles.append(clip_info.title)
            return True

        filtered_clips_info = list(filter(is_used_title, clips_info))
        reduced_by = len(clips_info) - len(filtered_clips_info)
        self.logger.log(
            f"Filtering clips by used titles is done! ({reduced_by} clips removed)"
        )
        return filtered_clips_info, new_used_titles

    def filter_out_long_titles(
        self,
        clips_info: list[ClipInfo],
    ) -> list[ClipInfo]:
        self.logger.log("Filtering out clips with too long titles...")
        filtered_clips = [
            clip_info for clip_info in clips_info if len(clip_info.title) <= 50
        ]
        reduced_by = len(clips_info) - len(filtered_clips)
        self.logger.log(
            "Filtering out clips with too long titles is done! "
            f"({reduced_by} clips removed)"
        )
        return filtered_clips

    def sort_by_views(
        self, clips_info: list[ClipInfo], reverse: bool | None = None
    ) -> list[ClipInfo]:
        self.logger.log("Sorting clips by views...")
        is_reverse = True if reverse is None else not bool(reverse)
        sorted_clips_info = sorted(
            deepcopy(clips_info),
            key=lambda clip: clip.viewCount,
            reverse=is_reverse,
        )
        self.logger.log(
            f"Sorting clips by views is done! (Total: {len(sorted_clips_info)})"
        )
        return sorted_clips_info

    def download_clip(
        self, clip_info: ClipInfo, clip_format: str | None = None
    ) -> Path:
        self.logger.log(
            f'Downloading clip "{clip_info.title}" from: https://www.twitch.tv'
            f"/{clip_info.broadcaster}/clip/{clip_info.slug} ..."
        )
        if not clip_format:
            clip_format = "mp4"
        file_path = Path(
            f"{self.clips_folder_path}/{clip_info.id}.{clip_format}"
        )
        command = [
            "twitch-dl",
            "download",
            clip_info.slug,
            "-q",
            f"{clip_info.quality}p",
            "--overwrite",
            "-o",
            file_path,
        ]
        subprocess.check_output(command)
        self.logger.log(f"Downloaded clip: {clip_info.title}")
        return Path(file_path)

    def download_multiple_clips(
        self, clips_info: list[ClipInfo], clips_format: str | None = None
    ) -> list[Path]:
        self.logger.log("Downloading multiple clips...")
        if not clips_format:
            clips_format = "mp4"

        files_paths = []
        for clip_info in clips_info:
            file_path = self.download_clip(
                clip_info=clip_info,
                clip_format=clips_format,
            )
            files_paths.append(Path(file_path))
        self.logger.log(f"Downloaded {self._count_downloaded_clips()} clips")
        return files_paths

    def delete_clip_by_path(self, path: Path) -> tuple[bool, str]:
        self.logger.log(f"Deleting clip {path}...")
        if path.exists():
            os.remove(path)
            log_info = f"Clip deleted: {path}"
            self.logger.log(log_info)
            return True, log_info
        log_info = f"Clip not found: {path}"
        self.logger.log(log_info)
        return False, log_info

    def delete_all_clips(self) -> None:
        self.logger.log("Cleaning clips folder...")
        for dirs, _, files in os.walk(self.clips_folder_path):
            for file in files:
                file_path = os.path.join(dirs, file)
                self.delete_clip_by_path(path=Path(file_path))
        self.logger.log("Clips folder cleaned!")

    def _count_downloaded_clips(self) -> int:
        counter = 0
        for _, _, files in os.walk(self.clips_folder_path):
            for _ in files:
                counter += 1
        return counter
