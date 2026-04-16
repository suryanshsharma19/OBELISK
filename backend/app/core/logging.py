"""Logging setup — console + rotating file handler."""

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
from app.core.request_context import get_request_id

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | req=%(request_id)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

JSON_FORMAT = (
    '{"timestamp":"%(asctime)s","level":"%(levelname)s",'
    '"logger":"%(name)s","request_id":"%(request_id)s",'
    '"message":"%(message)s"}'
)

COLOR_FORMAT = (
    "%(log_color)s%(asctime)s | %(levelname)-8s%(reset)s | "
    "%(cyan)s%(name)s%(reset)s | req=%(request_id)s | %(message)s"
)


class RequestContextFilter(logging.Filter):
    """Inject request_id from context vars so every log line is traceable."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


def _get_console_handler(debug: bool) -> logging.Handler:
    handler = logging.StreamHandler(sys.stderr)
    handler.addFilter(RequestContextFilter())

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
        formatter = logging.Formatter(JSON_FORMAT, datefmt=DATE_FORMAT)

    handler.setFormatter(formatter)
    return handler


def _get_file_handler() -> logging.Handler:
    handler = RotatingFileHandler(
        LOG_DIR / "obelisk.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    handler.addFilter(RequestContextFilter())
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    return handler


def setup_logger(name: str) -> logging.Logger:
    settings = get_settings()
    level = logging.DEBUG if settings.debug else logging.INFO

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        console = _get_console_handler(settings.debug)
        console.setLevel(level)
        logger.addHandler(console)

        file_handler = _get_file_handler()
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger
