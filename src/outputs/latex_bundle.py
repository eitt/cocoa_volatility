"""Helpers for building a self-contained LaTeX manuscript bundle."""

from __future__ import annotations

from pathlib import Path
import shutil

import pandas as pd

from src.utils.file_utils import ensure_directory


def copy_tree_files(source_dir: Path, destination_dir: Path) -> list[dict[str, object]]:
    """Copy all files from a source tree into a destination tree."""
    records: list[dict[str, object]] = []
    ensure_directory(destination_dir)

    for source_path in sorted(source_dir.rglob("*")):
        if not source_path.is_file():
            continue
        relative_path = source_path.relative_to(source_dir)
        destination_path = destination_dir / relative_path
        ensure_directory(destination_path.parent)
        shutil.copy2(source_path, destination_path)
        records.append(
            {
                "source_path": str(source_path),
                "destination_path": str(destination_path),
                "size_bytes": source_path.stat().st_size,
            }
        )
    return records


def copy_file(source_path: Path, destination_path: Path) -> dict[str, object]:
    """Copy one file into the manuscript bundle."""
    ensure_directory(destination_path.parent)
    shutil.copy2(source_path, destination_path)
    return {
        "source_path": str(source_path),
        "destination_path": str(destination_path),
        "size_bytes": source_path.stat().st_size,
    }


def build_latex_bundle_manifest(records: list[dict[str, object]]) -> pd.DataFrame:
    """Convert copied-file records into a manifest dataframe."""
    return pd.DataFrame.from_records(records).sort_values(
        ["destination_path", "source_path"]
    ).reset_index(drop=True)
