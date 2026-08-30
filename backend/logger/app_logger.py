"""Structured console and rotating file logger for BIS-SpecAI backend."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from backend.config.settings import app_settings

LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class ColoredFormatter(logging.Formatter):
    """Terminal formatter applying ANSI color codes based on log level."""

    COLORS: dict[int, str] = {
        logging.DEBUG: "\033[36m",     # Cyan
        logging.INFO: "\033[32m",      # Green
        logging.WARNING: "\033[33m",   # Yellow
        logging.ERROR: "\033[31m",     # Red
        logging.CRITICAL: "\033[35m",  # Magenta
    }
    RESET: str = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with color highlights for level badges."""
        color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{color}{record.levelname:<7}{self.RESET}"
        return super().format(record)


def setup_logging() -> None:
    """Initialize handlers for console output and rotating file storage."""
    log_dir = Path(app_settings.logging.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = Path(app_settings.logging.log_file)

    root = logging.getLogger()
    level_name = os.getenv("LOG_LEVEL", app_settings.logging.level).upper()
    log_level = getattr(logging, level_name, logging.INFO)
    root.setLevel(log_level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    if not any(isinstance(h, RotatingFileHandler) for h in root.handlers):
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=app_settings.logging.rotation_max_bytes,
            backupCount=app_settings.logging.backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        file_handler.setLevel(log_level)
        root.addHandler(file_handler)

    if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler) for h in root.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ColoredFormatter(LOG_FORMAT, DATE_FORMAT))
        console_handler.setLevel(log_level)
        root.addHandler(console_handler)


def get_logger(name: str | None = None) -> logging.Logger:
    """Get or configure a named logger instance."""
    setup_logging()
    return logging.getLogger(name or "bis_specai")
