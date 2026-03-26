"""Clean EU cocoa or chocolate price indicator files."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_collection.download_eurostat import (
    build_eurostat_api_url,
    load_eurostat_json_payload,
    normalize_eurostat_filtered_payload,
)
from src.data_collection.import_eurostat import filter_eurostat_series, load_eurostat_series
from src.data_collection.load_local_files import list_raw_files
from src.data_processing.clean_eu_prices import clean_eu_price_columns, scale_eu_indices
from src.utils.file_utils import load_yaml, write_dataframe
from src.utils.logging_utils import get_project_logger, log_dataframe_shape

PATHS = load_yaml(ROOT / "config" / "paths.yaml")
EU_SOURCE_CONFIG = load_yaml(ROOT / "config" / "eu_market_sources.yaml")


def main() -> None:
    """Load, standardize, and store EU downstream price inputs."""
    logger = get_project_logger("04_clean_eu_prices", ROOT / PATHS["output_logs"])
    raw_files = list_raw_files(ROOT / PATHS["raw_eu"], patterns=("*.csv", "*.xlsx", "*.parquet", "*.json"))
    column_map = {
        "time": "date",
        "date": "date",
        "geo": "geo",
        "value": "eu_hicp_chocolate_index",
        "obs_value": "eu_hicp_chocolate_index",
        "coicop": "item",
        "unit": "unit",
    }
    frames = []
    configured_series = EU_SOURCE_CONFIG["eu_market_prices"]["eurostat"].get("series", [])
    series_lookup = {(series["geo"], series["coicop"]): series for series in configured_series}

    for raw_file in raw_files:
        try:
            if raw_file.suffix.lower() == ".json" and "eurostat" in raw_file.name.lower():
                payload = load_eurostat_json_payload(raw_file)
                geo_codes = list((((payload.get("dimension") or {}).get("geo") or {}).get("category") or {}).get("index", {}).keys())
                item_codes = list((((payload.get("dimension") or {}).get("coicop") or {}).get("category") or {}).get("index", {}).keys())
                lookup_key = (geo_codes[0] if geo_codes else None, item_codes[0] if item_codes else None)
                series_config = series_lookup.get(lookup_key)
                if not series_config:
                    logger.warning("Skipping %s because no series configuration matched %s", raw_file.name, lookup_key)
                    continue

                frame = normalize_eurostat_filtered_payload(
                    payload,
                    value_column=series_config["value_column"],
                    series_name=series_config["series_name"],
                    source_dataset=EU_SOURCE_CONFIG["eu_market_prices"]["eurostat"]["dataset_name"],
                    source_url=build_eurostat_api_url(
                        dataset_code=EU_SOURCE_CONFIG["eu_market_prices"]["eurostat"]["dataset_code"],
                        geo=series_config["geo"],
                        coicop=series_config["coicop"],
                        unit=EU_SOURCE_CONFIG["eu_market_prices"]["eurostat"]["unit"],
                        frequency=EU_SOURCE_CONFIG["eu_market_prices"]["eurostat"]["frequency"],
                    ),
                )
                frame["source_file"] = raw_file.name
                frames.append(frame)
                continue

            frame = load_eurostat_series(raw_file)
            frame.columns = [str(column).strip().lower() for column in frame.columns]
            frame = clean_eu_price_columns(frame, column_map)
            frame = filter_eurostat_series(frame, geo_codes=["EU27_2020"], item_codes=["CP01183"])
            frame = scale_eu_indices(frame, value_column="eu_hicp_chocolate_index")
            frame["source_file"] = raw_file.name
            frames.append(frame)
        except Exception as error:  # pragma: no cover
            logger.warning("Skipping %s because %s", raw_file.name, error)

    if frames:
        cleaned = pd.concat(frames, ignore_index=True)
    else:
        cleaned = pd.DataFrame(columns=["date", "geo", "eu_hicp_chocolate_index", "item", "unit", "source_file"])

    output_path = ROOT / PATHS["data_interim_cleaned"] / "eu_price_indicators_cleaned.csv"
    write_dataframe(cleaned, output_path)
    log_dataframe_shape(logger, "eu_price_indicators_cleaned", cleaned)


if __name__ == "__main__":
    main()
