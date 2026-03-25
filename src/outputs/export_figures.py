"""Figure export helpers."""

from __future__ import annotations

from pathlib import Path

from src.utils.file_utils import ensure_directory


def export_matplotlib_figure(fig, output_path: str | Path, dpi: int = 300) -> Path:
    """Write a Matplotlib figure to disk."""
    path = Path(output_path)
    ensure_directory(path.parent)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    return path

