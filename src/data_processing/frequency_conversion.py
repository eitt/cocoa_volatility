"""Frequency conversion helpers for panel time series."""

from __future__ import annotations

import pandas as pd

from src.utils.date_utils import convert_to_month_start


def convert_to_monthly_frequency(
    dataframe: pd.DataFrame,
    date_column: str,
    group_columns: list[str],
    value_column: str,
    how: str = "mean",
) -> pd.DataFrame:
    """Aggregate a dataframe to month-start timestamps."""
    monthly = dataframe.copy()
    monthly[date_column] = convert_to_month_start(monthly[date_column])
    aggregations = {value_column: how}
    return (
        monthly.groupby(group_columns + [date_column], dropna=False, as_index=False)
        .agg(aggregations)
        .sort_values(group_columns + [date_column])
    )

