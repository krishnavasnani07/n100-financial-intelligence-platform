import logging
import sys
from src.config import settings


def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger configured with handlers for console and file logging.

    Args:
        name (str): The name of the logger (usually __name__).

    Returns:
        logging.Logger: The configured Logger instance.
    """
    logger = logging.getLogger(name)

    # Set the logging level from the central configuration
    log_level_str = settings.LOG_LEVEL
    log_level = getattr(logging, log_level_str, logging.INFO)
    logger.setLevel(log_level)

    # Avoid adding multiple handlers to the same logger if it is imported multiple times
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
        )

        # Console handler (standard output)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler
        try:
            file_handler = logging.FileHandler(settings.LOG_FILE, encoding="utf-8")
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # Write error to stdout since file logger setup failed
            console_handler.stream.write(
                f"CRITICAL: Failed to initialize file log handler at {settings.LOG_FILE}: {e}\n"
            )

    return logger
