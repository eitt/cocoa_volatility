"""Download macro control series for the cocoa volatility project."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_collection.download_macro_controls import (
    build_banrep_trm_url,
    fetch_json,
    fetch_text,
    normalize_banrep_trm_payload,
    parse_eia_brent_daily_history,
    parse_eia_brent_monthly_history,
    write_json_payload,
    write_text_payload,
)
from src.utils.file_utils import load_yaml, write_dataframe
from src.utils.logging_utils import get_project_logger, log_dataframe_shape

PATHS = load_yaml(ROOT / "config" / "paths.yaml")
PROJECT_CONFIG = load_yaml(ROOT / "config" / "project_config.yaml")
SOURCE_CONFIG = load_yaml(ROOT / "config" / "macro_control_sources.yaml")


def resolve_run_date() -> date:
    """Use the configured project run date when available."""
    configured_run_date = PROJECT_CONFIG.get("project", {}).get("run_date")
    if configured_run_date:
        return date.fromisoformat(configured_run_date)
    return date.today()


def main() -> None:
    """Download COP/USD and Brent oil control series."""
    logger = get_project_logger("00_download_macro_controls", ROOT / PATHS["output_logs"])
    run_date = resolve_run_date()
    raw_dir = ROOT / PATHS["raw_macro"]
    harmonized_dir = ROOT / PATHS["data_interim_harmonized"]
    metadata_dir = ROOT / PATHS["raw_metadata"]
    manifest_records: list[dict[str, object]] = []

    banrep_config = SOURCE_CONFIG["macro_controls"]["banco_republica"]
    trm_url = build_banrep_trm_url(
        series_id=banrep_config["series_id"],
        tipo_dato=banrep_config["tipo_dato"],
        cant_datos=banrep_config["cant_datos"],
        frecuencia_datos=banrep_config["frecuencia_datos"],
    )
    logger.info("Requesting Banco de la Republica TRM historical series")
    trm_payload = fetch_json(trm_url)
    trm_raw_json_path = raw_dir / f"{run_date.isoformat()}_banrep_trm_daily_raw.json"
    write_json_payload(trm_payload, trm_raw_json_path)
    trm_daily = normalize_banrep_trm_payload(trm_payload, source_url=trm_url)
    trm_raw_csv_path = raw_dir / f"{run_date.isoformat()}_banrep_trm_daily_raw.csv"
    trm_harmonized_path = harmonized_dir / f"{run_date.isoformat()}_banrep_trm_daily.csv"
    write_dataframe(trm_daily, trm_raw_csv_path)
    write_dataframe(trm_daily, trm_harmonized_path)
    log_dataframe_shape(logger, "banrep_trm_daily", trm_daily)
    manifest_records.append(
        {
            "download_date": run_date.isoformat(),
            "source_institution": banrep_config["source_name"],
            "source_dataset": banrep_config["dataset_name"],
            "series_name": "cop_usd_exchange_rate",
            "frequency": "daily",
            "request_start": trm_daily["date"].min().date().isoformat() if not trm_daily.empty else None,
            "request_end": trm_daily["date"].max().date().isoformat() if not trm_daily.empty else None,
            "raw_file": trm_raw_json_path.name,
            "raw_csv_file": trm_raw_csv_path.name,
            "harmonized_file": trm_harmonized_path.name,
            "rows": len(trm_daily),
            "source_url": trm_url,
        }
    )

    eia_config = SOURCE_CONFIG["macro_controls"]["eia"]
    for frequency, parser, url_suffix in (
        ("daily", parse_eia_brent_daily_history, "daily_url"),
        ("monthly", parse_eia_brent_monthly_history, "monthly_url"),
    ):
        source_url = eia_config[url_suffix]
        logger.info("Requesting EIA Brent oil %s history", frequency)
        html_text = fetch_text(source_url)
        raw_html_path = raw_dir / f"{run_date.isoformat()}_eia_brent_{frequency}_raw.html"
        write_text_payload(html_text, raw_html_path)

        normalized = parser(html_text, source_url=source_url)
        raw_csv_path = raw_dir / f"{run_date.isoformat()}_eia_brent_{frequency}_raw.csv"
        harmonized_path = harmonized_dir / f"{run_date.isoformat()}_eia_brent_{frequency}.csv"
        write_dataframe(normalized, raw_csv_path)
        write_dataframe(normalized, harmonized_path)
        log_dataframe_shape(logger, f"eia_brent_{frequency}", normalized)

        manifest_records.append(
            {
                "download_date": run_date.isoformat(),
                "source_institution": eia_config["source_name"],
                "source_dataset": eia_config["dataset_name"],
                "series_name": "brent_oil_usd_bbl",
                "frequency": frequency,
                "request_start": normalized["date"].min().date().isoformat() if not normalized.empty else None,
                "request_end": normalized["date"].max().date().isoformat() if not normalized.empty else None,
                "raw_file": raw_html_path.name,
                "raw_csv_file": raw_csv_path.name,
                "harmonized_file": harmonized_path.name,
                "rows": len(normalized),
                "source_url": source_url,
            }
        )

    manifest = pd.DataFrame.from_records(manifest_records)
    manifest_path = metadata_dir / f"{run_date.isoformat()}_macro_controls_download_manifest.csv"
    write_dataframe(manifest, manifest_path)
    logger.info("Wrote macro controls download manifest to %s", manifest_path)


if __name__ == "__main__":
    main()
