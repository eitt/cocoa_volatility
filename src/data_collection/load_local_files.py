"""Local file discovery and tabular loading helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def list_raw_files(raw_directory: str | Path, patterns: tuple[str, ...] = ("*.csv", "*.xlsx", "*.parquet")) -> list[Path]:
    """List tabular files in a raw-data directory."""
    directory = Path(raw_directory)
    files: list[Path] = []
    for pattern in patterns:
        files.extend(sorted(directory.glob(pattern)))
    return files


def load_tabular_file(file_path: str | Path, **kwargs) -> pd.DataFrame:
    """Load a CSV, Excel, or Parquet file based on its suffix."""
    path = Path(file_path)
    if path.suffix == ".csv":
        return pd.read_csv(path, **kwargs)
    if path.suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path, **kwargs)
    if path.suffix == ".parquet":
        return pd.read_parquet(path, **kwargs)
    raise ValueError(f"Unsupported file format: {path.suffix}")


def build_file_registry(source_name: str, raw_directory: str | Path) -> pd.DataFrame:
    """Create a file-level registry for a source directory."""
    records = [
        {"source_name": source_name, "file_name": path.name, "file_path": str(path)}
        for path in list_raw_files(raw_directory)
    ]
    return pd.DataFrame(records)

