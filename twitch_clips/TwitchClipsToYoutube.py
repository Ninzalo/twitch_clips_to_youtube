import argparse
import os
import time
from pathlib import Path
from typing import List

from .BaseYoutubeUploader import BaseUploader
from .CookieFormatter import NetScapeFormatter
from .Logger import BaseLogger, Logger
from .TwitchClipsDownloader import ClipInfo, PeriodEnum, TwitchClipsDownloader
from .YoutubeUploaderViaApi import YoutubeUploaderViaApi
from .YoutubeUploaderViaCookies import (
    CookiesUploaderSettings,
    YoutubeUploaderViaCookies,
)


class TwitchClipsToYoutube:
    def __init__(
        self,
        twitch_channels_urls: List[str],
        clips_folder_path: str,
        max_videos_to_upload: int,
        cookies_settings: CookiesUploaderSettings | None = None,
        client_secret_folder_path: str | None = None,
        twitch_clips_period: PeriodEnum | None = None,
        clips_per_twitch_channel_limit: int | None = None,
        unsupported_words_for_title: List[str] | None = None,
        used_titles: List[str] | None = None,
        logger: BaseLogger | None = None,
    ) -> None:
        self.logger = logger if logger else Logger()

        self.retries = None
        self.cookies_folder_path = f"{os.getcwd()}"
        self.use_cookies = False
        if cookies_settings is not None:
            self.cookies_folder_path = cookies_settings.cookies_folder_path
            self.retries = cookies_settings.cookies_validation_retries
            self.use_cookies = True
        self.json_cookies_path = str(Path(f"{self.cookies_folder_path}/cookies.json"))
        self.cookies_path = str(Path(f"{self.cookies_folder_path}/cookies.txt"))

        self.client_secret_folder_path = f"{os.getcwd()}"
        self.use_client_secret = False
        if client_secret_folder_path is not None:
            self.client_secret_folder_path = client_secret_folder_path
            self.use_client_secret = True
        self.client_secret_path = str(
            Path(f"{client_secret_folder_path}/client_secret.json")
        )

        if not self.use_cookies and not self.use_client_secret:
            raise ValueError("No cookies or client secret provided")

        self.clips_folder_path = clips_folder_path

        self.twitch_urls = twitch_channels_urls
        self.twitch_clips_period = twitch_clips_period
        self.clips_limit = clips_per_twitch_channel_limit

        self.unsupported_words = (
            unsupported_words_for_title if unsupported_words_for_title else []
        )
        self.used_titles = used_titles if used_titles else []
        self.max_videos = max_videos_to_upload
        if self.max_videos < 1:
            raise ValueError("Max videos must be at least 1")

        self.twitch_downloader = TwitchClipsDownloader(
            twitch_urls=self.twitch_urls,
            logger=self.logger,
            clips_folder_path=self.clips_folder_path,
        )

    def _create_clips_folder(self) -> None:
        if not Path(self.clips_folder_path).exists():
            self.logger.log("Clips folder doesn't exist. Creating new one...")
            Path(self.clips_folder_path).mkdir(parents=True, exist_ok=True)
            time.sleep(5)

    def _check_cookies_file(self) -> bool:
        if not Path(self.cookies_folder_path).exists():
            self.logger.log("Cookies folder doesn't exist. Creating new one...")
            Path(self.cookies_folder_path).mkdir(parents=True, exist_ok=True)
            return False
        if not Path(self.cookies_path).exists():
            if Path(self.json_cookies_path).exists():
                try:
                    netscape_formatter = NetScapeFormatter(logger=self.logger)
                    netscape_formatter.save(
                        json_cookies_file_path=self.json_cookies_path,
                        formatted_cookies_file_path=self.cookies_path,
                    )
                    return True
                except Exception:
                    pass
            self.logger.log("Cookies file doesn't exist.")
            return False
        return True

    def _check_client_secret_file(self) -> bool:
        if not Path(self.client_secret_folder_path).exists():
            self.logger.log("Client secret folder doesn't exist. Creating new one...")
            Path(self.client_secret_folder_path).mkdir(parents=True, exist_ok=True)
            return False
        if not Path(self.client_secret_path).exists():
            self.logger.log("Client secret file doesn't exist.")
            return False
        return True

    def _filter_clips(self, clips: List[ClipInfo]) -> List[ClipInfo]:
        filtered_clips_info_by_unsupported_words = (
            self.twitch_downloader.filter_clips_by_unsupported_words(
                clips_info=clips, unsupported_words=self.unsupported_words
            )
        )
        demojized_clips_info = self.twitch_downloader.demojize_clips(
            clips_info=filtered_clips_info_by_unsupported_words
        )
        filtered_clips_info_by_used_titles, _ = (
            self.twitch_downloader.filter_clips_by_used_titles(
                clips_info=demojized_clips_info, used_titles=self.used_titles
            )
        )
        return filtered_clips_info_by_used_titles

    def _publish_clip(self, clip_info: ClipInfo, yt_uploader: BaseUploader) -> None:
        clip_path = self.twitch_downloader.download_clip(
            clip_slug=clip_info.slug, clip_id=clip_info.id
        )
        title_with_author = f"{clip_info.title} @{clip_info.broadcaster}"
        description = f"Streamer: https://www.twitch.tv/{clip_info.broadcaster}"
        yt_uploader.upload(
            video_path=clip_path,
            title=title_with_author,
            description=description,
            tags=None,
            privacy=None,
        )
        self.twitch_downloader.delete_clip_by_path(path=clip_path)
        self.used_titles.append(clip_info.title)

    def run(self) -> None:
        yt_uploader = None
        if self.use_cookies:
            if self._check_cookies_file():
                yt_uploader = YoutubeUploaderViaCookies(
                    cookies_path=self.cookies_path,
                    retries=self.retries,
                    logger=self.logger,
                )
                if not yt_uploader.has_valid_cookies():
                    self.logger.log("Invalid cookies.")
                    yt_uploader = None
                else:
                    self.logger.log("Cookies-Uploader initialized.")
        if yt_uploader is None and self.use_client_secret:
            parser = argparse.ArgumentParser()
            parser.add_argument(
                "--force",
                "-f",
                action="store_true",
                help="Force run unsafe API uploader",
                required=True,
            )
            _ = parser.parse_args()
            self.logger.log("Forced unsafe API uploader.")
            if self._check_client_secret_file():
                try:
                    yt_uploader = YoutubeUploaderViaApi(
                        client_secret=self.client_secret_path,
                        logger=self.logger,
                    )
                    self.max_videos = min(self.max_videos, 2)
                    self.logger.log("Max videos reduced to 2")
                    self.logger.log("API-Uploader initialized.")
                except:
                    self.logger.log(
                        "Invalid client secret. Retry or change client secret."
                    )
                    yt_uploader = None

        if yt_uploader is None:
            raise ValueError("No valid cookies or client secret provided")

        self._create_clips_folder()

        all_clips_json = self.twitch_downloader.get_clips(
            period=self.twitch_clips_period, clips_limit=self.clips_limit
        )

        all_clips_info = self.twitch_downloader.generate_clips_info(
            clips_json=all_clips_json
        )

        filtered_clips = self._filter_clips(clips=all_clips_info)

        sorted_clips_info_by_views = self.twitch_downloader.sort_by_views(
            clips_info=filtered_clips
        )

        for clip_info in sorted_clips_info_by_views[: self.max_videos]:
            try:
                self._publish_clip(clip_info=clip_info, yt_uploader=yt_uploader)
            except Exception as e:
                self.logger.log(f"FInished due to an error: {e}")
                break

        self.twitch_downloader.delete_all_clips()
