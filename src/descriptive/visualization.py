"""Lightweight plotting helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_time_series(
    dataframe: pd.DataFrame,
    date_column: str,
    value_columns: list[str],
    title: str,
):
    """Create a simple line plot for selected series."""
    fig, ax = plt.subplots(figsize=(10, 5))
    for column in value_columns:
        if column in dataframe.columns:
            ax.plot(dataframe[date_column], dataframe[column], label=column)
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    return fig


def save_figure(fig, output_path: str | Path, dpi: int = 300) -> Path:
    """Persist a Matplotlib figure to disk."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    return path
