"""Logging configuration and setup."""

import logging
import sys

from app.core.config import get_settings

settings = get_settings()


def setup_logging() -> None:
    """Configure root logger and log format."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    # Clear existing handlers to prevent duplicate output
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Silence noisy third-party loggers if needed
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(name)
