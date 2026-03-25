"""Table export helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.utils.file_utils import ensure_directory


def export_dataframe_table(dataframe: pd.DataFrame, output_path: str | Path, index: bool = False) -> Path:
    """Export a dataframe to CSV or Excel."""
    path = Path(output_path)
    ensure_directory(path.parent)
    if path.suffix == ".csv":
        dataframe.to_csv(path, index=index)
    elif path.suffix == ".xlsx":
        dataframe.to_excel(path, index=index)
    else:
        raise ValueError(f"Unsupported table format: {path.suffix}")
    return path

