"""CyberGuard-ID — Logging Configuration.

Structured logging dengan correlation/analysis ID.
Jangan log: API key, username asli, raw sensitive text, secrets.
"""

import logging
import sys
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    log_dir: str = "artifacts/logs",
    log_level: str = "INFO",
    log_file: str = "app.log",
) -> None:
    """Configure structured logging to file and console.

    Args:
        log_dir: Directory for log files.
        log_level: Logging level string.
        log_file: Name of the log file.
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, log_level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # File handler — detailed
    file_handler = logging.FileHandler(log_path / log_file, encoding="utf-8", mode="a")
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    root_logger.addHandler(file_handler)

    # Console handler — less verbose
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(max(level, logging.INFO))
    console_handler.setFormatter(logging.Formatter("%(levelname)-8s | %(name)-20s | %(message)s"))
    root_logger.addHandler(console_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger for a module.

    Args:
        name: Module or component name.

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(f"cyberguard.{name}")
