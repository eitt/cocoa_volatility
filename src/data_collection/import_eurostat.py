"""Import helpers for Eurostat price series."""

from __future__ import annotations

import pandas as pd

from src.data_collection.load_local_files import load_tabular_file


def load_eurostat_series(file_path: str, **kwargs) -> pd.DataFrame:
    """Load a Eurostat export file."""
    return load_tabular_file(file_path, **kwargs)


def filter_eurostat_series(
    dataframe: pd.DataFrame,
    geo_codes: list[str] | None = None,
    item_codes: list[str] | None = None,
) -> pd.DataFrame:
    """Filter Eurostat series by geography and item code when columns exist."""
    filtered = dataframe.copy()
    if geo_codes and "geo" in filtered.columns:
        filtered = filtered.loc[filtered["geo"].isin(geo_codes)]
    if item_codes and "item" in filtered.columns:
        filtered = filtered.loc[filtered["item"].isin(item_codes)]
    return filtered.copy()

