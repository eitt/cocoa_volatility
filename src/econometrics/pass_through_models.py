"""Pass-through estimation helpers."""

from __future__ import annotations

import pandas as pd
import statsmodels.api as sm


def estimate_pass_through_elasticity(
    dataframe: pd.DataFrame,
    y_column: str,
    x_columns: list[str],
):
    """Estimate a simple pass-through regression with an intercept."""
    model_data = dataframe[[y_column, *x_columns]].dropna()
    y_values = model_data[y_column]
    x_values = sm.add_constant(model_data[x_columns])
    return sm.OLS(y_values, x_values).fit()


def summarize_pass_through_result(result) -> pd.DataFrame:
    """Convert a regression result into a compact coefficient table."""
    return pd.DataFrame(
        {
            "parameter": result.params.index,
            "coefficient": result.params.values,
            "p_value": result.pvalues.values,
        }
    )

