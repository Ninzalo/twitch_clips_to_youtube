from abc import ABC, abstractmethod


class BaseLogger(ABC):
    @abstractmethod
    def log(self, message: str) -> None:
        """Log message

        :param message: message to be logged
        :type message: str

        :returns: None
        :rtype: None
        """


class Logger(BaseLogger):
    def __init__(self, debug_mode: bool = True) -> None:
        self.debug_mode = debug_mode

    def log(self, message: str) -> None:
        if self.debug_mode:
            print(f"[INFO] {message[:1].upper()}{message[1:]}")
