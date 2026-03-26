"""Clean international cocoa benchmark and futures price files."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_collection.import_icco import load_icco_prices, standardize_icco_prices
from src.data_collection.import_world_bank import extract_world_bank_cocoa_monthly_series
from src.data_collection.import_yahoo_finance import load_yahoo_chart_payload, normalize_yahoo_chart_payload
from src.data_collection.load_local_files import list_raw_files
from src.data_processing.clean_international_prices import clean_international_price_columns, standardize_world_currency
from src.utils.file_utils import load_yaml, write_dataframe
from src.utils.logging_utils import get_project_logger, log_dataframe_shape

PATHS = load_yaml(ROOT / "config" / "paths.yaml")


def main() -> None:
    """Load, standardize, and store international cocoa price inputs."""
    logger = get_project_logger("03_clean_international_prices", ROOT / PATHS["output_logs"])
    raw_files = list_raw_files(ROOT / PATHS["raw_international"], patterns=("*.csv", "*.xlsx", "*.parquet", "*.json"))
    column_map = {
        "date": "date",
        "month": "date",
        "time": "date",
        "cocoa_price": "world_cocoa_price_usd_mt",
        "price": "world_cocoa_price_usd_mt",
        "value": "world_cocoa_price_usd_mt",
        "currency": "currency",
        "unit": "unit",
    }
    benchmark_frames = []
    futures_frames = []

    for raw_file in raw_files:
        try:
            lower_name = raw_file.name.lower()

            if raw_file.suffix.lower() == ".json" and "yahoo_finance" in lower_name:
                payload = load_yahoo_chart_payload(raw_file)
                result = ((payload.get("chart") or {}).get("result") or [{}])[0]
                symbol = (result.get("meta") or {}).get("symbol", "CC=F")
                frequency = "monthly" if "monthly" in lower_name else "daily"
                frame = normalize_yahoo_chart_payload(payload, frequency=frequency, symbol=symbol)
                frame["source_file"] = raw_file.name
                futures_frames.append(frame)
                continue

            if raw_file.suffix.lower() in {".xlsx", ".xls"} and "world_bank" in lower_name:
                frame = extract_world_bank_cocoa_monthly_series(str(raw_file))
                frame["source_file"] = raw_file.name
                benchmark_frames.append(frame)
                continue

            frame = load_icco_prices(raw_file)
            frame = standardize_icco_prices(frame)
            frame = clean_international_price_columns(frame, column_map)
            frame = standardize_world_currency(
                frame,
                value_column="world_cocoa_price_usd_mt",
                currency_column="currency",
            )
            frame["frequency"] = "monthly"
            frame["series_name"] = "world_cocoa_price_usd_mt"
            frame["source_file"] = raw_file.name
            benchmark_frames.append(frame)
        except Exception as error:  # pragma: no cover
            logger.warning("Skipping %s because %s", raw_file.name, error)

    if benchmark_frames:
        benchmark_cleaned = pd.concat(benchmark_frames, ignore_index=True)
    else:
        benchmark_cleaned = pd.DataFrame(
            columns=[
                "date",
                "period_code",
                "world_cocoa_price_usd_kg",
                "world_cocoa_price_usd_mt",
                "currency",
                "unit",
                "frequency",
                "series_name",
                "source_institution",
                "source_dataset",
                "source_unit_raw",
                "source_file",
            ]
        )

    output_path = ROOT / PATHS["data_interim_cleaned"] / "world_cocoa_prices_cleaned.csv"
    write_dataframe(benchmark_cleaned, output_path)
    log_dataframe_shape(logger, "world_cocoa_prices_cleaned", benchmark_cleaned)

    if futures_frames:
        futures_cleaned = pd.concat(futures_frames, ignore_index=True)
    else:
        futures_cleaned = pd.DataFrame(
            columns=[
                "date",
                "symbol",
                "frequency",
                "world_cocoa_futures_usd_mt",
                "open",
                "high",
                "low",
                "close",
                "adj_close",
                "volume",
                "currency",
                "unit",
                "series_name",
                "source_institution",
                "source_dataset",
                "source_url",
                "source_file",
            ]
        )

    futures_output_path = ROOT / PATHS["data_interim_cleaned"] / "world_cocoa_futures_prices_cleaned.csv"
    write_dataframe(futures_cleaned, futures_output_path)
    log_dataframe_shape(logger, "world_cocoa_futures_prices_cleaned", futures_cleaned)


if __name__ == "__main__":
    main()
