"""Helpers for constructing the final analysis panel."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.data_processing.merge_series import merge_time_series, sort_series_panel


def build_analysis_dataset(
    domestic_df: pd.DataFrame,
    international_df: pd.DataFrame,
    eu_df: pd.DataFrame,
    trade_df: pd.DataFrame | None = None,
    climate_df: pd.DataFrame | None = None,
    join_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Merge the main analytical blocks into one panel."""
    frames = [domestic_df, international_df, eu_df]
    if trade_df is not None:
        frames.append(trade_df)
    if climate_df is not None:
        frames.append(climate_df)

    merged = merge_time_series(frames, join_columns=join_columns or ["date"], how="outer")
    return sort_series_panel(merged, date_column="date")


def finalize_analysis_columns(dataframe: pd.DataFrame, log_columns: list[str]) -> pd.DataFrame:
    """Add log-transformed versions of selected columns."""
    finalized = dataframe.copy()
    for column in log_columns:
        if column in finalized.columns:
            finalized[f"log_{column}"] = np.log(finalized[column].where(finalized[column] > 0))
    return finalized
