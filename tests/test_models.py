from __future__ import annotations

import numpy as np
import pandas as pd

from src.econometrics.pass_through_models import estimate_pass_through_elasticity
from src.econometrics.stationarity_tests import run_stationarity_suite


def test_run_stationarity_suite_returns_expected_tests() -> None:
    rng = np.random.default_rng(42)
    dataframe = pd.DataFrame({"series": rng.normal(size=60)})

    results = run_stationarity_suite(dataframe, ["series"])

    assert set(results["test"]) >= {"adf", "kpss", "pp"}


def test_estimate_pass_through_elasticity_recovers_positive_relationship() -> None:
    dataframe = pd.DataFrame({"x": [1, 2, 3, 4], "y": [5, 8, 11, 14]})

    result = estimate_pass_through_elasticity(dataframe, y_column="y", x_columns=["x"])

    assert result.params["x"] > 0
