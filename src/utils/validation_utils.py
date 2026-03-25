"""Validation helpers for small functional modules."""

from __future__ import annotations

import pandas as pd


def require_columns(dataframe: pd.DataFrame, required_columns: list[str]) -> None:
    """Raise an error when required columns are missing."""
    missing = [column for column in required_columns if column not in dataframe.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def validate_non_empty_frame(dataframe: pd.DataFrame, context: str) -> None:
    """Raise an error when a dataframe is empty."""
    if dataframe.empty:
        raise ValueError(f"{context} produced an empty dataframe.")


def drop_missing_required(dataframe: pd.DataFrame, required_columns: list[str]) -> pd.DataFrame:
    """Drop rows that are missing required values."""
    require_columns(dataframe, required_columns)
    return dataframe.dropna(subset=required_columns).copy()


def ensure_numeric_series(series: pd.Series) -> pd.Series:
    """Coerce a Series to numeric values."""
    return pd.to_numeric(series, errors="coerce")
