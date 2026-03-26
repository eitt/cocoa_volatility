"""Download helpers for Eurostat HICP series."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd
import requests

from src.utils.file_utils import ensure_directory


def build_eurostat_api_url(
    dataset_code: str,
    geo: str,
    coicop: str,
    unit: str = "I15",
    frequency: str = "M",
) -> str:
    """Build a filtered Eurostat statistics API URL."""
    query = urlencode(
        {
            "geo": geo,
            "coicop": coicop,
            "unit": unit,
            "freq": frequency,
        }
    )
    return f"https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{dataset_code}?{query}"


def fetch_eurostat_json(url: str, timeout: int = 120, headers: dict[str, str] | None = None) -> dict:
    """Fetch a Eurostat JSON payload."""
    response = requests.get(url, timeout=timeout, headers=headers or {"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    return response.json()


def write_eurostat_json(payload: dict, output_path: str | Path) -> Path:
    """Write a Eurostat payload to disk."""
    path = Path(output_path)
    ensure_directory(path.parent)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_eurostat_json_payload(file_path: str | Path) -> dict:
    """Load a saved Eurostat JSON payload."""
    return json.loads(Path(file_path).read_text(encoding="utf-8"))


def normalize_eurostat_filtered_payload(
    payload: dict,
    value_column: str,
    series_name: str,
    source_dataset: str,
    source_url: str | None = None,
) -> pd.DataFrame:
    """Normalize a filtered Eurostat HICP payload into a monthly dataframe."""
    dimensions = payload.get("dimension", {})
    geo_category = ((dimensions.get("geo") or {}).get("category") or {})
    geo_codes = list((geo_category.get("index") or {}).keys())
    geo_labels = geo_category.get("label") or {}
    geo_code = geo_codes[0] if geo_codes else None

    item_category = ((dimensions.get("coicop") or {}).get("category") or {})
    item_codes = list((item_category.get("index") or {}).keys())
    item_labels = item_category.get("label") or {}
    item_code = item_codes[0] if item_codes else None

    unit_category = ((dimensions.get("unit") or {}).get("category") or {})
    unit_codes = list((unit_category.get("index") or {}).keys())
    unit_labels = unit_category.get("label") or {}
    unit_code = unit_codes[0] if unit_codes else None

    time_category = ((dimensions.get("time") or {}).get("category") or {})
    time_index = time_category.get("index") or {}
    reverse_time_index = {int(index): label for label, index in time_index.items()}

    records: list[dict[str, object]] = []
    for flattened_index, value in (payload.get("value") or {}).items():
        time_code = reverse_time_index.get(int(flattened_index))
        if not time_code:
            continue
        records.append(
            {
                "date": pd.Timestamp(f"{time_code}-01"),
                value_column: value,
                "geo": geo_code,
                "geo_label": geo_labels.get(geo_code, geo_code),
                "item": item_code,
                "item_label": item_labels.get(item_code, item_code),
                "unit": unit_code,
                "unit_label": unit_labels.get(unit_code, unit_code),
                "frequency": "monthly",
                "series_name": series_name,
                "source_institution": "Eurostat",
                "source_dataset": source_dataset,
                "source_url": source_url,
                "api_updated": payload.get("updated"),
            }
        )

    return pd.DataFrame.from_records(records).sort_values("date").reset_index(drop=True)
