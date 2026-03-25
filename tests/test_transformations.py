from __future__ import annotations

import pandas as pd

from src.data_processing.deflate_prices import deflate_nominal_series
from src.data_processing.frequency_conversion import convert_to_monthly_frequency
from src.descriptive.volatility_measures import compute_log_returns


def test_convert_to_monthly_frequency_means_values() -> None:
    dataframe = pd.DataFrame(
        {
            "date": ["2024-01-05", "2024-01-20", "2024-02-01"],
            "series": ["a", "a", "a"],
            "value": [10.0, 20.0, 30.0],
        }
    )

    monthly = convert_to_monthly_frequency(
        dataframe,
        date_column="date",
        group_columns=["series"],
        value_column="value",
    )

    assert len(monthly) == 2
    assert monthly.loc[0, "value"] == 15.0


def test_deflate_nominal_series_creates_real_price() -> None:
    dataframe = pd.DataFrame({"nominal": [200.0], "deflator": [100.0]})
    deflated = deflate_nominal_series(dataframe, nominal_column="nominal", deflator_column="deflator")
    assert deflated.loc[0, "real_price"] == 200.0


def test_compute_log_returns_adds_return_column() -> None:
    dataframe = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-02-01"]),
            "price": [10.0, 20.0],
        }
    )

    returns = compute_log_returns(dataframe, value_column="price", date_column="date")
    assert "price_log_return" in returns.columns

