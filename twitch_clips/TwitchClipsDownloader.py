import json
import os
import subprocess
from pathlib import Path
from typing import List, Literal

from .Logger import BaseLogger, Logger

PERIOD = Literal["last_day", "last_week", "last_month", "all"]


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
        self, clips_limit: int | None = None, period: PERIOD | None = None
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
            if clips_limit is None:
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

    def download_clips(self, clips_slugs: List[str]) -> None:
        self.logger.log("Downloading clips...")
        command = [
            "twitch-dl",
            "download",
        ]
        for clip_slug in clips_slugs:
            command.append(str(clip_slug))
        command.append("-q")
        command.append("source")
        command.append("--overwrite")
        command.append("-o")
        command.append(f"{self.clips_folder_path}" r"{id}.{format}")

        subprocess.check_output(command)
        self.logger.log(f"Downloaded {self._count_downloaded_clips()} clips")

    def get_clips_slugs(self, clips_json: List[dict]) -> List[str]:
        self.logger.log("Getting clips slugs...")
        clips_slugs = [clip["slug"] for clip in clips_json]
        self.logger.log(f"Got {len(clips_slugs)} clips slugs")
        return clips_slugs

    def delete_clips(self) -> None:
        self.logger.log("Cleaning clips folder...")
        for dirs, _, files in os.walk(self.clips_folder_path):
            for file in files:
                file_path = os.path.join(dirs, file)
                os.remove(file_path)
                self.logger.log(f"Clip deleted: {file_path}")
        self.logger.log("Clips folder cleaned!")

    def _count_downloaded_clips(self) -> int:
        counter = 0
        for dirs, _, files in os.walk(self.clips_folder_path):
            for file in files:
                counter += 1
        return counter
