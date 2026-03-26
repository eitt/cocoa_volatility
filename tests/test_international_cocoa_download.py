from __future__ import annotations

from pathlib import Path
import tempfile

import pandas as pd

from src.data_collection.download_international_cocoa import build_yahoo_chart_url
from src.data_collection.import_world_bank import extract_world_bank_cocoa_monthly_series
from src.data_collection.import_yahoo_finance import normalize_yahoo_chart_payload


def test_build_yahoo_chart_url_contains_expected_query_arguments() -> None:
    url = build_yahoo_chart_url(symbol="CC=F", start_date="2000-01-01", end_date="2000-01-31", interval="1d")

    assert "finance/chart/CC=F" in url
    assert "interval=1d" in url
    assert "includeAdjustedClose=true" in url
    assert "events=history" in url


def test_normalize_yahoo_chart_payload_returns_expected_columns() -> None:
    payload = {
        "chart": {
            "result": [
                {
                    "meta": {"currency": "USD", "symbol": "CC=F"},
                    "timestamp": [946684800, 946771200],
                    "indicators": {
                        "quote": [
                            {
                                "open": [920.0, 930.0],
                                "high": [940.0, 950.0],
                                "low": [910.0, 920.0],
                                "close": [935.0, 945.0],
                                "volume": [100, 200],
                            }
                        ],
                        "adjclose": [{"adjclose": [935.0, 945.0]}],
                    },
                }
            ]
        }
    }

    normalized = normalize_yahoo_chart_payload(payload, frequency="daily", symbol="CC=F")

    assert normalized["world_cocoa_futures_usd_mt"].tolist() == [935.0, 945.0]
    assert normalized["frequency"].tolist() == ["daily", "daily"]
    assert normalized["symbol"].tolist() == ["CC=F", "CC=F"]


def test_extract_world_bank_cocoa_monthly_series_parses_cocoa_column() -> None:
    rows = [
        ["title", None, None],
        ["subtitle", None, None],
        ["note", None, None],
        ["updated", None, None],
        [None, "Coffee", "Cocoa"],
        [None, "($/kg)", "($/kg)"],
        ["1960M01", 0.111, 0.634],
        ["1960M02", 0.222, 0.608],
    ]
    dataframe = pd.DataFrame(rows)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "world_bank_sample.xlsx"
        with pd.ExcelWriter(path) as writer:
            dataframe.to_excel(writer, sheet_name="Monthly Prices", header=False, index=False)
        extracted = extract_world_bank_cocoa_monthly_series(str(path))

    assert extracted["world_cocoa_price_usd_kg"].tolist() == [0.634, 0.608]
    assert extracted["world_cocoa_price_usd_mt"].tolist() == [634.0, 608.0]
    assert extracted["currency"].tolist() == ["USD", "USD"]
