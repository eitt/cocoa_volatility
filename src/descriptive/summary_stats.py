"""Descriptive statistics helpers."""

from __future__ import annotations

import pandas as pd


def compute_summary_statistics(dataframe: pd.DataFrame, value_columns: list[str]) -> pd.DataFrame:
    """Return count, mean, dispersion, and quantiles for selected columns."""
    available = [column for column in value_columns if column in dataframe.columns]
    if not available:
        return pd.DataFrame()
    return dataframe[available].describe().transpose().reset_index(names="variable")

