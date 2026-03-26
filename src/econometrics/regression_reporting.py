"""Helpers for consistent regression fitting and reporting."""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


def fit_hac_ols(
    dataframe: pd.DataFrame,
    y_column: str,
    x_columns: list[str],
    maxlags: int = 1,
):
    """Fit an OLS model with HAC standard errors."""
    model_data = dataframe[[y_column, *x_columns]].dropna()
    y_values = model_data[y_column]
    x_values = sm.add_constant(model_data[x_columns])
    result = sm.OLS(y_values, x_values).fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})
    return result, model_data.index


def summarize_regression_result(
    result,
    model_id: str,
    chapter: str,
    sample_variant: str,
    dependent_variable: str,
    specification: str,
) -> pd.DataFrame:
    """Convert a statsmodels regression result into a coefficient table."""
    confidence_intervals = result.conf_int()
    records = []
    for parameter in result.params.index:
        records.append(
            {
                "chapter": chapter,
                "model_id": model_id,
                "sample_variant": sample_variant,
                "dependent_variable": dependent_variable,
                "specification": specification,
                "parameter": parameter,
                "coefficient": float(result.params[parameter]),
                "std_error": float(result.bse[parameter]),
                "t_stat": float(result.tvalues[parameter]),
                "p_value": float(result.pvalues[parameter]),
                "ci_lower": float(confidence_intervals.loc[parameter, 0]),
                "ci_upper": float(confidence_intervals.loc[parameter, 1]),
            }
        )
    return pd.DataFrame.from_records(records)


def summarize_model_fit(
    result,
    model_id: str,
    chapter: str,
    sample_variant: str,
    dependent_variable: str,
    specification: str,
) -> pd.DataFrame:
    """Convert a statsmodels regression result into a one-row fit summary."""
    return pd.DataFrame.from_records(
        [
            {
                "chapter": chapter,
                "model_id": model_id,
                "sample_variant": sample_variant,
                "dependent_variable": dependent_variable,
                "specification": specification,
                "nobs": float(result.nobs),
                "r_squared": float(result.rsquared),
                "adj_r_squared": float(result.rsquared_adj),
                "aic": float(result.aic),
                "bic": float(result.bic),
                "f_statistic": float(result.fvalue) if result.fvalue is not None else np.nan,
                "f_p_value": float(result.f_pvalue) if result.f_pvalue is not None else np.nan,
            }
        ]
    )
