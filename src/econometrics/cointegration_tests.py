"""Co-integration test helpers."""

from __future__ import annotations

import pandas as pd
from statsmodels.tsa.stattools import coint
from statsmodels.tsa.vector_ar.vecm import coint_johansen


def run_engle_granger_test(y: pd.Series, x: pd.Series) -> dict[str, float]:
    """Run an Engle-Granger co-integration test."""
    aligned = pd.concat([y, x], axis=1).dropna()
    statistic, p_value, critical_values = coint(aligned.iloc[:, 0], aligned.iloc[:, 1])
    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "critical_value_1pct": float(critical_values[0]),
        "critical_value_5pct": float(critical_values[1]),
        "critical_value_10pct": float(critical_values[2]),
    }


def run_johansen_test(dataframe: pd.DataFrame, det_order: int = 0, k_ar_diff: int = 1) -> pd.DataFrame:
    """Run a Johansen co-integration test on a multivariate system."""
    cleaned = dataframe.dropna()
    result = coint_johansen(cleaned, det_order=det_order, k_ar_diff=k_ar_diff)
    return pd.DataFrame(
        {
            "trace_statistic": result.lr1,
            "critical_value_90pct": result.cvt[:, 0],
            "critical_value_95pct": result.cvt[:, 1],
            "critical_value_99pct": result.cvt[:, 2],
        }
    )

