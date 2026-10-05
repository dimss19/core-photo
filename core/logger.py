"""Logging infrastructure for Core Photo application.
Follows security rules: No secrets logged, rotating file handlers,
and human-readable formatting.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_initialized = False


def setup_logging(
    log_dir: Optional[Path] = None,
    level: str = "INFO",
    max_mb: int = 10,
    backup_count: int = 5
) -> Path:
    """Configures root logger with console and rotating file handler.
    Returns path to the log file.
    """
    global _initialized
    if _initialized:
        # Return existing log file path if already setup
        if log_dir is None:
            log_dir = Path("CorePhotoData") / "Logs"
        return Path(log_dir) / "corephoto.log"

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Avoid duplicate handlers
    root_logger.handlers.clear()

    formatter = logging.Formatter(DEFAULT_LOG_FORMAT, datefmt=DATE_FORMAT)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File Handler
    if log_dir is None:
        log_dir = Path("CorePhotoData") / "Logs"
    else:
        log_dir = Path(log_dir)

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "corephoto.log"

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_mb * 1024 * 1024,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    _initialized = True
    logging.info("Logging initialized. Writing logs to %s", log_file)
    return log_file


def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a named logger."""
    return logging.getLogger(name)
