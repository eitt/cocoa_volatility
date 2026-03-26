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
CLIMATE_CONFIG = load_yaml(ROOT / "config" / "climate_locations.yaml")

CLIMATE_RENAME_MAP = {
    "PRECTOTCORR": "nasa_precipitation_mm_day",
    "T2M": "nasa_temperature_c",
    "T2M_MAX": "nasa_temperature_max_c",
    "T2M_MIN": "nasa_temperature_min_c",
    "RH2M": "nasa_relative_humidity_pct",
    "WS2M": "nasa_wind_speed_ms",
    "ALLSKY_SFC_SW_DWN": "nasa_surface_solar_radiation_mj_m2_day",
}


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


def load_latest_monthly_climate_series() -> pd.DataFrame:
    """Load the latest monthly NASA POWER wide table and rename selected variables."""
    harmonized_dir = ROOT / PATHS["data_interim_harmonized"]
    candidates = sorted(harmonized_dir.glob("*_nasa_power_all_locations_wide.csv"))
    if not candidates:
        candidates = sorted(harmonized_dir.glob("*_monthly_nasa_power_wide.csv"))
    if not candidates:
        return pd.DataFrame(columns=["date"] + list(CLIMATE_RENAME_MAP.values()))

    frame = pd.read_csv(candidates[-1])
    if "frequency" in frame.columns:
        frame = frame.loc[frame["frequency"].astype(str).str.lower() == "monthly"].copy()

    locations = CLIMATE_CONFIG.get("locations", [])
    preferred_location_id = locations[0].get("location_id") if locations else None
    if preferred_location_id and "location_id" in frame.columns:
        preferred_frame = frame.loc[frame["location_id"] == preferred_location_id].copy()
        if not preferred_frame.empty:
            frame = preferred_frame

    keep_columns = ["date"] + [column for column in CLIMATE_RENAME_MAP if column in frame.columns]
    if "date" not in frame.columns or len(keep_columns) == 1:
        return pd.DataFrame(columns=["date"] + list(CLIMATE_RENAME_MAP.values()))

    climate = frame[keep_columns].copy().rename(columns=CLIMATE_RENAME_MAP)
    climate["date"] = convert_to_month_start(climate["date"])
    for column in climate.columns:
        if column != "date":
            climate[column] = pd.to_numeric(climate[column], errors="coerce")
    climate = climate.dropna(subset=["date"]).drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)
    return climate


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
    exchange_rate = load_monthly_series(
        "macro_controls_cleaned.csv",
        date_column="date",
        value_column="cop_usd_exchange_rate",
        output_column=CONFIG["series"]["exchange_rate"],
    )
    oil_price = load_monthly_series(
        "macro_controls_cleaned.csv",
        date_column="date",
        value_column="brent_oil_usd_bbl",
        output_column=CONFIG["series"]["oil_price"],
    )
    climate = load_latest_monthly_climate_series()

    merged = build_analysis_dataset(domestic, international, eu, join_columns=["date"])
    if not exchange_rate.empty:
        merged = merged.merge(exchange_rate, on="date", how="outer")
    if not oil_price.empty:
        merged = merged.merge(oil_price, on="date", how="outer")
    if not climate.empty:
        merged = merged.merge(climate, on="date", how="outer")
    merged = finalize_analysis_columns(
        merged,
        log_columns=[
            CONFIG["series"]["domestic_price"],
            CONFIG["series"]["international_price"],
            CONFIG["series"]["eu_price"],
            CONFIG["series"]["exchange_rate"],
            CONFIG["series"]["oil_price"],
        ],
    )

    output_path = ROOT / PATHS["data_processed_analysis_ready"] / "merged_cocoa_price_panel.csv"
    write_dataframe(merged, output_path)
    log_dataframe_shape(logger, "merged_cocoa_price_panel", merged)


if __name__ == "__main__":
    main()
