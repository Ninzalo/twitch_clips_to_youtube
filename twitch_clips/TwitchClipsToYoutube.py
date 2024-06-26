import argparse
from dataclasses import dataclass
from pathlib import Path

from .BaseYoutubeUploader import (
    BaseLanguageEnum,
    BaseLicenseEnum,
    BasePrivacyEnum,
    BaseUploader,
    VideoInfo,
)
from .CookieFormatter import JSONNetScapeFormatter, StdinNetScapeFormatter
from .Logger import BaseLogger, Logger
from .TwitchClipsDownloader import ClipInfo, TwitchClipsDownloader, TwitchData
from .VerticalVideoConverter import VerticalVideoConverter
from .YoutubeUploaderViaCookies import (
    CookiesUploaderSettings,
    YoutubeUploaderViaCookies,
)


@dataclass
class VideoProperties:
    license_: BaseLicenseEnum | None = None
    language: BaseLanguageEnum | None = None
    privacy: BasePrivacyEnum | None = None
    made_for_kids: bool | None = None


@dataclass
class CustomVideoMetadata:
    custom_description: str | None = None
    custom_tags: list[str] | None = None
    streamer_url_in_desc: bool | None = None
    streamer_tag_in_title: bool | None = None
    shorts_tag_in_title: bool | None = None
    video_properties: VideoProperties | None = None


@dataclass
class VerticalVideoRange:
    min_duration: int
    max_duration: int


class TwitchClipsToYoutube:
    def __init__(
        self,
        max_videos_to_upload: int,
        twitch_data: TwitchData,
        cookies_settings: CookiesUploaderSettings,
        custom_metadata: CustomVideoMetadata | None = None,
        logger: BaseLogger | None = None,
    ) -> None:
        self.logger = logger or Logger()

        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--cookies",
            "-c",
            action="store_true",
            help="Use cookies from stdin",
            dest="use_stdin_cookies",
        )
        self.args = parser.parse_args()

        self.max_videos = max_videos_to_upload
        if not self.max_videos > 0:
            max_videos_error = "Max videos must be at least 1"
            raise ValueError(max_videos_error)

        self.cookies_folder_path = cookies_settings.cookies_folder_path
        self.retries = cookies_settings.cookies_validation_retries
        self.json_cookies_path = Path(
            f"{self.cookies_folder_path}/cookies.json",
        )
        self.cookies_path = Path(f"{self.cookies_folder_path}/cookies.txt")

        self.yt_uploader = self._get_uploader()

        self.custom_metadata = custom_metadata

        self.vertical_video_range = VerticalVideoRange(
            min_duration=3,
            max_duration=58,
        )
        max_vertical_video_duration = 58
        if (
            self.vertical_video_range.max_duration
            > max_vertical_video_duration
        ):
            vertical_video_duration_error = (
                "Max vertical video duration must be less "
                f"than {max_vertical_video_duration}"
            )
            raise ValueError(vertical_video_duration_error)

        self.clips_folder_path = twitch_data.clips_folder_path
        self._create_clips_folder(clips_folder=self.clips_folder_path)

        self.twitch_urls = twitch_data.channels_urls
        self.twitch_clips_period = twitch_data.clips_period
        self.clips_limit = twitch_data.clips_per_channel_limit
        self.unsupported_words = twitch_data.unsupported_words_for_title or []
        self.used_titles = twitch_data.used_titles or []

        self.twitch_downloader = TwitchClipsDownloader(
            twitch_urls=twitch_data.channels_urls,
            clips_folder_path=twitch_data.clips_folder_path,
            logger=self.logger,
        )

    def _create_clips_folder(self, clips_folder: Path) -> None:
        if not clips_folder.exists():
            self.logger.log("Clips folder doesn't exist. Creating new one...")
            clips_folder.mkdir(parents=True, exist_ok=True)

    def _get_cookies_uploader(
        self,
    ) -> tuple[YoutubeUploaderViaCookies | None, bool]:
        try:
            cookies_uploader = YoutubeUploaderViaCookies(
                cookies_path=self.cookies_path,
                retries=self.retries,
                logger=self.logger,
            )
            if cookies_uploader.has_valid_cookies():
                self.logger.log("Cookies-Uploader initialized.")
                return cookies_uploader, True
            self.logger.log("Invalid cookies.")
            return cookies_uploader, False
        except Exception:
            return None, False

    def _stdin_to_cookies(self) -> None:
        if self.args.use_stdin_cookies:
            try:
                StdinNetScapeFormatter(logger=self.logger).save(
                    formatted_cookies_file_path=self.cookies_path,
                    unformatted_cookies_file_path=Path(),
                )
            except ValueError as e:
                raise e
            except Exception as e:
                raise e
            return
        stdin_error = "Unable to read cookies from stdin. Use --cookies flag."
        raise RuntimeError(stdin_error)

    def _get_uploader(self) -> BaseUploader:
        if self._check_cookies_file():
            yt_uploader, is_valid = self._get_cookies_uploader()
            if yt_uploader is not None and is_valid:
                return yt_uploader
            self._stdin_to_cookies()
            yt_uploader, _ = self._get_cookies_uploader()
            if yt_uploader is not None:
                return yt_uploader
        else:
            self._stdin_to_cookies()
            yt_uploader, _ = self._get_cookies_uploader()
            if yt_uploader is not None:
                return yt_uploader
        no_cookies_error = "No valid cookies or client secret provided"
        raise ValueError(no_cookies_error)

    def _check_cookies_file(self) -> bool:
        cookies_folder = self.cookies_folder_path
        cookies_path = self.cookies_path
        json_cookies_path = self.json_cookies_path
        if not cookies_folder.exists():
            self.logger.log(
                "Cookies folder doesn't exist. Creating new one...",
            )
            cookies_folder.mkdir(parents=True, exist_ok=True)
            return False
        if not cookies_path.exists():
            if json_cookies_path.exists():
                try:
                    netscape_formatter = JSONNetScapeFormatter(
                        logger=self.logger,
                    )
                    netscape_formatter.save(
                        unformatted_cookies_file_path=json_cookies_path,
                        formatted_cookies_file_path=cookies_path,
                    )
                    return True
                except Exception:
                    pass
            self.logger.log("Cookies file doesn't exist.")
            return False
        return True

    def _filter_clips(self, clips: list[ClipInfo]) -> list[ClipInfo]:
        filtered_clips_info = (
            self.twitch_downloader.filter_clips_by_unsupported_words(
                clips_info=clips,
                unsupported_words=self.unsupported_words,
            )
        )
        filtered_clips_info = self.twitch_downloader.demojize_clips(
            clips_info=filtered_clips_info,
        )
        filtered_clips_info, _ = (
            self.twitch_downloader.filter_clips_by_used_titles(
                clips_info=filtered_clips_info,
                used_titles=self.used_titles,
            )
        )
        return filtered_clips_info

    def _download_clip(self, clip_info: ClipInfo) -> Path:
        try:
            return self.twitch_downloader.download_clip(clip_info=clip_info)
        except Exception as e:
            download_error = f"Failed to download clip: {clip_info.slug}"
            raise RuntimeError(download_error) from e

    def _generate_video_metadata(
        self,
        clip_info: ClipInfo,
        is_vertical: bool | None = None,
    ) -> tuple[str, str, list[str]]:
        title = f"{clip_info.title}"
        description = ""
        tags = [f"{clip_info.broadcaster}"]
        if self.custom_metadata is not None:
            if self.custom_metadata.streamer_tag_in_title:
                title += f" #{clip_info.broadcaster}"
            if self.custom_metadata.shorts_tag_in_title and is_vertical:
                title += r" #shorts"
            if self.custom_metadata.streamer_url_in_desc:
                description += (
                    f"Streamer: https://www.twitch.tv/{clip_info.broadcaster}"
                )
            if (
                self.custom_metadata.custom_description is not None
                and isinstance(
                    self.custom_metadata.custom_description,
                    str,
                )
            ):
                if description != "":
                    description += "\n\n"
                description += f"{self.custom_metadata.custom_description}"
            if self.custom_metadata.custom_tags is not None and isinstance(
                self.custom_metadata.custom_tags,
                list,
            ):
                tags.extend(self.custom_metadata.custom_tags)
        title = title.strip()
        description = description.strip()
        title_length_limit = 99
        if len(title) > title_length_limit:
            title_length_error = "Title length is more than 99 characters"
            raise RuntimeError(title_length_error)
        return title, description, tags

    def _convert_clip_to_vertical(
        self,
        clip_path: Path,
        clip_info: ClipInfo,
    ) -> Path:
        try:
            background_file_path = (
                VerticalVideoConverter.create_background_file(
                    output_file_path=Path(
                        f"{self.clips_folder_path}/{clip_info.id}"
                        "_background.mp4",
                    ),
                    duration=clip_info.duration_seconds,
                    framerate=clip_info.framerate,
                )
            )
            vertical_video_path = VerticalVideoConverter.create_vertical_video(
                clip_path=clip_path,
                background_path=background_file_path,
                output_path=Path(
                    f"{self.clips_folder_path}/{clip_info.id}_vertical.mp4",
                ),
            )
            for path in (background_file_path, clip_path):
                deletion_status, log_info = (
                    self.twitch_downloader.delete_clip_by_path(path=path)
                )
                if not deletion_status:
                    self.logger.log(f"{log_info}")
            return vertical_video_path
        except Exception as e:
            raise RuntimeError(e) from e

    def _publish_clip(
        self,
        clip_info: ClipInfo,
        is_vertical: bool | None = None,
    ) -> bool:
        try:
            clip_path = self._download_clip(clip_info)
            try:
                title, description, tags = self._generate_video_metadata(
                    clip_info,
                    is_vertical,
                )
            except RuntimeError as e:
                self.logger.log(f"{e}")
                self.used_titles.append(clip_info.title)
                return False
            if is_vertical:
                try:
                    clip_path = self._convert_clip_to_vertical(
                        clip_path,
                        clip_info,
                    )
                except RuntimeError as e:
                    self.logger.log(f"{e}")
                    title = title.replace(" #shorts", "")
            self.yt_uploader.upload(
                VideoInfo(
                    video_path=clip_path,
                    title=title,
                    description=description,
                    tags=tags,
                    made_for_kids=(
                        self.custom_metadata.video_properties.made_for_kids
                        if self.custom_metadata
                        and self.custom_metadata.video_properties
                        else None
                    ),
                    privacy=(
                        self.custom_metadata.video_properties.privacy
                        if self.custom_metadata
                        and self.custom_metadata.video_properties
                        else None
                    ),
                    language=(
                        self.custom_metadata.video_properties.language
                        if self.custom_metadata
                        and self.custom_metadata.video_properties
                        else None
                    ),
                    license_=(
                        self.custom_metadata.video_properties.license_
                        if self.custom_metadata
                        and self.custom_metadata.video_properties
                        else None
                    ),
                ),
            )
            self.used_titles.append(clip_info.title)
            deletion_status, log_info = (
                self.twitch_downloader.delete_clip_by_path(
                    clip_path,
                )
            )
            if not deletion_status:
                self.logger.log(log_info)
            return True
        except RuntimeError as e:
            self.logger.log("An error occurred while publishing the clip.")
            self.logger.log(f"Error details: {e}")
            raise e

    def run(self) -> None:
        all_clips_json = self.twitch_downloader.get_clips(
            period=self.twitch_clips_period,
            clips_limit=self.clips_limit,
        )
        all_clips_info = self.twitch_downloader.generate_clips_info(
            clips_json=all_clips_json,
        )
        filtered_clips = self._filter_clips(clips=all_clips_info)
        sorted_clips_info_by_views = self.twitch_downloader.sort_by_views(
            clips_info=filtered_clips,
        )
        posted_videos = 0
        for clip_info in sorted_clips_info_by_views:
            is_vertical = (
                self.vertical_video_range.min_duration
                <= clip_info.duration_seconds
                < self.vertical_video_range.max_duration
            )
            try:
                success = self._publish_clip(
                    clip_info=clip_info,
                    is_vertical=is_vertical,
                )
                if success:
                    posted_videos += 1
            except RuntimeError:
                break
            if posted_videos >= self.max_videos:
                break
        self.twitch_downloader.delete_all_clips()

    def close_session(self) -> None:
        self.yt_uploader.close_session()
