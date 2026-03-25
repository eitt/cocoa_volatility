"""Clean international cocoa benchmark price files."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_collection.import_icco import load_icco_prices, standardize_icco_prices
from src.data_collection.load_local_files import list_raw_files
from src.data_processing.clean_international_prices import clean_international_price_columns, standardize_world_currency
from src.utils.file_utils import load_yaml, write_dataframe
from src.utils.logging_utils import get_project_logger, log_dataframe_shape

PATHS = load_yaml(ROOT / "config" / "paths.yaml")


def main() -> None:
    """Load, standardize, and store international cocoa price inputs."""
    logger = get_project_logger("03_clean_international_prices", ROOT / PATHS["output_logs"])
    raw_files = list_raw_files(ROOT / PATHS["raw_international"])
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
    frames = []

    for raw_file in raw_files:
        try:
            frame = load_icco_prices(raw_file)
            frame = standardize_icco_prices(frame)
            frame = clean_international_price_columns(frame, column_map)
            frame = standardize_world_currency(
                frame,
                value_column="world_cocoa_price_usd_mt",
                currency_column="currency",
            )
            frame["source_file"] = raw_file.name
            frames.append(frame)
        except Exception as error:  # pragma: no cover
            logger.warning("Skipping %s because %s", raw_file.name, error)

    if frames:
        cleaned = pd.concat(frames, ignore_index=True)
    else:
        cleaned = pd.DataFrame(
            columns=["date", "world_cocoa_price_usd_mt", "currency", "unit", "source_file"]
        )

    output_path = ROOT / PATHS["data_interim_cleaned"] / "world_cocoa_prices_cleaned.csv"
    write_dataframe(cleaned, output_path)
    log_dataframe_shape(logger, "world_cocoa_prices_cleaned", cleaned)


if __name__ == "__main__":
    main()
