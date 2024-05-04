import time
from pathlib import Path
from typing import List

from .Driver import Driver
from .Logger import BaseLogger, Logger
from .TwitchClipsDownloader import PeriodEnum, TwitchClipsDownloader
from .YoutubeAuth import YoutubeAuth
from .YoutubeUploader import YoutubeUploader
from .YTCookieSaver import BaseYTCookieSaver, NetScapeSaver, YTCookieSaver


class TwitchClipsToYoutubeVideos:
    def __init__(
        self,
        youtube_login: str,
        youtube_password: str,
        cookies_folder_path: str,
        twitch_channels_urls: List[str],
        clips_folder_path: str,
        max_videos_to_upload: int,
        twitch_clips_period: PeriodEnum | None = None,
        clips_per_twitch_channel_limit: int | None = None,
        unsupported_words_for_title: List[str] | None = None,
        used_titles: List[str] | None = None,
        cookies_saver: BaseYTCookieSaver | None = None,
        logger: BaseLogger | None = None,
    ) -> None:
        self.youtube_login = youtube_login
        self.youtube_password = youtube_password

        self.cookies_folder_path = cookies_folder_path
        self.cookies_path = str(Path(f"{cookies_folder_path}/cookies.txt"))

        self.clips_folder_path = clips_folder_path

        self.logger = logger if logger else Logger()

        self.cookies_saver = cookies_saver if cookies_saver else NetScapeSaver()

        self.twitch_urls = twitch_channels_urls
        self.twitch_clips_period = twitch_clips_period
        self.clips_limit = clips_per_twitch_channel_limit

        self.unsupported_words = (
            unsupported_words_for_title if unsupported_words_for_title else []
        )
        self.used_titles = used_titles if used_titles else []
        self.max_videos = max_videos_to_upload

    def get_cookies(self):
        browser = Driver(headless=True, logger=self.logger)
        driver = browser.get_driver()

        yt_auth = YoutubeAuth(
            login=self.youtube_login,
            password=self.youtube_password,
            driver=driver,
            logger=self.logger,
        )
        yt_cookies = yt_auth.get_yt_cookies()

        yt_cookies_saver = YTCookieSaver(
            cookies_saver=self.cookies_saver, logger=self.logger
        )
        yt_cookies_saver.save_cookies(cookies=yt_cookies, filepath=self.cookies_path)

    def run(self) -> None:
        if not Path(self.cookies_path).exists():
            self.logger.log("Cookies file doesn't exist. Creating new one...")
            if not Path(self.cookies_folder_path).exists():
                self.logger.log("Cookies folder doesn't exist. Creating new one...")
                Path(self.cookies_folder_path).mkdir(parents=True, exist_ok=True)
            self.get_cookies()

        yt_uploader = YoutubeUploader(
            cookies_path=self.cookies_path, logger=self.logger
        )
        if not yt_uploader.has_valid_cookies():
            self.logger.log("Invalid cookies. Creating new ones...")
            self.get_cookies()

        if not Path(self.clips_folder_path).exists():
            self.logger.log("Clips folder doesn't exist. Creating new one...")
            Path(self.clips_folder_path).mkdir(parents=True, exist_ok=True)
            time.sleep(5)

        twitch_downloader = TwitchClipsDownloader(
            twitch_urls=self.twitch_urls,
            logger=self.logger,
            clips_folder_path=self.clips_folder_path,
        )

        all_clips_json = twitch_downloader.get_clips(
            period=self.twitch_clips_period, clips_limit=self.clips_limit
        )

        all_clips_info = twitch_downloader.generate_clips_info(
            clips_json=all_clips_json
        )

        filtered_clips_info_by_unsupported_words = (
            twitch_downloader.filter_clips_by_unsupported_words(
                clips_info=all_clips_info, unsupported_words=self.unsupported_words
            )
        )

        demojized_clips_info = twitch_downloader.demojize_clips(
            clips_info=filtered_clips_info_by_unsupported_words
        )

        filtered_clips_info_by_used_titles, _ = (
            twitch_downloader.filter_clips_by_used_titles(
                clips_info=demojized_clips_info, used_titles=self.used_titles
            )
        )

        sorted_clips_info_by_views = twitch_downloader.sort_by_views(
            clips_info=filtered_clips_info_by_used_titles
        )

        for clip_info in sorted_clips_info_by_views[: self.max_videos]:
            try:
                clip_path = twitch_downloader.download_clip(
                    clip_slug=clip_info.slug, clip_id=clip_info.id
                )
                title_with_author = f"{clip_info.title} @{clip_info.broadcaster}"
                description = f"Streamer: https://www.twitch.tv/{clip_info.broadcaster}"
                yt_uploader.upload(
                    title=title_with_author,
                    description=description,
                    video_path=clip_path,
                )
                twitch_downloader.delete_clip_by_path(path=clip_path)
                self.used_titles.append(clip_info.title)
            except Exception as e:
                print(e)

        twitch_downloader.delete_all_clips()
