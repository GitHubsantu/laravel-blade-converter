"""
Centralized logging configuration for the Laravel Blade Converter.

All modules obtain their logger via ``get_logger(__name__)`` so that
output is consistently formatted and can be routed to both a rotating
log file and the in-app Output Console widget.
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

_LOG_DIR = Path.home() / ".laravel_blade_converter" / "logs"
_LOG_FILE = _LOG_DIR / "app.log"

_CONFIGURED = False


class QtLogBridge(logging.Handler):
    """
    A logging.Handler that forwards records to a callback so the GUI
    (Output Console) can render log messages in real time.
    """

    def __init__(self, callback):
        super().__init__()
        self._callback = callback
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
            self._callback(record.levelname, message)
        except Exception:
            # Logging must never crash the application.
            pass


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging once (idempotent)."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger("blade_converter")
    root.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-28s | %(message)s",
        datefmt="%H:%M:%S",
    )

    file_handler = logging.handlers.RotatingFileHandler(
        _LOG_FILE, maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)
    root.addHandler(stream_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(f"blade_converter.{name}")


def attach_gui_handler(callback, level: int = logging.INFO) -> QtLogBridge:
    """Attach a handler that streams log records into the GUI console."""
    configure_logging()
    handler = QtLogBridge(callback)
    handler.setLevel(level)
    logging.getLogger("blade_converter").addHandler(handler)
    return handler
