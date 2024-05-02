import ssl

import undetected_chromedriver as uc


class Driver:
    def __init__(self, headless: bool = False, use_subprocess: bool = True) -> None:
        ssl._create_default_https_context = ssl._create_unverified_context
        self.driver = uc.Chrome(headless=headless, use_subprocess=use_subprocess)

    def get_driver(self) -> uc.Chrome:
        return self.driver

    def close(self) -> None:
        self.driver.close()
        self.driver.quit()
