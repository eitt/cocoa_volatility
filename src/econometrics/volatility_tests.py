"""Volatility diagnostics for time-series return data."""

from __future__ import annotations

import numpy as np
import pandas as pd
from statsmodels.stats.diagnostic import het_arch


def run_arch_lm_test(series: pd.Series, max_lags: int = 6) -> dict[str, float | str]:
    """Run an ARCH-LM test on a return series."""
    cleaned = pd.to_numeric(series, errors="coerce").dropna()
    if len(cleaned) < 12:
        return {
            "test": "arch_lm",
            "status": "insufficient_observations",
            "observations": float(len(cleaned)),
        }

    used_lags = max(1, min(max_lags, len(cleaned) // 5))
    lm_stat, lm_pvalue, f_stat, f_pvalue = het_arch(cleaned, nlags=used_lags)
    return {
        "test": "arch_lm",
        "lags": float(used_lags),
        "statistic": float(lm_stat),
        "p_value": float(lm_pvalue),
        "f_statistic": float(f_stat),
        "f_p_value": float(f_pvalue),
        "observations": float(len(cleaned)),
    }


def run_arch_lm_suite(dataframe: pd.DataFrame, value_columns: list[str], max_lags: int = 6) -> pd.DataFrame:
    """Run ARCH-LM tests across selected columns."""
    records: list[dict[str, float | str]] = []
    for column in value_columns:
        if column not in dataframe.columns:
            continue
        records.append({"variable": column, **run_arch_lm_test(dataframe[column], max_lags=max_lags)})
    return pd.DataFrame.from_records(records)


def compute_volatility_summary(
    dataframe: pd.DataFrame,
    return_columns: list[str],
    rolling_window: int = 12,
    periods_per_year: int = 12,
) -> pd.DataFrame:
    """Summarize return volatility characteristics for selected columns."""
    records: list[dict[str, float | str]] = []
    for column in return_columns:
        if column not in dataframe.columns:
            continue

        cleaned = pd.to_numeric(dataframe[column], errors="coerce").dropna()
        if cleaned.empty:
            continue

        rolling = cleaned.rolling(window=rolling_window, min_periods=max(2, rolling_window // 2)).std()
        records.append(
            {
                "variable": column,
                "observations": float(len(cleaned)),
                "mean_return": float(cleaned.mean()),
                "std_dev": float(cleaned.std()),
                "annualized_volatility": float(cleaned.std() * np.sqrt(periods_per_year)),
                "mean_abs_return": float(cleaned.abs().mean()),
                "max_abs_return": float(cleaned.abs().max()),
                "min_return": float(cleaned.min()),
                "max_return": float(cleaned.max()),
                "rolling_volatility_mean": float(rolling.mean()) if rolling.notna().any() else np.nan,
                "rolling_volatility_max": float(rolling.max()) if rolling.notna().any() else np.nan,
            }
        )

    return pd.DataFrame.from_records(records)
