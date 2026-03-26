"""Table export helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.utils.file_utils import write_dataframe


def export_dataframe_table(dataframe: pd.DataFrame, output_path: str | Path, index: bool = False) -> Path:
    """Export a dataframe using the shared project writer."""
    return write_dataframe(dataframe, output_path, index=index)
