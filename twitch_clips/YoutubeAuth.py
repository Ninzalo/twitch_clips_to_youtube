import time
from random import randint
from typing import Any, List

from selenium.webdriver.common.keys import Keys

from .Logger import BaseLogger, Logger


class YoutubeAuth:
    def __init__(
        self,
        login: str,
        password: str,
        driver,
        logger: BaseLogger | None = None,
    ) -> None:
        self.logger = logger if logger else Logger()

        self.logger.log(f"Validating YouTube credentials...")
        self.validate_value_type(value=login, type_=str)
        self.validate_non_empty_string(string=login)
        self.login = login

        self.validate_value_type(value=password, type_=str)
        self.validate_non_empty_string(string=password)
        self.password = password

        self.logger.log(f"Validating driver...")
        self.validate_non_null_value(value=driver)
        self.driver = driver

    @staticmethod
    def validate_value_type(value: Any, type_: Any) -> None:
        if not isinstance(value, type_):
            raise TypeError(f"Value {value} should be {type_}")

    @staticmethod
    def validate_non_empty_string(string: str) -> None:
        if not string:
            raise ValueError(f"Value of {string} should not be empty")

    @staticmethod
    def validate_non_null_value(value: Any) -> None:
        if value is None:
            raise ValueError(f"Value of {value} should not be None")

    def get_yt_cookies(self) -> List[dict]:
        self.logger.log("Authenticating Google account...")
        with self.driver as sb:
            auth_url = (
                r"https://accounts.google.com/o/oauth2/v2/auth/"
                r"oauthchooseaccount?"
                r"redirect_uri=https%3A%2F%2Fdevelopers.google.com%2Foauthplayground"
                r"&prompt=consent"
                r"&response_type=code"
                r"&client_id=407408718192.apps.googleusercontent.com"
                r"&scope=email&access_type=offline&flowName=GeneralOAuthFlow"
            )
            sb.uc_open_with_reconnect(auth_url, 3)
            time.sleep(randint(10, 20))

            self.logger.log("Entering login...")
            login_input_selector = r"#identifierId"
            sb.type(login_input_selector, self.login)
            sb.send_keys(login_input_selector, Keys.ENTER)
            time.sleep(randint(5, 10))
            self.logger.log("Login entered!")

            self.logger.log("Entering password...")
            password_input_selector = (
                r"#password > div.aCsJod.oJeWuf > div > div.Xb9hP > input"
            )
            sb.type(password_input_selector, self.password)
            sb.send_keys(password_input_selector, Keys.ENTER)
            time.sleep(randint(5, 10))
            self.logger.log("Password entered!")

            self.logger.log("Redirecting to YouTube...")
            sb.uc_open_with_reconnect("https://youtube.com", 3)
            time.sleep(randint(10, 20))

            self.logger.log("Getting cookies...")
            cookies = sb.get_cookies()
            self.logger.log("Cookies saved!")

        return cookies
