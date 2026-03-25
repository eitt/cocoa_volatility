"""Import helpers for ICCO statistics."""

from __future__ import annotations

import pandas as pd

from src.data_collection.load_local_files import load_tabular_file


def load_icco_prices(file_path: str, **kwargs) -> pd.DataFrame:
    """Load an ICCO file into a dataframe."""
    return load_tabular_file(file_path, **kwargs)


def standardize_icco_prices(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Standardize expected ICCO column names when possible."""
    renamed = dataframe.copy()
    renamed.columns = [
        str(column).strip().lower().replace(" ", "_").replace("-", "_")
        for column in renamed.columns
    ]
    return renamed

