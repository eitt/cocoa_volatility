"""Volatility measures for cocoa price series."""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_log_returns(
    dataframe: pd.DataFrame,
    value_column: str,
    date_column: str,
    group_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Compute within-group log returns from a price series."""
    ordered = dataframe.sort_values((group_columns or []) + [date_column]).copy()
    if group_columns:
        ordered[f"{value_column}_log_return"] = ordered.groupby(group_columns)[value_column].transform(
            lambda series: np.log(series / series.shift(1))
        )
    else:
        ordered[f"{value_column}_log_return"] = np.log(ordered[value_column] / ordered[value_column].shift(1))
    return ordered


def compute_rolling_volatility(
    dataframe: pd.DataFrame,
    return_column: str,
    window: int = 12,
    group_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Compute rolling standard deviation of returns."""
    volatility = dataframe.copy()
    output_column = f"{return_column}_rolling_volatility"
    if group_columns:
        volatility[output_column] = volatility.groupby(group_columns)[return_column].transform(
            lambda series: series.rolling(window=window, min_periods=max(2, window // 2)).std()
        )
    else:
        volatility[output_column] = volatility[return_column].rolling(
            window=window, min_periods=max(2, window // 2)
        ).std()
    return volatility
