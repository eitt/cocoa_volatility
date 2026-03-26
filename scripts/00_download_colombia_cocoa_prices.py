"""Download Colombian domestic cocoa price series from official sources."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_collection.download_domestic_cocoa import (
    aggregate_agronet_weekly_to_monthly,
    extract_agronet_weekly_cacao_series,
    fetch_text,
    write_text,
)
from src.utils.file_utils import load_yaml, write_dataframe
from src.utils.logging_utils import get_project_logger, log_dataframe_shape

PATHS = load_yaml(ROOT / "config" / "paths.yaml")
PROJECT_CONFIG = load_yaml(ROOT / "config" / "project_config.yaml")
SOURCE_CONFIG = load_yaml(ROOT / "config" / "domestic_market_sources.yaml")


def resolve_run_date() -> date:
    """Use the configured project run date when available."""
    configured_run_date = PROJECT_CONFIG.get("project", {}).get("run_date")
    if configured_run_date:
        return date.fromisoformat(configured_run_date)
    return date.today()


def main() -> None:
    """Download the official AgroNet weekly cacao reference table."""
    logger = get_project_logger("00_download_colombia_cocoa_prices", ROOT / PATHS["output_logs"])
    run_date = resolve_run_date()
    raw_dir = ROOT / PATHS["raw_colombia"]
    harmonized_dir = ROOT / PATHS["data_interim_harmonized"]
    metadata_dir = ROOT / PATHS["raw_metadata"]

    agronet_config = SOURCE_CONFIG["colombia_domestic_prices"]["agronet"]
    source_url = agronet_config["weekly_page_url"]

    logger.info("Requesting AgroNet weekly cacao reference page")
    html_text = fetch_text(source_url)
    raw_html_path = raw_dir / f"{run_date.isoformat()}_agronet_cacao_weekly_raw.html"
    write_text(html_text, raw_html_path)

    weekly = extract_agronet_weekly_cacao_series(
        html_text,
        source_url=source_url,
        source_name=agronet_config["source_name"],
        source_dataset=agronet_config["dataset_name"],
    )
    raw_weekly_csv_path = raw_dir / f"{run_date.isoformat()}_agronet_cacao_weekly_raw.csv"
    raw_weekly_json_path = raw_dir / f"{run_date.isoformat()}_agronet_cacao_weekly_raw.json"
    write_dataframe(weekly, raw_weekly_csv_path)

    weekly_path = harmonized_dir / f"{run_date.isoformat()}_agronet_cacao_weekly.csv"
    write_dataframe(weekly, weekly_path)
    log_dataframe_shape(logger, "agronet_cacao_weekly", weekly)

    monthly = aggregate_agronet_weekly_to_monthly(weekly)
    raw_monthly_csv_path = raw_dir / f"{run_date.isoformat()}_agronet_cacao_monthly_raw.csv"
    raw_monthly_json_path = raw_dir / f"{run_date.isoformat()}_agronet_cacao_monthly_raw.json"
    write_dataframe(monthly, raw_monthly_csv_path)

    monthly_path = harmonized_dir / f"{run_date.isoformat()}_agronet_cacao_monthly.csv"
    write_dataframe(monthly, monthly_path)
    log_dataframe_shape(logger, "agronet_cacao_monthly", monthly)

    manifest = pd.DataFrame.from_records(
        [
            {
                "download_date": run_date.isoformat(),
                "source_institution": agronet_config["source_name"],
                "source_dataset": agronet_config["dataset_name"],
                "frequency": "weekly",
                "request_start": weekly["week_start_date"].min().date().isoformat() if not weekly.empty else None,
                "request_end": weekly["date"].max().date().isoformat() if not weekly.empty else None,
                "raw_html_file": raw_html_path.name,
                "raw_csv_file": raw_weekly_csv_path.name,
                "raw_json_file": raw_weekly_json_path.name,
                "harmonized_file": weekly_path.name,
                "rows": len(weekly),
                "source_url": source_url,
            },
            {
                "download_date": run_date.isoformat(),
                "source_institution": agronet_config["source_name"],
                "source_dataset": agronet_config["dataset_name"],
                "frequency": "monthly",
                "request_start": monthly["date"].min().date().isoformat() if not monthly.empty else None,
                "request_end": monthly["date"].max().date().isoformat() if not monthly.empty else None,
                "raw_html_file": raw_html_path.name,
                "raw_csv_file": raw_monthly_csv_path.name,
                "raw_json_file": raw_monthly_json_path.name,
                "harmonized_file": monthly_path.name,
                "rows": len(monthly),
                "source_url": source_url,
            },
        ]
    )
    manifest_path = metadata_dir / f"{run_date.isoformat()}_colombia_cocoa_download_manifest.csv"
    write_dataframe(manifest, manifest_path)
    logger.info("Wrote domestic cocoa download manifest to %s", manifest_path)


if __name__ == "__main__":
    main()
