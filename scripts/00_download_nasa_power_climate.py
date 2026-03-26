"""Download NASA POWER climate series for configured Colombian locations."""

from __future__ import annotations

from datetime import date, timedelta
import json
from pathlib import Path
import re
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_collection.download_nasa_power import (
    build_nasa_power_point_url,
    fetch_nasa_power_point_json,
    normalize_nasa_power_payload,
    pivot_nasa_power_long_to_wide,
)
from src.utils.file_utils import ensure_directory, load_yaml, write_dataframe
from src.utils.logging_utils import get_project_logger, log_dataframe_shape

PATHS = load_yaml(ROOT / "config" / "paths.yaml")
PROJECT_CONFIG = load_yaml(ROOT / "config" / "project_config.yaml")
CLIMATE_CONFIG = load_yaml(ROOT / "config" / "climate_locations.yaml")


def slugify(text: str) -> str:
    """Convert a location label into a stable ASCII-friendly slug."""
    normalized = re.sub(r"[^a-z0-9]+", "_", text.lower())
    return normalized.strip("_")


def resolve_run_date() -> date:
    """Use the configured project run date when available."""
    configured_run_date = PROJECT_CONFIG.get("project", {}).get("run_date")
    if configured_run_date:
        return date.fromisoformat(configured_run_date)
    return date.today()


def resolve_request_window(frequency: str, configured_window: dict[str, str | None], run_date: date) -> tuple[str, str]:
    """Resolve open-ended start and end dates for NASA POWER requests."""
    start = configured_window.get("start")
    end = configured_window.get("end")
    if not start:
        raise ValueError(f"Missing start date for {frequency} NASA POWER download.")

    if end:
        return str(start), str(end)

    if frequency == "monthly":
        return str(start), str(run_date.year - 1)
    if frequency == "daily":
        return str(start), (run_date - timedelta(days=1)).strftime("%Y%m%d")
    raise ValueError(f"Unsupported frequency: {frequency}")


def write_json(payload: dict, output_path: Path) -> Path:
    """Write a JSON payload to disk with UTF-8 encoding."""
    ensure_directory(output_path.parent)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def main() -> None:
    """Download configured NASA POWER climate series and save normalized outputs."""
    logger = get_project_logger("00_download_nasa_power_climate", ROOT / PATHS["output_logs"])
    run_date = resolve_run_date()
    raw_climate_dir = ROOT / PATHS["raw_climate"]
    harmonized_dir = ROOT / PATHS["data_interim_harmonized"]
    raw_metadata_dir = ROOT / PATHS["raw_metadata"]
    parameters = PROJECT_CONFIG.get("climate_extension", {}).get("nasa_power_parameters", [])
    locations = CLIMATE_CONFIG.get("locations", [])
    community = CLIMATE_CONFIG.get("nasa_power", {}).get("community", "AG")

    if not parameters:
        raise ValueError("No NASA POWER parameters were configured in project_config.yaml.")
    if not locations:
        raise ValueError("No climate locations were configured in climate_locations.yaml.")

    manifest_records: list[dict[str, object]] = []
    combined_long_frames: list[pd.DataFrame] = []
    combined_wide_frames: list[pd.DataFrame] = []

    for location in locations:
        location_name = location.get("location_name", location.get("location_id", "unknown_location"))
        location_slug = slugify(location.get("location_id", location_name))

        for frequency in ("monthly", "daily"):
            request_window = CLIMATE_CONFIG.get("downloads", {}).get(frequency, {})
            start, end = resolve_request_window(frequency, request_window, run_date)
            url = build_nasa_power_point_url(
                frequency=frequency,
                parameters=parameters,
                latitude=float(location["latitude"]),
                longitude=float(location["longitude"]),
                start=start,
                end=end,
                community=community,
            )
            logger.info("Requesting %s NASA POWER data for %s", frequency, location_name)
            payload = fetch_nasa_power_point_json(url)

            raw_json_path = raw_climate_dir / f"{run_date.isoformat()}_{location_slug}_{frequency}_nasa_power_raw.json"
            write_json(payload, raw_json_path)

            location_metadata = {
                "location_id": location.get("location_id"),
                "location_name": location_name,
                "municipality": location.get("municipality"),
                "department": location.get("department"),
                "country": location.get("country"),
                "coordinate_source": location.get("coordinate_source"),
                "coordinate_source_url": location.get("coordinate_source_url"),
                "download_date": run_date.isoformat(),
                "source_institution": "NASA POWER",
                "source_dataset": "Temporal API point time series",
                "community": community,
            }
            long_df = normalize_nasa_power_payload(
                payload,
                frequency=frequency,
                location_metadata=location_metadata,
                source_url=url,
            )
            wide_df = pivot_nasa_power_long_to_wide(long_df)

            long_output_path = (
                harmonized_dir / f"{run_date.isoformat()}_{location_slug}_{frequency}_nasa_power_long.csv"
            )
            wide_output_path = (
                harmonized_dir / f"{run_date.isoformat()}_{location_slug}_{frequency}_nasa_power_wide.csv"
            )
            write_dataframe(long_df, long_output_path)
            write_dataframe(wide_df, wide_output_path)
            log_dataframe_shape(logger, f"{location_slug}_{frequency}_nasa_power_long", long_df)
            log_dataframe_shape(logger, f"{location_slug}_{frequency}_nasa_power_wide", wide_df)

            combined_long_frames.append(long_df)
            combined_wide_frames.append(wide_df)
            manifest_records.append(
                {
                    "download_date": run_date.isoformat(),
                    "location_id": location.get("location_id"),
                    "location_name": location_name,
                    "department": location.get("department"),
                    "frequency": frequency,
                    "request_start": start,
                    "request_end": end,
                    "parameter_count": len(parameters),
                    "parameters": ",".join(parameters),
                    "community": community,
                    "raw_json_file": raw_json_path.name,
                    "harmonized_long_file": long_output_path.name,
                    "harmonized_wide_file": wide_output_path.name,
                    "long_rows": len(long_df),
                    "wide_rows": len(wide_df),
                    "source_url": url,
                }
            )

    manifest = pd.DataFrame.from_records(manifest_records)
    manifest_output_path = raw_metadata_dir / f"{run_date.isoformat()}_nasa_power_download_manifest.csv"
    write_dataframe(manifest, manifest_output_path)
    logger.info("Wrote NASA POWER manifest to %s", manifest_output_path)

    combined_long = pd.concat(combined_long_frames, ignore_index=True) if combined_long_frames else pd.DataFrame()
    combined_wide = pd.concat(combined_wide_frames, ignore_index=True) if combined_wide_frames else pd.DataFrame()

    combined_long_path = harmonized_dir / f"{run_date.isoformat()}_nasa_power_all_locations_long.csv"
    combined_wide_path = harmonized_dir / f"{run_date.isoformat()}_nasa_power_all_locations_wide.csv"
    write_dataframe(combined_long, combined_long_path)
    write_dataframe(combined_wide, combined_wide_path)
    log_dataframe_shape(logger, "nasa_power_all_locations_long", combined_long)
    log_dataframe_shape(logger, "nasa_power_all_locations_wide", combined_wide)


if __name__ == "__main__":
    main()
