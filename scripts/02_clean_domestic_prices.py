"""Clean Colombian domestic cocoa price files."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_collection.download_domestic_cocoa import extract_agronet_weekly_cacao_series
from src.data_collection.import_sipsa import clean_sipsa_columns, load_sipsa_prices, select_cocoa_rows
from src.data_collection.load_local_files import list_raw_files
from src.data_processing.clean_colombia_prices import clean_colombia_price_columns, normalize_colombia_units
from src.utils.file_utils import load_yaml, write_dataframe
from src.utils.logging_utils import get_project_logger, log_dataframe_shape

PATHS = load_yaml(ROOT / "config" / "paths.yaml")
SOURCE_CONFIG = load_yaml(ROOT / "config" / "domestic_market_sources.yaml")


def load_agronet_raw_pages(raw_directory: Path, logger) -> pd.DataFrame:
    """Load and deduplicate AgroNet cacao weekly pages saved as raw HTML."""
    html_files = sorted(raw_directory.glob("*_agronet_cacao_weekly_raw.html"))
    frames: list[pd.DataFrame] = []
    agronet_config = SOURCE_CONFIG["colombia_domestic_prices"]["agronet"]

    for html_file in html_files:
        try:
            html_text = html_file.read_text(encoding="utf-8")
            frame = extract_agronet_weekly_cacao_series(
                html_text,
                source_url=agronet_config["weekly_page_url"],
                source_name=agronet_config["source_name"],
                source_dataset=agronet_config["dataset_name"],
            )
            frame["source_file"] = html_file.name
            frames.append(frame)
        except Exception as error:  # pragma: no cover - defensive logging for messy raw inputs
            logger.warning("Skipping %s because %s", html_file.name, error)

    if not frames:
        return pd.DataFrame()

    cleaned = pd.concat(frames, ignore_index=True)
    cleaned = cleaned.sort_values(["date", "source_file"]).drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)
    return cleaned


def main() -> None:
    """Load, standardize, and store Colombian price inputs."""
    logger = get_project_logger("02_clean_domestic_prices", ROOT / PATHS["output_logs"])
    raw_directory = ROOT / PATHS["raw_colombia"]
    agronet_cleaned = load_agronet_raw_pages(raw_directory, logger)

    if not agronet_cleaned.empty:
        cleaned = normalize_colombia_units(agronet_cleaned, value_column="price", unit_column="unit")
        output_path = ROOT / PATHS["data_interim_cleaned"] / "colombia_cocoa_prices_cleaned.csv"
        write_dataframe(cleaned, output_path)
        log_dataframe_shape(logger, "colombia_cocoa_prices_cleaned", cleaned)
        return

    raw_files = list_raw_files(raw_directory)
    column_map = {
        "fecha": "date",
        "producto": "product_name",
        "articulo": "product_name",
        "plaza": "market",
        "mercado": "market",
        "precio": "price",
        "unidad": "unit",
    }
    frames = []

    for raw_file in raw_files:
        try:
            frame = load_sipsa_prices(raw_file)
            frame = clean_sipsa_columns(frame)
            frame = clean_colombia_price_columns(frame, column_map)
            frame = select_cocoa_rows(frame, product_column="product_name")
            frame = normalize_colombia_units(frame)
            frame["source_file"] = raw_file.name
            frames.append(frame)
        except Exception as error:  # pragma: no cover - defensive logging for messy raw inputs
            logger.warning("Skipping %s because %s", raw_file.name, error)

    if frames:
        cleaned = pd.concat(frames, ignore_index=True)
    else:
        cleaned = pd.DataFrame(columns=["date", "product_name", "market", "price", "unit", "source_file"])

    output_path = ROOT / PATHS["data_interim_cleaned"] / "colombia_cocoa_prices_cleaned.csv"
    write_dataframe(cleaned, output_path)
    log_dataframe_shape(logger, "colombia_cocoa_prices_cleaned", cleaned)


if __name__ == "__main__":
    main()
