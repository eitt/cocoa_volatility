"""Download EU downstream price indicators from Eurostat."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_collection.download_eurostat import (
    build_eurostat_api_url,
    fetch_eurostat_json,
    normalize_eurostat_filtered_payload,
    write_eurostat_json,
)
from src.utils.file_utils import load_yaml, write_dataframe
from src.utils.logging_utils import get_project_logger, log_dataframe_shape

PATHS = load_yaml(ROOT / "config" / "paths.yaml")
PROJECT_CONFIG = load_yaml(ROOT / "config" / "project_config.yaml")
SOURCE_CONFIG = load_yaml(ROOT / "config" / "eu_market_sources.yaml")


def resolve_run_date() -> date:
    """Use the configured project run date when available."""
    configured_run_date = PROJECT_CONFIG.get("project", {}).get("run_date")
    if configured_run_date:
        return date.fromisoformat(configured_run_date)
    return date.today()


def main() -> None:
    """Download the official Eurostat EU chocolate price series."""
    logger = get_project_logger("00_download_eu_prices", ROOT / PATHS["output_logs"])
    run_date = resolve_run_date()
    raw_dir = ROOT / PATHS["raw_eu"]
    harmonized_dir = ROOT / PATHS["data_interim_harmonized"]
    metadata_dir = ROOT / PATHS["raw_metadata"]

    eurostat_config = SOURCE_CONFIG["eu_market_prices"]["eurostat"]
    dataset_code = eurostat_config["dataset_code"]
    manifest_records: list[dict[str, object]] = []

    for series_config in eurostat_config.get("series", []):
        url = build_eurostat_api_url(
            dataset_code=dataset_code,
            geo=series_config["geo"],
            coicop=series_config["coicop"],
            unit=eurostat_config["unit"],
            frequency=eurostat_config["frequency"],
        )
        logger.info(
            "Requesting Eurostat HICP series for geo=%s and coicop=%s",
            series_config["geo"],
            series_config["coicop"],
        )
        payload = fetch_eurostat_json(url)

        raw_path = raw_dir / f"{run_date.isoformat()}_eurostat_{series_config['geo']}_{series_config['coicop']}_raw.json"
        write_eurostat_json(payload, raw_path)

        normalized = normalize_eurostat_filtered_payload(
            payload,
            value_column=series_config["value_column"],
            series_name=series_config["series_name"],
            source_dataset=eurostat_config["dataset_name"],
            source_url=url,
        )
        output_path = harmonized_dir / f"{run_date.isoformat()}_eurostat_{series_config['output_slug']}_monthly.csv"
        write_dataframe(normalized, output_path)
        log_dataframe_shape(logger, f"eurostat_{series_config['output_slug']}_monthly", normalized)

        manifest_records.append(
            {
                "download_date": run_date.isoformat(),
                "source_institution": eurostat_config["source_name"],
                "source_dataset": eurostat_config["dataset_name"],
                "dataset_code": dataset_code,
                "series_name": series_config["series_name"],
                "geo": series_config["geo"],
                "coicop": series_config["coicop"],
                "request_start": normalized["date"].min().date().isoformat() if not normalized.empty else None,
                "request_end": normalized["date"].max().date().isoformat() if not normalized.empty else None,
                "raw_json_file": raw_path.name,
                "harmonized_file": output_path.name,
                "rows": len(normalized),
                "source_url": url,
                "api_updated": payload.get("updated"),
            }
        )

    manifest = pd.DataFrame.from_records(manifest_records)
    manifest_path = metadata_dir / f"{run_date.isoformat()}_eu_price_download_manifest.csv"
    write_dataframe(manifest, manifest_path)
    logger.info("Wrote EU price download manifest to %s", manifest_path)


if __name__ == "__main__":
    main()
