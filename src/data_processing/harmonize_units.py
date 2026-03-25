"""Unit and currency harmonization helpers."""

from __future__ import annotations

import pandas as pd

from src.utils.validation_utils import ensure_numeric_series


def harmonize_mass_units(
    dataframe: pd.DataFrame,
    value_column: str,
    unit_column: str,
    conversions: dict[str, float],
    output_column: str = "value_harmonized",
) -> pd.DataFrame:
    """Convert values into a common unit using explicit conversion factors."""
    harmonized = dataframe.copy()
    harmonized[value_column] = ensure_numeric_series(harmonized[value_column])
    harmonized[output_column] = harmonized.apply(
        lambda row: row[value_column] * conversions.get(str(row[unit_column]).lower(), 1.0),
        axis=1,
    )
    return harmonized


def convert_currency_series(
    dataframe: pd.DataFrame,
    value_column: str,
    rate_column: str,
    output_column: str = "value_converted",
) -> pd.DataFrame:
    """Convert a nominal series using a provided exchange-rate column."""
    converted = dataframe.copy()
    converted[value_column] = ensure_numeric_series(converted[value_column])
    converted[rate_column] = ensure_numeric_series(converted[rate_column])
    converted[output_column] = converted[value_column] * converted[rate_column]
    return converted

