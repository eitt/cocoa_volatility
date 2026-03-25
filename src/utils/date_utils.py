"""Date handling helpers for time-series data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def coerce_datetime_series(series: pd.Series) -> pd.Series:
    """Convert a pandas Series to timezone-naive datetimes."""
    return pd.to_datetime(series, errors="coerce").dt.tz_localize(None)


def convert_to_month_start(series: pd.Series) -> pd.Series:
    """Map dates to month-start timestamps."""
    return coerce_datetime_series(series).dt.to_period("M").dt.to_timestamp()


def filter_date_range(
    dataframe: pd.DataFrame,
    date_column: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """Filter observations to an inclusive date window."""
    filtered = dataframe.copy()
    filtered[date_column] = coerce_datetime_series(filtered[date_column])

    if start_date:
        filtered = filtered.loc[filtered[date_column] >= pd.Timestamp(start_date)]
    if end_date:
        filtered = filtered.loc[filtered[date_column] <= pd.Timestamp(end_date)]

    return filtered


def infer_stem_from_path(path: str | Path) -> str:
    """Return the stem of a path for labeling outputs."""
    return Path(path).stem

