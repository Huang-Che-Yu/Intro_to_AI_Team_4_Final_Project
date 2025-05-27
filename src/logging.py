import os
import logging
from colorama import Fore, Style


class Logger:
    def __init__(self, level=logging.INFO):
        self.logger = logging.getLogger("assistant")
        self.logger.setLevel(logging.DEBUG)
        # Stream handler
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level)
        self.logger.addHandler(stream_handler)
        # File handler
        log_filename = os.getenv(
            "ASSISTANT_LOG", f"{os.path.expanduser('~')}/.assistant.log"
        )
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        self.logger.addHandler(file_handler)

    def debug(self, message: str):
        self.logger.debug(message)

    def info(self, message: str):
        self.logger.info(f"{Fore.BLUE}{message}{Style.RESET_ALL}")

    def warning(self, message: str):
        self.logger.warning(f"{Fore.YELLOW}{message}{Style.RESET_ALL}")

    def error(self, message: str):
        self.logger.error(f"{Fore.RED}{message}{Style.RESET_ALL}")

    def critical(self, message: str):
        self.logger.critical(f"{Fore.RED}{message}{Style.RESET_ALL}")


logger = Logger()


def get_logger():
    return logger
