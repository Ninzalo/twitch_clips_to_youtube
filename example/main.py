import json
from pathlib import Path

from twitch_clips import (
    BaseLanguageEnum,
    BaseLicenseEnum,
    BasePrivacyEnum,
    CookiesUploaderSettings,
    CustomVideoMetadata,
    Logger,
    PeriodEnum,
    TwitchClipsToYoutube,
    TwitchData,
    VideoProperties,
)

MAX_VIDEOS = 1

DEBUG_MODE = True

COOKIES_VALIDATION_RETRIES = 5

COOKIES_FOLDER_PATH = Path(f"{Path.cwd()}/cookies/")

CLIPS_FOLDER_PATH = Path(f"{Path.cwd()}/clips/")

CLIPS_PER_TWITCH_CHANNEL_LIMIT = None

TWITCH_CLIPS_PERIOD = PeriodEnum.LAST_DAY

CUSTOM_TAGS = []

CUSTOM_DESCRIPTION = ""

CUSTOM_LICENSE = BaseLicenseEnum.STANDARD

CUSTOM_LANGUAGE = BaseLanguageEnum.RUSSIAN

CUSTOM_PRIVACY = BasePrivacyEnum.PUBLIC

IS_MADE_FOR_KIDS = False

STREAMER_URL_IN_DESC = True

STREAMER_TAG_IN_TITLE = True

SHORTS_TAG_IN_TITLE = True

CONFIGS_FOLDER_PATH = Path(f"{Path.cwd()}/configs/")

TWICH_URLS_PATH = Path(f"{CONFIGS_FOLDER_PATH}/twitch_urls.json")

USED_TITLES_PATH = Path(f"{CONFIGS_FOLDER_PATH}/used_titles.json")

UNSUPPORTED_WORDS_PATH = Path(f"{CONFIGS_FOLDER_PATH}/unsupported_words.json")


if __name__ == "__main__":
    if not CONFIGS_FOLDER_PATH.exists():
        Path(CONFIGS_FOLDER_PATH).mkdir(parents=True, exist_ok=True)
    if not TWICH_URLS_PATH.exists():
        with Path.open(
            TWICH_URLS_PATH, "w", encoding="utf-8",
        ) as twitch_urls_file:
            json.dump([], twitch_urls_file, ensure_ascii=False, indent=4)
    with Path.open(TWICH_URLS_PATH, encoding="utf-8") as twitch_urls_file:
        TWICH_URLS = json.load(twitch_urls_file)
    if not USED_TITLES_PATH.exists():
        with Path.open(
            USED_TITLES_PATH, "w", encoding="utf-8",
        ) as used_titles_file:
            json.dump([], used_titles_file, ensure_ascii=False, indent=4)
    with Path.open(USED_TITLES_PATH, encoding="utf-8") as file:
        USED_TITLES = json.load(file)
    if not UNSUPPORTED_WORDS_PATH.exists():
        with Path.open(
            UNSUPPORTED_WORDS_PATH, "w", encoding="utf-8",
        ) as u_w_file:
            json.dump([], u_w_file, ensure_ascii=False, indent=4)
    with Path.open(UNSUPPORTED_WORDS_PATH, encoding="utf-8") as file:
        UNSUPPORTED_WORDS = json.load(file)
    custom_metadata = CustomVideoMetadata(
        custom_description=CUSTOM_DESCRIPTION,
        custom_tags=CUSTOM_TAGS,
        streamer_url_in_desc=STREAMER_URL_IN_DESC,
        streamer_tag_in_title=STREAMER_TAG_IN_TITLE,
        shorts_tag_in_title=SHORTS_TAG_IN_TITLE,
        video_properties=VideoProperties(
            license_=CUSTOM_LICENSE,
            language=CUSTOM_LANGUAGE,
            privacy=CUSTOM_PRIVACY,
            made_for_kids=IS_MADE_FOR_KIDS,
        ),
    )
    logger = Logger(debug_mode=DEBUG_MODE)

    uploader = TwitchClipsToYoutube(
        max_videos_to_upload=MAX_VIDEOS,
        twitch_data=TwitchData(
            channels_urls=TWICH_URLS,
            clips_folder_path=CLIPS_FOLDER_PATH,
            clips_period=TWITCH_CLIPS_PERIOD,
            clips_per_channel_limit=CLIPS_PER_TWITCH_CHANNEL_LIMIT,
            unsupported_words_for_title=UNSUPPORTED_WORDS,
            used_titles=USED_TITLES,
        ),
        custom_metadata=custom_metadata,
        cookies_settings=CookiesUploaderSettings(
            cookies_folder_path=COOKIES_FOLDER_PATH,
            cookies_validation_retries=COOKIES_VALIDATION_RETRIES,
        ),
        logger=logger,
    )
    uploader.run()
    uploader.close_session()

    with Path.open(USED_TITLES_PATH, "w", encoding="utf-8") as file:
        json.dump(uploader.used_titles, file, ensure_ascii=False, indent=4)
