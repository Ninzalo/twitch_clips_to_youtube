import ssl

from seleniumbase import SB


class Driver:
    def __init__(self, headless: bool = False) -> None:
        ssl._create_default_https_context = ssl._create_unverified_context
        self.driver = SB(uc=True, xvfb=headless, headless=headless, headless2=headless)

    def get_driver(self):
        return self.driver
