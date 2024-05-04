import ssl
from contextlib import _GeneratorContextManager

from seleniumbase import SB

from .Logger import BaseLogger, Logger


class Driver:
    def __init__(
        self, headless: bool = False, logger: BaseLogger | None = None
    ) -> None:
        ssl._create_default_https_context = ssl._create_unverified_context
        self.driver = SB(uc=True, xvfb=headless, headless=headless, headless2=headless)
        self.logger = logger if logger else Logger()

    def get_driver(self) -> _GeneratorContextManager:
        self.logger.log("Driver Initialized")
        return self.driver
