import logging
import os

from colorama import Fore, Style

COLORS = {
    logging.DEBUG: Fore.LIGHTBLACK_EX,
    logging.INFO: Fore.BLUE,
    logging.WARNING: Fore.YELLOW,
    logging.ERROR: Fore.RED,
    logging.CRITICAL: Fore.RED,
}


class StreamFormatter(logging.Formatter):
    """Logging Formatter to add colors"""

    def format(self, record: logging.LogRecord) -> str:
        level = record.levelno
        fmt = f"{COLORS[level]}{record.msg}{Style.RESET_ALL}"
        return fmt


class FileFormatter(logging.Formatter):
    """Logging Formatter to add colors"""

    BASE_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: COLORS[logging.DEBUG] + BASE_FORMAT + Style.RESET_ALL,
        logging.INFO: COLORS[logging.INFO] + BASE_FORMAT + Style.RESET_ALL,
        logging.WARNING: COLORS[logging.WARNING] + BASE_FORMAT + Style.RESET_ALL,
        logging.ERROR: COLORS[logging.ERROR] + BASE_FORMAT + Style.RESET_ALL,
        logging.CRITICAL: COLORS[logging.CRITICAL] + BASE_FORMAT + Style.RESET_ALL,
    }

    def format(self, record: logging.LogRecord) -> str:
        level = record.levelno
        fmt = self.FORMATS.get(level, self.BASE_FORMAT)
        formatter = logging.Formatter(fmt)
        return formatter.format(record)


class LoggerManager:
    """
    LoggerManager is a singleton class that provides a configured logger instance.
    The logger is configured with both a stream handler and a file handler.
    The stream handler outputs logs to the console with colored formatting.
    The file handler outputs logs to a file with colored formatting.
    The logger will be configured only once and the same instance
        will be returned on subsequent calls.
    """

    logger: logging.Logger | None = None

    @classmethod
    def get_logger(cls, level: int = logging.INFO) -> logging.Logger:
        """Get the logger instance

        Args:
            level (int, optional): The logging level. Defaults to logging.DEBUG.

        Returns:
            logging.Logger: The logger instance
        """

        if cls.logger is None:
            cls.logger = logging.getLogger("assistant")
            cls.logger.setLevel(logging.DEBUG)

            # Stream handler
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(level)
            stream_handler.setFormatter(StreamFormatter())
            cls.logger.addHandler(stream_handler)

            # File handler
            log_filename = os.getenv(
                "ASSISTANT_LOG", f"{os.path.expanduser('~')}/.assistant.log"
            )
            file_handler = logging.FileHandler(log_filename)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(FileFormatter())
            cls.logger.addHandler(file_handler)

        return cls.logger
