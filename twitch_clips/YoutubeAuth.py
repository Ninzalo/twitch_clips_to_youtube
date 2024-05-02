import os
import sys
import time
from random import randint
from typing import Any, List

import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys


class YoutubeAuth:
    def __init__(
        self,
        login: str,
        password: str,
        driver: uc.Chrome,
    ) -> None:
        self.validate_value_type(value=login, type_=str)
        self.validate_non_empty_string(string=login)
        self.login = login
        self.validate_value_type(value=password, type_=str)
        self.validate_non_empty_string(string=password)
        self.password = password
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

    def login_youtube(self) -> None:
        try:
            self._open_login_page()
            self._enter_login()
            self._enter_password()
            self._open_youtube()
        except Exception as e:
            self.driver.save_screenshot(f"{os.getcwd()}/last_yt_login_error.png")
            print(e)
            sys.exit()

    def get_cookies(self) -> List[dict]:
        yt_cookies = self.driver.get_cookies()
        return yt_cookies

    def _open_login_page(self) -> None:
        auth_url = (
            r"https://accounts.google.com/o/oauth2/v2/auth/"
            r"oauthchooseaccount?"
            r"redirect_uri=https%3A%2F%2Fdevelopers.google.com%2Foauthplayground"
            r"&prompt=consent"
            r"&response_type=code"
            r"&client_id=407408718192.apps.googleusercontent.com"
            r"&scope=email&access_type=offline&flowName=GeneralOAuthFlow"
        )
        self.driver.get(auth_url)
        time.sleep(randint(10, 20))

    def _enter_login(self) -> None:
        login_input_xpath = r'//*[@id="identifierId"]'
        login_input_el = self.driver.find_element(
            by=uc.By.XPATH, value=login_input_xpath
        )
        login_input_el.send_keys(self.login, Keys.ENTER)
        time.sleep(randint(5, 10))

    def _enter_password(self) -> None:
        password_input_xpath = r'//*[@id="password"]/div[1]/div/div[1]/input'
        password_input_el = self.driver.find_element(
            by=uc.By.XPATH, value=password_input_xpath
        )
        password_input_el.clear()
        password_input_el.send_keys(self.password, Keys.ENTER)
        time.sleep(randint(5, 10))

    def _open_youtube(self) -> None:
        self.driver.get("https://youtube.com")
        time.sleep(randint(10, 20))
