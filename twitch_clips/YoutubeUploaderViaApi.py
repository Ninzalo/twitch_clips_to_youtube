from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import httplib2
import pytz
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow

from .BaseYoutubeUploader import BasePrivacyEnum, BaseUploader
from .Logger import BaseLogger, Logger


@dataclass
class ApiUploaderSettings:
    client_secret_folder_path: str


class YoutubeUploaderViaApi(BaseUploader):
    def __init__(
        self,
        client_secret: str,
        logger: BaseLogger | None = None,
    ) -> None:
        self.client_secret = client_secret
        self.logger = logger if logger else Logger()

    @staticmethod
    def getScheduleDateTime(days: int = 0):
        # Set the publish time to 2 PM Eastern Time (US) on the next day
        eastern_tz = pytz.timezone("America/Los_Angeles")
        publish_time = datetime.now(eastern_tz)
        if days > 0:
            publish_time = datetime.now(eastern_tz) + timedelta(days)
        publish_time = publish_time.replace(hour=14, minute=0, second=0, microsecond=0)

        # Set the publish time in the UTC timezone
        publish_time_utc = publish_time.astimezone(pytz.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        return publish_time_utc

    # Start the OAuth flow to retrieve credentials
    def authorize_credentials(self):
        scope = "https://www.googleapis.com/auth/youtube"
        storage = Storage("credentials.storage")
        # Fetch credentials from storage
        credentials = storage.get()
        # If the credentials doesn't exist in the storage location then run the flow
        if credentials is None or credentials.invalid:
            flow = flow_from_clientsecrets(self.client_secret, scope=scope)
            http = httplib2.Http()
            credentials = run_flow(flow, storage, http=http)
        return credentials

    def getYoutubeService(self):
        credentials = self.authorize_credentials()
        http = credentials.authorize(httplib2.Http())
        discovery_url = "https://www.googleapis.com/discovery/v1/apis/youtube/v3/rest"
        service = discovery.build(
            "youtube", "v3", http=http, discoveryServiceUrl=discovery_url
        )
        return service

    def upload(
        self,
        video_path: str | Path,
        title: str,
        description: str | None = None,
        tags: List[str] | None = None,
        privacy: BasePrivacyEnum | None = None,
    ):
        day = 0
        if description is None:
            description = ""
        if tags is None:
            tags = []
        if privacy is None:
            privacy = BasePrivacyEnum.PUBLIC

        self.logger.log("Uploading...")
        youtube = self.getYoutubeService()
        try:
            # Define the video resource object
            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags,
                },
                "status": {"privacyStatus": privacy},
            }
            if privacy == "private":
                body["status"]["publishAt"] = self.getScheduleDateTime(day)
            # Define the media file object
            media_file = MediaFileUpload(video_path)
            # Call the API's videos.insert method to upload the video
            videos = youtube.videos()
            response = videos.insert(
                part="snippet,status", body=body, media_body=media_file
            ).execute()
            # Print the response after the video has been uploaded
            self.logger.log("Video uploaded successfully!")
            self.logger.log(f'Title: {response["snippet"]["title"]}')
            self.logger.log(f'URL: https://www.youtube.com/watch?v={response["id"]}')

        except HttpError as e:
            raise Exception(
                f"An HTTP error {e.resp.status} occurred: {e.content.decode('utf-8')}"
            )
