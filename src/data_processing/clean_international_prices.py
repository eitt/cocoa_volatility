"""Cleaning helpers for international cocoa price series."""

from __future__ import annotations

import pandas as pd

from src.utils.validation_utils import ensure_numeric_series


def clean_international_price_columns(dataframe: pd.DataFrame, column_map: dict[str, str]) -> pd.DataFrame:
    """Rename international price columns using an explicit mapping."""
    return dataframe.rename(columns=column_map).copy()


def standardize_world_currency(
    dataframe: pd.DataFrame,
    value_column: str = "price",
    currency_column: str = "currency",
) -> pd.DataFrame:
    """Standardize numeric values and uppercase currency labels."""
    cleaned = dataframe.copy()
    if value_column in cleaned.columns:
        cleaned[value_column] = ensure_numeric_series(cleaned[value_column])
    if currency_column in cleaned.columns:
        cleaned[currency_column] = cleaned[currency_column].astype(str).str.upper()
    return cleaned

