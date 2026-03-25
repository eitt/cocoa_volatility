"""Logging helpers for script entry points."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.utils.file_utils import ensure_directory


def get_project_logger(name: str, log_dir: str | Path) -> logging.Logger:
    """Create or reuse a file-backed logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    ensure_directory(log_dir)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(Path(log_dir) / f"{name}.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    return logger


def log_dataframe_shape(logger: logging.Logger, label: str, dataframe: pd.DataFrame) -> None:
    """Log the row and column count of a dataframe."""
    logger.info("%s shape: rows=%s columns=%s", label, len(dataframe), len(dataframe.columns))

