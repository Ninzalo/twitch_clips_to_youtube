import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from .Logger import BaseLogger, Logger


class BaseCookieFormatter(ABC):
    """Base class for JSON Cookie Formatter"""

    @abstractmethod
    def save(
        self,
        json_cookies_file_path: str | Path,
        formatted_cookies_file_path: str | Path,
    ) -> None:
        """Formats json cookies to a file"""


class NetScapeFormatter(BaseCookieFormatter):
    def __init__(self, logger: BaseLogger | None = None) -> None:
        self.logger = logger if logger else Logger()

    def save(
        self,
        json_cookies_file_path: str | Path,
        formatted_cookies_file_path: str | Path,
    ) -> None:
        self.logger.log("Formatting JSON cookies to Netscape format...")
        self.logger.log("Reading JSON cookie file...")
        json_cookies_data = self._read_json_cookies_file(
            json_cookies_file_path=json_cookies_file_path
        )
        self.logger.log("Formatting extracted cookies to Netscape format...")
        netscape_string = self._to_netscape_string(
            cookie_data=json_cookies_data,
        )
        self.logger.log("Saving formatted cookies to Netscape format...")
        self._save_cookies_to_file(
            netscape_string=netscape_string,
            formatted_cookies_file_path=formatted_cookies_file_path,
        )
        self.logger.log(
            "Finished formatting JSON cookies to Netscape format! "
            f"Result saved to: {formatted_cookies_file_path}"
        )

    @staticmethod
    def _read_json_cookies_file(
        json_cookies_file_path: str | Path,
    ) -> List[dict]:
        if Path(json_cookies_file_path).exists():
            with open(json_cookies_file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        raise ValueError("JSON cookie file doesn't exist")

    @classmethod
    def _save_cookies_to_file(
        cls, netscape_string: str, formatted_cookies_file_path: str | Path
    ) -> None:
        with open(formatted_cookies_file_path, "w", encoding="utf-8") as file:
            netscape_header_text = (
                "# Netscape HTTP Cookie File\n"
                "# http://curl.haxx.se/rfc/cookie_spec.html\n"
                "# This is a generated file!  Do not edit.\n\n"
            )

            file.write(netscape_header_text)
            file.write(netscape_string)

    @classmethod
    def _to_netscape_string(cls, cookie_data: List[dict]) -> str:
        result = []
        for cookie in cookie_data:
            domain = cookie.get("domain", "")
            expiration_date = cookie.get("expiry", None)
            path = cookie.get("path", "")
            secure = cookie.get("secure", False)
            name = cookie.get("name", "")
            value = cookie.get("value", "")

            include_sub_domain = domain.startswith(".") if domain else False
            expiry = str(int(expiration_date)) if expiration_date else "0"

            result.append(
                [
                    domain,
                    str(include_sub_domain).upper(),
                    path,
                    str(secure).upper(),
                    expiry,
                    name,
                    value,
                ]
            )

        return "\n".join("\t".join(cookie_parts) for cookie_parts in result)
