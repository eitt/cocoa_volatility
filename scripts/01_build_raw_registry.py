"""Build a registry of raw files available for the project."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_collection.load_local_files import build_file_registry
from src.utils.file_utils import load_yaml, write_dataframe
from src.utils.logging_utils import get_project_logger

PATHS = load_yaml(ROOT / "config" / "paths.yaml")


def main() -> None:
    """Scan raw-data folders and write a file registry."""
    logger = get_project_logger("01_build_raw_registry", ROOT / PATHS["output_logs"])
    source_directories = {
        "colombia": ROOT / PATHS["raw_colombia"],
        "international": ROOT / PATHS["raw_international"],
        "eu": ROOT / PATHS["raw_eu"],
        "trade": ROOT / PATHS["raw_trade"],
        "climate": ROOT / PATHS["raw_climate"],
    }

    registries = []
    for source_name, directory in source_directories.items():
        registry = build_file_registry(source_name, directory)
        logger.info("Found %s files for %s", len(registry), source_name)
        registries.append(registry)

    combined = pd.concat(registries, ignore_index=True) if registries else pd.DataFrame()
    output_path = ROOT / PATHS["raw_metadata"] / "raw_file_registry.csv"
    write_dataframe(combined, output_path)
    logger.info("Wrote raw registry to %s", output_path)


if __name__ == "__main__":
    main()
