from abc import ABC, abstractmethod
from pathlib import Path
from typing import List


class BaseYTCookieSaver(ABC):
    """Base class for Youtube Cookie Saver"""

    @classmethod
    @abstractmethod
    def save(cls, cookies: List[dict], filepath: str | Path) -> None:
        """Saves cookies to a file"""


class NetScapeSaver(BaseYTCookieSaver):
    @classmethod
    def save(cls, cookies: List[dict], filepath: str | Path) -> None:
        cls._save_cookies_to_file(cookie_data=cookies, file_path=filepath)

    @classmethod
    def _save_cookies_to_file(cls, cookie_data, file_path):
        netscape_string = cls._to_netscape_string(cookie_data)
        with open(file_path, "w", encoding="utf-8") as file:
            netscape_header_text = (
                "# Netscape HTTP Cookie File\n"
                "# http://curl.haxx.se/rfc/cookie_spec.html\n"
                "# This is a generated file!  Do not edit.\n\n"
            )

            file.write(netscape_header_text)
            file.write(netscape_string)

    @classmethod
    def _to_netscape_string(cls, cookie_data):
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


class YTCookieSaver:
    def __init__(self, cookies_saver: BaseYTCookieSaver) -> None:
        self.cookies_saver = cookies_saver

    def save_cookies(self, cookies: List[dict], filepath: str | Path) -> None:
        self._validate_filepath_type(filepath=filepath)
        self._validate_non_empty_filepath(filepath=filepath)
        self.cookies_saver.save(cookies=cookies, filepath=filepath)

    @staticmethod
    def _validate_filepath_type(filepath: str | Path) -> None:
        if not isinstance(filepath, str) and not isinstance(filepath, Path):
            raise TypeError(f"Filepath must be a string, not {filepath}")

    @staticmethod
    def _validate_non_empty_filepath(filepath: str | Path) -> None:
        if not str(filepath).strip():
            raise ValueError("Filepath cannot be empty")
