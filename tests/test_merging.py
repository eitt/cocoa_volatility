from __future__ import annotations

import pandas as pd

from src.data_processing.build_analysis_dataset import build_analysis_dataset
from src.data_processing.merge_series import merge_time_series


def test_merge_time_series_on_date_column() -> None:
    left = pd.DataFrame({"date": ["2024-01-01"], "domestic": [1.0]})
    right = pd.DataFrame({"date": ["2024-01-01"], "world": [2.0]})

    merged = merge_time_series([left, right], join_columns=["date"])

    assert list(merged.columns) == ["date", "domestic", "world"]
    assert merged.loc[0, "world"] == 2.0


def test_build_analysis_dataset_combines_three_blocks() -> None:
    domestic = pd.DataFrame({"date": ["2024-01-01"], "domestic": [1.0]})
    world = pd.DataFrame({"date": ["2024-01-01"], "world": [2.0]})
    eu = pd.DataFrame({"date": ["2024-01-01"], "eu": [3.0]})

    panel = build_analysis_dataset(domestic, world, eu, join_columns=["date"])

    assert set(panel.columns) == {"date", "domestic", "world", "eu"}

