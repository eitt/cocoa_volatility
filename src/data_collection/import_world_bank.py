"""Import helpers for World Bank commodity price files."""

from __future__ import annotations

import pandas as pd

from src.data_collection.load_local_files import load_tabular_file


def load_world_bank_prices(file_path: str, **kwargs) -> pd.DataFrame:
    """Load a World Bank commodity file."""
    return load_tabular_file(file_path, **kwargs)


def reshape_world_bank_prices(
    dataframe: pd.DataFrame,
    date_column: str = "date",
    value_column: str = "price",
    series_name: str = "world_cocoa_price_usd_mt",
) -> pd.DataFrame:
    """Return a long-form dataframe with a consistent series label."""
    reshaped = dataframe.copy()
    if date_column not in reshaped.columns or value_column not in reshaped.columns:
        return reshaped
    reshaped["series_name"] = series_name
    return reshaped[[date_column, value_column, "series_name"]].copy()

