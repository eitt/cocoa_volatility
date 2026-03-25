"""Import helpers for trade-flow files."""

from __future__ import annotations

import pandas as pd

from src.data_collection.load_local_files import load_tabular_file


def load_trade_data(file_path: str, **kwargs) -> pd.DataFrame:
    """Load a trade data file."""
    return load_tabular_file(file_path, **kwargs)


def filter_cocoa_hs_codes(dataframe: pd.DataFrame, hs_codes: list[str], column: str = "hs_code") -> pd.DataFrame:
    """Keep trade observations belonging to cocoa-related HS codes."""
    if column not in dataframe.columns:
        return dataframe.copy()
    normalized = dataframe.copy()
    normalized[column] = normalized[column].astype(str).str.zfill(4)
    return normalized.loc[normalized[column].isin(hs_codes)].copy()

