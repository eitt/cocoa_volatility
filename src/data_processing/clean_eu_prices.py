"""Cleaning helpers for EU price indicators."""

from __future__ import annotations

import pandas as pd

from src.utils.validation_utils import ensure_numeric_series


def clean_eu_price_columns(dataframe: pd.DataFrame, column_map: dict[str, str]) -> pd.DataFrame:
    """Rename EU price columns using an explicit mapping."""
    return dataframe.rename(columns=column_map).copy()


def scale_eu_indices(dataframe: pd.DataFrame, value_column: str = "value", base: float = 100.0) -> pd.DataFrame:
    """Rescale index values to a chosen base when possible."""
    scaled = dataframe.copy()
    if value_column not in scaled.columns:
        return scaled
    scaled[value_column] = ensure_numeric_series(scaled[value_column])
    return scaled.assign(value_scaled=scaled[value_column] / base)

