"""ARIMA estimation helpers."""

from __future__ import annotations

import pandas as pd
from statsmodels.tsa.arima.model import ARIMA


def estimate_arima_model(series: pd.Series, order: tuple[int, int, int], exog: pd.DataFrame | None = None):
    """Fit an ARIMA model to a cleaned series."""
    cleaned = series.dropna()
    model = ARIMA(cleaned, order=order, exog=exog.loc[cleaned.index] if exog is not None else None)
    return model.fit()


def summarize_arima_result(result) -> dict[str, float]:
    """Extract a compact ARIMA summary for tabulation."""
    return {
        "aic": float(result.aic),
        "bic": float(result.bic),
        "hqic": float(result.hqic),
        "llf": float(result.llf),
    }

