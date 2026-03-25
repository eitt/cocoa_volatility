"""Deflation helpers for nominal price series."""

from __future__ import annotations

import pandas as pd

from src.utils.validation_utils import ensure_numeric_series


def deflate_nominal_series(
    dataframe: pd.DataFrame,
    nominal_column: str,
    deflator_column: str,
    base: float = 100.0,
    output_column: str = "real_price",
) -> pd.DataFrame:
    """Convert nominal prices to real prices using an index-style deflator."""
    adjusted = dataframe.copy()
    adjusted[nominal_column] = ensure_numeric_series(adjusted[nominal_column])
    adjusted[deflator_column] = ensure_numeric_series(adjusted[deflator_column])
    adjusted[output_column] = adjusted[nominal_column] / adjusted[deflator_column] * base
    return adjusted

