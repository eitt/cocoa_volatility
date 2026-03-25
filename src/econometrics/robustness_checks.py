"""Simple robustness utilities."""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd


def run_subsample_check(
    dataframe: pd.DataFrame,
    date_column: str,
    split_date: str,
    model_function: Callable[[pd.DataFrame], object],
) -> dict[str, object]:
    """Estimate the same model on pre- and post-split subsamples."""
    cutoff = pd.Timestamp(split_date)
    pre_sample = dataframe.loc[dataframe[date_column] < cutoff].copy()
    post_sample = dataframe.loc[dataframe[date_column] >= cutoff].copy()
    return {
        "pre_sample_result": model_function(pre_sample) if not pre_sample.empty else None,
        "post_sample_result": model_function(post_sample) if not post_sample.empty else None,
    }
