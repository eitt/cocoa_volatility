"""Model summary export helpers."""

from __future__ import annotations

from pathlib import Path

from src.utils.file_utils import ensure_directory


def export_text_summary(summary_text: str, output_path: str | Path) -> Path:
    """Write a text summary to disk."""
    path = Path(output_path)
    ensure_directory(path.parent)
    path.write_text(summary_text, encoding="utf-8")
    return path


def model_result_to_text(result) -> str:
    """Convert a statsmodels result object to a text summary."""
    return result.summary().as_text()
