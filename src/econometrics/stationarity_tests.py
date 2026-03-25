"""Stationarity tests for price and return series."""

from __future__ import annotations

import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss


def run_adf_test(series: pd.Series, autolag: str = "AIC") -> dict[str, float | str]:
    """Run an Augmented Dickey-Fuller test on a series."""
    cleaned = series.dropna()
    statistic, p_value, lags, observations, *_ = adfuller(cleaned, autolag=autolag)
    return {
        "test": "adf",
        "statistic": float(statistic),
        "p_value": float(p_value),
        "lags": float(lags),
        "observations": float(observations),
    }


def run_kpss_test(series: pd.Series, regression: str = "c") -> dict[str, float | str]:
    """Run a KPSS test on a series."""
    cleaned = series.dropna()
    statistic, p_value, lags, *_ = kpss(cleaned, regression=regression, nlags="auto")
    return {
        "test": "kpss",
        "statistic": float(statistic),
        "p_value": float(p_value),
        "lags": float(lags),
        "observations": float(len(cleaned)),
    }


def run_phillips_perron_test(series: pd.Series) -> dict[str, float | str]:
    """Run a Phillips-Perron test when the optional dependency is available."""
    cleaned = series.dropna()
    try:
        from arch.unitroot import PhillipsPerron
    except ImportError:
        return {"test": "pp", "status": "arch_not_installed", "observations": float(len(cleaned))}

    result = PhillipsPerron(cleaned)
    return {
        "test": "pp",
        "statistic": float(result.stat),
        "p_value": float(result.pvalue),
        "lags": float(result.lags),
        "observations": float(len(cleaned)),
    }


def run_stationarity_suite(dataframe: pd.DataFrame, value_columns: list[str]) -> pd.DataFrame:
    """Run ADF, KPSS, and optional PP tests across selected columns."""
    records: list[dict[str, float | str]] = []
    for column in value_columns:
        if column not in dataframe.columns:
            continue
        records.extend(
            [
                {"variable": column, **run_adf_test(dataframe[column])},
                {"variable": column, **run_kpss_test(dataframe[column])},
                {"variable": column, **run_phillips_perron_test(dataframe[column])},
            ]
        )
    return pd.DataFrame(records)

