import json
import os
import subprocess
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Tuple

import emoji

from .Logger import BaseLogger, Logger


class PeriodEnum(str, Enum):
    LAST_DAY = "last_day"
    LAST_WEEK = "last_week"
    LAST_MONTH = "last_month"
    ALL = "all"


@dataclass
class ClipInfo:
    id: str
    slug: str
    title: str
    viewCount: int
    durationSeconds: int
    broadcaster: str


class TwitchClipsDownloader:
    def __init__(
        self,
        twitch_urls: List[str],
        clips_folder_path: str,
        logger: BaseLogger | None = None,
    ):
        self.clips_folder_path = clips_folder_path
        self.logger = logger if logger else Logger()
        self.twitch_urls = twitch_urls

    def get_clips(
        self, clips_limit: int | None = None, period: PeriodEnum | None = None
    ) -> List[dict]:
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
        return ClipInfo(
            id=clip_dict["id"],
            slug=clip_dict["slug"],
            title=clip_dict["title"],
            viewCount=clip_dict["viewCount"],
            durationSeconds=clip_dict["durationSeconds"],
            broadcaster=clip_dict["broadcaster"]["login"],
        )

    def generate_clips_info(self, clips_json: List[dict]) -> List[ClipInfo]:
        self.logger.log("Generating clips info...")
        clips_info = []
        for clip_dict in clips_json:
            clip_info = self.generate_clip_info_dcls(clip_dict=clip_dict)
            if clip_info not in clips_info:
                clips_info.append(clip_info)
        self.logger.log("Generating clips info is done!")
        return clips_info

    def filter_clips_by_unsupported_words(
        self, clips_info: List[ClipInfo], unsupported_words: List[str]
    ) -> List[ClipInfo]:
        self.logger.log("Filtering clips by unsupported words...")

        def filter_unsupported_words(clip_info: ClipInfo) -> bool:
            for word in unsupported_words:
                if word.lower() in clip_info.title.lower():
                    return False
            return True

        self.logger.log("Filtering clips by unsupported words is done!")
        return list(filter(filter_unsupported_words, clips_info))

    def _demojize_clip_title(self, clip_info: ClipInfo) -> ClipInfo:
        clip_info_dict_without_title = deepcopy(clip_info.__dict__)
        clip_info_dict_without_title.pop("title", None)
        return ClipInfo(
            **clip_info_dict_without_title,
            title=str(emoji.demojize(clip_info.title)),
        )

    def demojize_clips(self, clips_info: List[ClipInfo]) -> List[ClipInfo]:
        self.logger.log("Demojizing clips titles...")
        demojized_clips = [
            self._demojize_clip_title(clip_info) for clip_info in clips_info
        ]
        self.logger.log("Demojizing clips is done!")
        return demojized_clips

    def filter_clips_by_used_titles(
        self, clips_info: List[ClipInfo], used_titles: List[str]
    ) -> Tuple[List[ClipInfo], List[str]]:
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
        self.logger.log("Filtering clips by used titles is done!")
        return filtered_clips_info, new_used_titles

    def sort_by_views(
        self, clips_info: List[ClipInfo], reverse: bool | None = None
    ) -> List[ClipInfo]:
        self.logger.log("Sorting clips by views...")
        is_reverse = True if reverse is None else not bool(reverse)
        sorted_clips_info = sorted(
            deepcopy(clips_info),
            key=lambda clip: clip.viewCount,
            reverse=is_reverse,
        )
        self.logger.log("Sorting clips by views is done!")
        return sorted_clips_info

    def download_clip(
        self, clip_slug: str, clip_id: str, clip_format: str | None = None
    ) -> Path:
        self.logger.log(f"Downloading clip {clip_slug}...")
        if not clip_format:
            clip_format = "mp4"
        file_path = f"{self.clips_folder_path}{clip_id}.{clip_format}"
        command = [
            "twitch-dl",
            "download",
            clip_slug,
            "-q",
            "source",
            "--overwrite",
            "-o",
            file_path,
        ]
        subprocess.check_output(command)
        self.logger.log(f"Downloaded clip {clip_slug}")
        return Path(file_path)

    def download_multiple_clips(
        self, clips_info: List[ClipInfo], clips_format: str | None = None
    ) -> List[Path]:
        self.logger.log("Downloading multiple clips...")
        if not clips_format:
            clips_format = "mp4"

        files_paths = []
        for clip_info in clips_info:
            file_path = self.download_clip(
                clip_slug=clip_info.slug,
                clip_id=clip_info.id,
                clip_format=clips_format,
            )
            files_paths.append(Path(file_path))
        self.logger.log(f"Downloaded {self._count_downloaded_clips()} clips")
        return files_paths

    def delete_clip_by_path(self, path: str | Path) -> None:
        self.logger.log(f"Deleting clip {path}...")
        if not isinstance(path, str):
            path = str(path)
        if Path(path).exists():
            os.remove(path)
            self.logger.log(f"Clip deleted: {path}")
            return
        self.logger.log(f"Clip not found: {path}")
        return

    def delete_all_clips(self) -> None:
        self.logger.log("Cleaning clips folder...")
        for dirs, _, files in os.walk(self.clips_folder_path):
            for file in files:
                file_path = os.path.join(dirs, file)
                self.delete_clip_by_path(path=file_path)
        self.logger.log("Clips folder cleaned!")

    def _count_downloaded_clips(self) -> int:
        counter = 0
        for _, _, files in os.walk(self.clips_folder_path):
            for _ in files:
                counter += 1
        return counter
