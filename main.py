import json
import os
from pathlib import Path

from dotenv import load_dotenv

from twitch_clips import Logger, NetScapeSaver, PeriodEnum, TwitchClipsToYoutubeVideos

load_dotenv()

YOUTUBE_LOGIN = str(os.getenv("YOUTUBE_LOGIN"))
YOUTUBE_PASSWORD = str(os.getenv("YOUTUBE_PASSWORD"))

COOKIES_FOLDER_PATH = str(Path(f"{os.getcwd()}/cookies"))

CLIPS_FOLDER_PATH = f"{os.getcwd()}/clips/"

MAX_VIDEOS = 3

CLIPS_PER_TWITCH_CHANNEL_LIMIT = 3

TWITCH_CLIPS_PERIOD = PeriodEnum.LAST_DAY

CONFIGS_FOLDER_PATH = Path(f"{os.getcwd()}/configs")
if not CONFIGS_FOLDER_PATH.exists():
    Path(CONFIGS_FOLDER_PATH).mkdir(parents=True, exist_ok=True)


TWICH_URLS_PATH = Path(f"{CONFIGS_FOLDER_PATH}/twitch_urls.json")

USED_TITLES_PATH = Path(f"{CONFIGS_FOLDER_PATH}/used_titles.json")
UNSUPPORTED_WORDS_PATH = Path(f"{CONFIGS_FOLDER_PATH}/unsupported_words.json")


logger = Logger(debug_mode=True)
cookies_saver = NetScapeSaver()

if __name__ == "__main__":
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

    uploader = TwitchClipsToYoutubeVideos(
        youtube_login=YOUTUBE_LOGIN,
        youtube_password=YOUTUBE_PASSWORD,
        cookies_folder_path=COOKIES_FOLDER_PATH,
        twitch_channels_urls=TWICH_URLS,
        clips_folder_path=CLIPS_FOLDER_PATH,
        max_videos_to_upload=MAX_VIDEOS,
        twitch_clips_period=TWITCH_CLIPS_PERIOD,
        clips_per_twitch_channel_limit=CLIPS_PER_TWITCH_CHANNEL_LIMIT,
        unsupported_words_for_title=UNSUPPORTED_WORDS,
        used_titles=USED_TITLES,
        cookies_saver=cookies_saver,
        logger=logger,
    )
    uploader.run()

    with open(USED_TITLES_PATH, "w", encoding="utf-8") as file:
        json.dump(uploader.used_titles, file, ensure_ascii=False, indent=4)
