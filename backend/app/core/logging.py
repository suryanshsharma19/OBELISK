"""
Logging configuration for OBELISK - Supply Chain Attack Detector.

Provides centralized logging with console (colored) and rotating file
handlers.  Log level is driven by the application's ``debug`` setting.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

try:
    import colorlog

    _HAS_COLORLOG = True
except ImportError:
    _HAS_COLORLOG = False

from app.config import get_settings

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

JSON_FORMAT = (
    '{"timestamp":"%(asctime)s","level":"%(levelname)s",'
    '"logger":"%(name)s","message":"%(message)s"}'
)

COLOR_FORMAT = (
    "%(log_color)s%(asctime)s | %(levelname)-8s%(reset)s | "
    "%(cyan)s%(name)s%(reset)s | %(message)s"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_console_handler(debug: bool) -> logging.Handler:
    """Return a stderr handler — colored in dev, JSON in prod."""
    handler = logging.StreamHandler(sys.stderr)

    if debug and _HAS_COLORLOG:
        formatter = colorlog.ColoredFormatter(
            COLOR_FORMAT,
            datefmt=DATE_FORMAT,
            log_colors={
                "DEBUG": "white",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
    elif debug:
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    else:
        # Production: JSON lines for easy ingestion
        formatter = logging.Formatter(JSON_FORMAT, datefmt=DATE_FORMAT)

    handler.setFormatter(formatter)
    return handler


def _get_file_handler() -> logging.Handler:
    """Return a rotating file handler (10 MB × 5 backups)."""
    handler = RotatingFileHandler(
        LOG_DIR / "obelisk.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    return handler


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def setup_logger(name: str) -> logging.Logger:
    """Create and return a fully configured logger.

    Parameters
    ----------
    name:
        Dotted logger name (typically ``__name__``).

    Returns
    -------
    logging.Logger
        Logger instance with console and file handlers attached.
    """
    settings = get_settings()
    level = logging.DEBUG if settings.debug else logging.INFO

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers when called more than once for the same name
    if not logger.handlers:
        console = _get_console_handler(settings.debug)
        console.setLevel(level)
        logger.addHandler(console)

        file_handler = _get_file_handler()
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

    # Don't propagate to the root logger
    logger.propagate = False

    return logger
