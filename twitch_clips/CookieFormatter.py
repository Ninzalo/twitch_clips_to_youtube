import datetime
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from .Logger import BaseLogger, Logger


class BaseCookieFormatter(ABC):
    """Base class for Cookie Formatter."""

    @abstractmethod
    def save(
        self,
        formatted_cookies_file_path: Path,
        unformatted_cookies_file_path: Path,
    ) -> None:
        """Format cookies to a file."""


class JSONNetScapeFormatter(BaseCookieFormatter):
    def __init__(self, logger: BaseLogger | None = None) -> None:
        self.logger = logger if logger else Logger()

    def save(
        self,
        formatted_cookies_file_path: Path,
        unformatted_cookies_file_path: Path,
    ) -> None:
        """Format JSON cookies to Netscape format and saves it to a file."""
        self.logger.log("Formatting JSON cookies to Netscape format...")
        self.logger.log("Reading JSON cookie file...")
        json_cookies_data = self._read_json_cookies_file(
            json_cookies_file_path=unformatted_cookies_file_path,
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
            f"Result saved to: {formatted_cookies_file_path}",
        )

    @staticmethod
    def _read_json_cookies_file(
        json_cookies_file_path: Path,
    ) -> List[dict]:
        if json_cookies_file_path.exists():
            with Path.open(json_cookies_file_path, encoding="utf-8") as file:
                return json.load(file)
        not_found_error = "JSON cookie file doesn't exist"
        raise ValueError(not_found_error)

    @staticmethod
    def _save_cookies_to_file(
        netscape_string: str,
        formatted_cookies_file_path: Path,
    ) -> None:
        with Path.open(
            formatted_cookies_file_path,
            "w",
            encoding="utf-8",
        ) as file:
            netscape_header_text = (
                "# Netscape HTTP Cookie File\n"
                "# http://curl.haxx.se/rfc/cookie_spec.html\n"
                "# This is a generated file!  Do not edit.\n\n"
            )

            file.write(netscape_header_text)
            file.write(netscape_string)

    @staticmethod
    def _to_netscape_string(cookie_data: List[dict]) -> str:
        result = []
        for cookie in cookie_data:
            domain = cookie.get("domain", "")
            expiration_date = cookie.get("expiry", None)
            if not expiration_date:
                expiration_date = cookie.get("expirationDate", None)
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
                ],
            )

        return "\n".join("\t".join(cookie_parts) for cookie_parts in result)


class StdinNetScapeFormatter(BaseCookieFormatter):
    def __init__(self, logger: BaseLogger | None = None) -> None:
        self.logger = logger if logger else Logger()

    def save(
        self,
        formatted_cookies_file_path: Path,
        unformatted_cookies_file_path: Path,
    ) -> None:
        self.logger.log("Reading cookies from STDIN...")
        unformatted_cookies = self._read_stdin()
        self.logger.log("Formatting cookies to Netscape format...")
        formatted_cookies = self._format_stdin_to_netscape(
            cookies=unformatted_cookies,
        )
        self.logger.log(
            f"Saving formatted cookies to {formatted_cookies_file_path}...",
        )
        self._save_cookies_to_file(
            netscape_string=formatted_cookies,
            formatted_cookies_file_path=formatted_cookies_file_path,
        )

    def _read_stdin(self) -> List[str]:
        print(
            "Input Cookie (Press Enter to finish input | Ctrl + C to cancel):",
        )
        cookies = []
        while True:
            try:
                line = input()
                if line == "":
                    break
            except EOFError:
                break
            cookies.append(str(line))
        return cookies

    @staticmethod
    def _convert_expiration(expiration: str):
        formats = ["%Y-%m-%dT%H:%M:%S.%fZ", "%d.%m.%Y, %H:%M:%S"]
        for format_ in formats:
            try:
                return int(
                    datetime.datetime.strptime(
                        expiration, format_,
                    ).timestamp(),
                )
            except Exception:
                continue
        convert_error = "Failed to convert expiration date"
        raise ValueError(convert_error)

    @classmethod
    def _format_stdin_to_netscape(cls, cookies: List[str]) -> str:
        try:
            formatted_cookies = []
            for cookie in cookies:
                cookie_parts = cookie.split("\t")
                cookie_parts_amount = 7
                if len(cookie_parts) < cookie_parts_amount:
                    continue
                name = cookie_parts[0]
                value = cookie_parts[1]
                domain = cookie_parts[2]
                path = cookie_parts[3]
                expiration = cookie_parts[4]
                http_only = cookie_parts[-1]
                if not name:
                    continue
                if domain[0] != ".":
                    domain = "." + domain
                http_only = "TRUE" if http_only == "✓" else "FALSE"
                if expiration in ("Session", "Сеанс"):
                    expiration = int(
                        (
                            datetime.datetime.now()
                            + datetime.timedelta(days=1)
                        ).timestamp(),
                    )
                else:
                    try:
                        expiration = cls._convert_expiration(
                            expiration=expiration,
                        )
                    except Exception:
                        continue

                formatted_cookie_str = "\t".join(
                    [
                        domain,
                        "TRUE",
                        path,
                        http_only,
                        str(expiration),
                        name,
                        value,
                    ],
                )
                formatted_cookies.append(formatted_cookie_str)
            return "\n".join(formatted_cookies)
        except Exception as e:
            format_error = "Failed to format stdin cookies"
            raise ValueError(format_error) from e

    @staticmethod
    def _save_cookies_to_file(
        netscape_string: str,
        formatted_cookies_file_path: Path,
    ) -> None:
        with Path.open(
            formatted_cookies_file_path,
            "w",
            encoding="utf-8",
        ) as file:
            netscape_header_text = (
                "# Netscape HTTP Cookie File\n"
                "# http://curl.haxx.se/rfc/cookie_spec.html\n"
                "# This is a generated file!  Do not edit.\n\n"
            )

            file.write(netscape_header_text)
            file.write(netscape_string)
