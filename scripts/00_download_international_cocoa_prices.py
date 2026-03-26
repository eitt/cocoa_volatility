"""Download international cocoa benchmark and futures series."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_collection.download_international_cocoa import (
    build_yahoo_chart_url,
    fetch_binary,
    fetch_json,
    write_binary,
    write_json,
)
from src.data_collection.import_world_bank import extract_world_bank_cocoa_monthly_series
from src.data_collection.import_yahoo_finance import normalize_yahoo_chart_payload
from src.utils.file_utils import load_yaml, write_dataframe
from src.utils.logging_utils import get_project_logger, log_dataframe_shape

PATHS = load_yaml(ROOT / "config" / "paths.yaml")
PROJECT_CONFIG = load_yaml(ROOT / "config" / "project_config.yaml")
SOURCE_CONFIG = load_yaml(ROOT / "config" / "international_market_sources.yaml")


def resolve_run_date() -> date:
    """Use the configured project run date when available."""
    configured_run_date = PROJECT_CONFIG.get("project", {}).get("run_date")
    if configured_run_date:
        return date.fromisoformat(configured_run_date)
    return date.today()


def main() -> None:
    """Download Yahoo Finance and World Bank cocoa series."""
    logger = get_project_logger("00_download_international_cocoa_prices", ROOT / PATHS["output_logs"])
    run_date = resolve_run_date()
    raw_dir = ROOT / PATHS["raw_international"]
    harmonized_dir = ROOT / PATHS["data_interim_harmonized"]
    metadata_dir = ROOT / PATHS["raw_metadata"]

    yahoo_config = SOURCE_CONFIG["international_cocoa"]["yahoo_finance"]
    world_bank_config = SOURCE_CONFIG["international_cocoa"]["world_bank"]

    manifest_records: list[dict[str, object]] = []

    symbol = yahoo_config["symbol"]
    start_date = yahoo_config["start_date"]
    end_date = run_date.isoformat()

    for interval in yahoo_config.get("intervals", []):
        frequency = "daily" if interval == "1d" else "monthly"
        url = build_yahoo_chart_url(symbol=symbol, start_date=start_date, end_date=end_date, interval=interval)
        logger.info("Requesting Yahoo Finance %s cocoa series for %s", frequency, symbol)
        payload = fetch_json(url)

        raw_json_path = raw_dir / f"{run_date.isoformat()}_yahoo_finance_{symbol.replace('=','_')}_{frequency}_raw.json"
        write_json(payload, raw_json_path)

        normalized = normalize_yahoo_chart_payload(
            payload,
            frequency=frequency,
            symbol=symbol,
            source_url=url,
            source_dataset=yahoo_config["dataset_name"],
        )
        output_path = harmonized_dir / f"{run_date.isoformat()}_yahoo_finance_{symbol.replace('=','_')}_{frequency}.csv"
        write_dataframe(normalized, output_path)
        log_dataframe_shape(logger, f"yahoo_finance_{symbol}_{frequency}", normalized)

        manifest_records.append(
            {
                "download_date": run_date.isoformat(),
                "source_institution": yahoo_config["source_name"],
                "source_dataset": yahoo_config["dataset_name"],
                "symbol": symbol,
                "frequency": frequency,
                "request_start": start_date,
                "request_end": end_date,
                "raw_file": raw_json_path.name,
                "harmonized_file": output_path.name,
                "rows": len(normalized),
                "source_url": url,
            }
        )

    world_bank_url = world_bank_config["monthly_workbook_url"]
    logger.info("Requesting World Bank monthly cocoa benchmark workbook")
    workbook_bytes = fetch_binary(world_bank_url)
    workbook_path = raw_dir / f"{run_date.isoformat()}_world_bank_pink_sheet_monthly_raw.xlsx"
    write_binary(workbook_bytes, workbook_path)

    world_bank_series = extract_world_bank_cocoa_monthly_series(str(workbook_path))
    world_bank_series["source_url"] = world_bank_url
    world_bank_output_path = harmonized_dir / f"{run_date.isoformat()}_world_bank_cocoa_monthly.csv"
    write_dataframe(world_bank_series, world_bank_output_path)
    log_dataframe_shape(logger, "world_bank_cocoa_monthly", world_bank_series)

    manifest_records.append(
        {
            "download_date": run_date.isoformat(),
            "source_institution": world_bank_config["source_name"],
            "source_dataset": world_bank_config["dataset_name"],
            "symbol": None,
            "frequency": "monthly",
            "request_start": world_bank_series["date"].min().date().isoformat() if not world_bank_series.empty else None,
            "request_end": world_bank_series["date"].max().date().isoformat() if not world_bank_series.empty else None,
            "raw_file": workbook_path.name,
            "harmonized_file": world_bank_output_path.name,
            "rows": len(world_bank_series),
            "source_url": world_bank_url,
        }
    )

    manifest = pd.DataFrame.from_records(manifest_records)
    manifest_path = metadata_dir / f"{run_date.isoformat()}_international_cocoa_download_manifest.csv"
    write_dataframe(manifest, manifest_path)
    logger.info("Wrote international cocoa download manifest to %s", manifest_path)


if __name__ == "__main__":
    main()
