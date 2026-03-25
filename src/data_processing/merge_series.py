"""Series merging helpers."""

from __future__ import annotations

from functools import reduce

import pandas as pd


def merge_time_series(
    series_frames: list[pd.DataFrame],
    join_columns: list[str],
    how: str = "outer",
) -> pd.DataFrame:
    """Merge many time-series dataframes on a shared key."""
    valid_frames = [frame.copy() for frame in series_frames if not frame.empty]
    if not valid_frames:
        return pd.DataFrame(columns=join_columns)
    return reduce(lambda left, right: left.merge(right, on=join_columns, how=how), valid_frames)


def sort_series_panel(
    dataframe: pd.DataFrame,
    date_column: str,
    entity_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Sort a merged panel on entity keys and time."""
    order = (entity_columns or []) + [date_column]
    return dataframe.sort_values(order).reset_index(drop=True)

