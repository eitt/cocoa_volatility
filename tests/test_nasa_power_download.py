from __future__ import annotations

import pandas as pd

from src.data_collection.download_nasa_power import (
    build_nasa_power_point_url,
    normalize_nasa_power_payload,
    pivot_nasa_power_long_to_wide,
)


def test_build_nasa_power_point_url_contains_expected_query_arguments() -> None:
    url = build_nasa_power_point_url(
        frequency="monthly",
        parameters=["PRECTOTCORR", "T2M"],
        latitude=6.9287793,
        longitude=-73.5207543,
        start="2000",
        end="2025",
    )

    assert "/api/temporal/monthly/point?" in url
    assert "parameters=PRECTOTCORR%2CT2M" in url
    assert "community=AG" in url
    assert "start=2000" in url
    assert "end=2025" in url


def test_normalize_nasa_power_payload_drops_monthly_annual_summary_rows() -> None:
    payload = {
        "geometry": {"coordinates": [-73.521, 6.929, 391.22]},
        "header": {
            "fill_value": -999.0,
            "time_standard": "LST",
            "start": "20200101",
            "end": "20201231",
        },
        "properties": {
            "parameter": {
                "PRECTOTCORR": {"202001": 3.48, "202013": 2.61},
                "T2M": {"202001": 25.47, "202013": 26.70},
            },
        },
        "parameters": {
            "PRECTOTCORR": {"units": "mm/day", "longname": "Precipitation Corrected"},
            "T2M": {"units": "C", "longname": "Temperature at 2 Meters"},
        },
    }

    normalized = normalize_nasa_power_payload(
        payload,
        frequency="monthly",
        location_metadata={"location_id": "san_vicente_de_chucuri"},
        source_url="https://power.larc.nasa.gov/api/temporal/monthly/point",
    )

    assert len(normalized) == 2
    assert normalized["period_code"].tolist() == ["202001", "202001"]
    assert normalized["date"].tolist() == [pd.Timestamp("2020-01-01"), pd.Timestamp("2020-01-01")]
    assert normalized["variable"].tolist() == ["PRECTOTCORR", "T2M"]


def test_pivot_nasa_power_long_to_wide_returns_one_row_per_period() -> None:
    long_df = pd.DataFrame(
        {
            "location_id": ["san_vicente_de_chucuri", "san_vicente_de_chucuri"],
            "location_name": ["San Vicente de Chucuri", "San Vicente de Chucuri"],
            "frequency": ["daily", "daily"],
            "date": [pd.Timestamp("2020-01-01"), pd.Timestamp("2020-01-01")],
            "period_code": ["20200101", "20200101"],
            "variable": ["PRECTOTCORR", "T2M"],
            "value": [34.27, 25.49],
            "unit": ["mm/day", "C"],
            "variable_long_name": ["Precipitation Corrected", "Temperature at 2 Meters"],
            "latitude": [6.929, 6.929],
            "longitude": [-73.521, -73.521],
            "elevation_m": [391.22, 391.22],
            "time_standard": ["LST", "LST"],
            "request_start": ["20200101", "20200101"],
            "request_end": ["20200105", "20200105"],
            "source_url": ["https://power.larc.nasa.gov", "https://power.larc.nasa.gov"],
        }
    )

    wide_df = pivot_nasa_power_long_to_wide(long_df)

    assert len(wide_df) == 1
    assert wide_df.loc[0, "PRECTOTCORR"] == 34.27
    assert wide_df.loc[0, "T2M"] == 25.49
