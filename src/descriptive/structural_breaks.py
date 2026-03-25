"""Simple break-screening helpers."""

from __future__ import annotations

import pandas as pd


def flag_large_changes(dataframe: pd.DataFrame, return_column: str, threshold: float = 2.0) -> pd.DataFrame:
    """Flag observations where returns exceed a chosen standard deviation threshold."""
    flagged = dataframe.copy()
    std_dev = flagged[return_column].std(skipna=True)
    flagged["break_flag"] = flagged[return_column].abs() > threshold * std_dev
    return flagged

