import logging
import os
from datetime import date

PACKAGE_LOGGER = "pixBoards"


def setup_logging(logs_dir="logs"):
    """Attach file + console handlers to the package logger, once.

    Module loggers (``logging.getLogger(__name__)``) propagate to it, so every
    message is written exactly once. Logs go to ``logs/`` in the current
    working directory, not inside the installed package.
    """
    logger = logging.getLogger(PACKAGE_LOGGER)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    os.makedirs(logs_dir, exist_ok=True)
    log_file_path = os.path.join(logs_dir, f"{date.today().isoformat()}.log")

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    file_handler = logging.FileHandler(log_file_path, encoding="utf-8", mode="a")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
