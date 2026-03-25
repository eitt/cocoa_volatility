"""Build a manifest of generated outputs."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.file_utils import load_yaml, write_dataframe
from src.utils.logging_utils import get_project_logger

PATHS = load_yaml(ROOT / "config" / "paths.yaml")


def build_manifest(paths: list[Path]) -> pd.DataFrame:
    """Build a manifest for existing files under selected directories."""
    records = []
    for base_path in paths:
        for file_path in sorted(base_path.rglob("*")):
            if file_path.is_file():
                records.append(
                    {
                        "relative_path": str(file_path.relative_to(ROOT)),
                        "size_bytes": file_path.stat().st_size,
                    }
                )
    return pd.DataFrame(records)


def main() -> None:
    """Export a manifest of processed data and output artifacts."""
    logger = get_project_logger("11_export_results", ROOT / PATHS["output_logs"])
    manifest = build_manifest(
        [
            ROOT / PATHS["data_processed_analysis_ready"],
            ROOT / PATHS["data_processed_final_series"],
            ROOT / PATHS["output_tables"],
            ROOT / PATHS["output_figures"],
            ROOT / PATHS["output_appendix"],
        ]
    )
    output_path = ROOT / PATHS["output_appendix"] / "export_manifest.csv"
    write_dataframe(manifest, output_path)
    logger.info("Wrote export manifest to %s", output_path)


if __name__ == "__main__":
    main()
