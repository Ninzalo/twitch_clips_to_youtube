from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from netscape_cookies import save_cookies_to_file


class BaseYTCookieSaver(ABC):
    """Base class for Youtube Cookie Saver"""

    @classmethod
    @abstractmethod
    def save(cls, cookies: List[dict], filepath: str | Path) -> None:
        """Saves cookies to a file"""


class NetScapeSaver(BaseYTCookieSaver):
    @classmethod
    def save(cls, cookies: List[dict], filepath: str | Path) -> None:
        save_cookies_to_file(cookie_data=cookies, file_path=filepath)


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
