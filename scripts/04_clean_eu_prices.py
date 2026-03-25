"""Clean EU cocoa or chocolate price indicator files."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_collection.import_eurostat import filter_eurostat_series, load_eurostat_series
from src.data_collection.load_local_files import list_raw_files
from src.data_processing.clean_eu_prices import clean_eu_price_columns, scale_eu_indices
from src.utils.file_utils import load_yaml, write_dataframe
from src.utils.logging_utils import get_project_logger, log_dataframe_shape

PATHS = load_yaml(ROOT / "config" / "paths.yaml")


def main() -> None:
    """Load, standardize, and store EU downstream price inputs."""
    logger = get_project_logger("04_clean_eu_prices", ROOT / PATHS["output_logs"])
    raw_files = list_raw_files(ROOT / PATHS["raw_eu"])
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

    for raw_file in raw_files:
        try:
            frame = load_eurostat_series(raw_file)
            frame.columns = [str(column).strip().lower() for column in frame.columns]
            frame = clean_eu_price_columns(frame, column_map)
            frame = filter_eurostat_series(frame, geo_codes=["EU27_2020", "FR"])
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
