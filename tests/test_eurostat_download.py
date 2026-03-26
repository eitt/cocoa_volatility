from __future__ import annotations

from src.data_collection.download_eurostat import build_eurostat_api_url, normalize_eurostat_filtered_payload


def test_build_eurostat_api_url_contains_expected_filters() -> None:
    url = build_eurostat_api_url(
        dataset_code="prc_hicp_midx",
        geo="EU27_2020",
        coicop="CP01183",
        unit="I15",
        frequency="M",
    )

    assert "prc_hicp_midx" in url
    assert "geo=EU27_2020" in url
    assert "coicop=CP01183" in url
    assert "unit=I15" in url
    assert "freq=M" in url


def test_normalize_eurostat_filtered_payload_returns_expected_monthly_frame() -> None:
    payload = {
        "updated": "2026-02-06T23:00:00+0100",
        "value": {"0": 100.0, "1": 101.2},
        "dimension": {
            "geo": {
                "category": {
                    "index": {"EU27_2020": 0},
                    "label": {"EU27_2020": "European Union - 27 countries (from 2020)"},
                }
            },
            "coicop": {
                "category": {
                    "index": {"CP01183": 0},
                    "label": {"CP01183": "Chocolate"},
                }
            },
            "unit": {
                "category": {
                    "index": {"I15": 0},
                    "label": {"I15": "Index, 2015=100"},
                }
            },
            "time": {
                "category": {
                    "index": {"2025-11": 0, "2025-12": 1},
                    "label": {"2025-11": "2025-11", "2025-12": "2025-12"},
                }
            },
        },
    }

    normalized = normalize_eurostat_filtered_payload(
        payload,
        value_column="eu_hicp_chocolate_index",
        series_name="eu_hicp_chocolate_index",
        source_dataset="HICP - monthly data (index)",
        source_url="https://example.com/eurostat",
    )

    assert normalized["date"].dt.strftime("%Y-%m-%d").tolist() == ["2025-11-01", "2025-12-01"]
    assert normalized["eu_hicp_chocolate_index"].tolist() == [100.0, 101.2]
    assert normalized["item_label"].tolist() == ["Chocolate", "Chocolate"]
    assert normalized["geo"].tolist() == ["EU27_2020", "EU27_2020"]
