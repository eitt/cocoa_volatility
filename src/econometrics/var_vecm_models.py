"""VAR and VECM estimation helpers."""

from __future__ import annotations

import pandas as pd
from statsmodels.tsa.vector_ar.var_model import VAR
from statsmodels.tsa.vector_ar.vecm import VECM


def select_var_lag_order(dataframe: pd.DataFrame, maxlags: int = 12):
    """Estimate lag-order selection statistics for a VAR."""
    cleaned = dataframe.dropna()
    return VAR(cleaned).select_order(maxlags=maxlags)


def fit_var_model(dataframe: pd.DataFrame, maxlags: int = 12):
    """Fit a VAR using AIC-selected lags."""
    cleaned = dataframe.dropna()
    lag_selection = VAR(cleaned).select_order(maxlags=maxlags)
    selected_lag = lag_selection.aic or 1
    return VAR(cleaned).fit(selected_lag)


def fit_vecm_model(dataframe: pd.DataFrame, coint_rank: int, k_ar_diff: int = 1):
    """Fit a VECM for a co-integrated multivariate system."""
    cleaned = dataframe.dropna()
    return VECM(cleaned, coint_rank=coint_rank, k_ar_diff=k_ar_diff).fit()
