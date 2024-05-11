import json
import os
from pathlib import Path

from twitch_clips import (
    CookiesUploaderSettings,
    CustomVideoMetadata,
    Logger,
    PeriodEnum,
    TwitchClipsToYoutube,
    TwitchData,
)

MAX_VIDEOS = 1

DEBUG_MODE = True

COOKIES_VALIDATION_RETRIES = 5

COOKIES_FOLDER_PATH = Path(f"{os.getcwd()}/cookies/")

CLIPS_FOLDER_PATH = Path(f"{os.getcwd()}/clips/")

CLIPS_PER_TWITCH_CHANNEL_LIMIT = None

TWITCH_CLIPS_PERIOD = PeriodEnum.LAST_DAY

CUSTOM_TAGS = []

CUSTOM_DESCRIPTION = ""

CONFIGS_FOLDER_PATH = Path(f"{os.getcwd()}/configs/")

TWICH_URLS_PATH = Path(f"{CONFIGS_FOLDER_PATH}/twitch_urls.json")

USED_TITLES_PATH = Path(f"{CONFIGS_FOLDER_PATH}/used_titles.json")

UNSUPPORTED_WORDS_PATH = Path(f"{CONFIGS_FOLDER_PATH}/unsupported_words.json")


if not CONFIGS_FOLDER_PATH.exists():
    Path(CONFIGS_FOLDER_PATH).mkdir(parents=True, exist_ok=True)
if not TWICH_URLS_PATH.exists():
    with open(TWICH_URLS_PATH, "w", encoding="utf-8") as twitch_urls_file:
        json.dump([], twitch_urls_file, ensure_ascii=False, indent=4)
with open(TWICH_URLS_PATH, "r", encoding="utf-8") as twitch_urls_file:
    TWICH_URLS = json.load(twitch_urls_file)
if not USED_TITLES_PATH.exists():
    with open(USED_TITLES_PATH, "w", encoding="utf-8") as used_titles_file:
        json.dump([], used_titles_file, ensure_ascii=False, indent=4)
with open(USED_TITLES_PATH, "r", encoding="utf-8") as file:
    USED_TITLES = json.load(file)
if not UNSUPPORTED_WORDS_PATH.exists():
    with open(UNSUPPORTED_WORDS_PATH, "w", encoding="utf-8") as u_w_file:
        json.dump([], u_w_file, ensure_ascii=False, indent=4)
with open(UNSUPPORTED_WORDS_PATH, "r", encoding="utf-8") as file:
    UNSUPPORTED_WORDS = json.load(file)
custom_metadata = CustomVideoMetadata(
    custom_description=CUSTOM_DESCRIPTION,
    custom_tags=CUSTOM_TAGS,
)
logger = Logger(debug_mode=DEBUG_MODE)

if __name__ == "__main__":
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

    with open(USED_TITLES_PATH, "w", encoding="utf-8") as file:
        json.dump(uploader.used_titles, file, ensure_ascii=False, indent=4)
