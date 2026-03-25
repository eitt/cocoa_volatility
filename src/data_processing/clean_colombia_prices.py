"""Cleaning helpers for Colombian domestic price series."""

from __future__ import annotations

import pandas as pd

from src.utils.validation_utils import ensure_numeric_series


def clean_colombia_price_columns(dataframe: pd.DataFrame, column_map: dict[str, str]) -> pd.DataFrame:
    """Rename Colombian price columns using an explicit mapping."""
    return dataframe.rename(columns=column_map).copy()


def normalize_colombia_units(
    dataframe: pd.DataFrame,
    value_column: str = "price",
    unit_column: str = "unit",
) -> pd.DataFrame:
    """Normalize common Colombia price units to lowercase labels."""
    cleaned = dataframe.copy()
    if unit_column in cleaned.columns:
        cleaned[unit_column] = cleaned[unit_column].astype(str).str.strip().str.lower()
    if value_column in cleaned.columns:
        cleaned[value_column] = ensure_numeric_series(cleaned[value_column])
    return cleaned

