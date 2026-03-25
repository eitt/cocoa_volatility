"""Import helpers for SIPSA price files."""

from __future__ import annotations

import pandas as pd

from src.data_collection.load_local_files import load_tabular_file


def load_sipsa_prices(file_path: str, **kwargs) -> pd.DataFrame:
    """Load a SIPSA file into a dataframe."""
    return load_tabular_file(file_path, **kwargs)


def clean_sipsa_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Standardize SIPSA column names to snake case."""
    cleaned = dataframe.copy()
    cleaned.columns = [
        str(column).strip().lower().replace(" ", "_").replace("-", "_")
        for column in cleaned.columns
    ]
    return cleaned


def select_cocoa_rows(dataframe: pd.DataFrame, product_column: str = "product_name") -> pd.DataFrame:
    """Keep rows whose product label contains cacao or cocoa."""
    if product_column not in dataframe.columns:
        return dataframe.copy()
    mask = dataframe[product_column].astype(str).str.lower().str.contains("cacao|cocoa", na=False)
    return dataframe.loc[mask].copy()

