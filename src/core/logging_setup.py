from __future__ import annotations

import logging
import sys
from pathlib import Path

from src.core import BASE_DIR


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("jobscout")
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    logger.addHandler(stream)

    log_dir = BASE_DIR / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "jobscout.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "jobscout") -> logging.Logger:
    root = logging.getLogger("jobscout")
    if not root.handlers:
        setup_logging()
    return logging.getLogger(name)
