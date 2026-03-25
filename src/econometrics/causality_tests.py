"""Granger causality helpers."""

from __future__ import annotations

import pandas as pd
from statsmodels.tsa.stattools import grangercausalitytests


def run_granger_causality(dataframe: pd.DataFrame, variables: list[str], maxlag: int = 6) -> pd.DataFrame:
    """Run pairwise Granger causality tests for a two-variable system."""
    if len(variables) != 2:
        raise ValueError("Granger causality helper expects exactly two variables.")

    cleaned = dataframe[variables].dropna()
    results = grangercausalitytests(cleaned, maxlag=maxlag, verbose=False)
    records = []
    for lag, lag_result in results.items():
        test_statistic, p_value, *_ = lag_result[0]["ssr_ftest"]
        records.append({"lag": lag, "statistic": float(test_statistic), "p_value": float(p_value)})
    return pd.DataFrame(records)

