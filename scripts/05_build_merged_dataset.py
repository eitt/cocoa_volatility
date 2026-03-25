"""Build the merged monthly analysis dataset."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_processing.build_analysis_dataset import build_analysis_dataset, finalize_analysis_columns
from src.utils.date_utils import convert_to_month_start
from src.utils.file_utils import load_yaml, write_dataframe
from src.utils.logging_utils import get_project_logger, log_dataframe_shape

PATHS = load_yaml(ROOT / "config" / "paths.yaml")
CONFIG = load_yaml(ROOT / "config" / "project_config.yaml")


def load_monthly_series(file_name: str, date_column: str, value_column: str, output_column: str) -> pd.DataFrame:
    """Load a cleaned CSV and collapse it to monthly observations."""
    path = ROOT / PATHS["data_interim_cleaned"] / file_name
    if not path.exists():
        return pd.DataFrame(columns=["date", output_column])

    frame = pd.read_csv(path)
    if date_column not in frame.columns or value_column not in frame.columns:
        return pd.DataFrame(columns=["date", output_column])

    series = frame[[date_column, value_column]].copy()
    series[date_column] = convert_to_month_start(series[date_column])
    series[value_column] = pd.to_numeric(series[value_column], errors="coerce")
    series = (
        series.dropna(subset=[date_column])
        .groupby(date_column, as_index=False)[value_column]
        .mean()
        .rename(columns={date_column: "date", value_column: output_column})
    )
    return series


def main() -> None:
    """Merge domestic, international, and EU series into one panel."""
    logger = get_project_logger("05_build_merged_dataset", ROOT / PATHS["output_logs"])

    domestic = load_monthly_series(
        "colombia_cocoa_prices_cleaned.csv",
        date_column="date",
        value_column="price",
        output_column=CONFIG["series"]["domestic_price"],
    )
    international = load_monthly_series(
        "world_cocoa_prices_cleaned.csv",
        date_column="date",
        value_column="world_cocoa_price_usd_mt",
        output_column=CONFIG["series"]["international_price"],
    )
    eu = load_monthly_series(
        "eu_price_indicators_cleaned.csv",
        date_column="date",
        value_column="eu_hicp_chocolate_index",
        output_column=CONFIG["series"]["eu_price"],
    )

    merged = build_analysis_dataset(domestic, international, eu, join_columns=["date"])
    merged = finalize_analysis_columns(
        merged,
        log_columns=[
            CONFIG["series"]["domestic_price"],
            CONFIG["series"]["international_price"],
            CONFIG["series"]["eu_price"],
        ],
    )

    output_path = ROOT / PATHS["data_processed_analysis_ready"] / "merged_cocoa_price_panel.csv"
    write_dataframe(merged, output_path)
    log_dataframe_shape(logger, "merged_cocoa_price_panel", merged)


if __name__ == "__main__":
    main()
