"""Lightweight plotting helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
import numpy as np
import pandas as pd

PROJECT_PALETTE = [
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#009E73",  # bluish green
    "#0072B2",  # blue
    "#D55E00",  # vermillion
    "#CC79A7",  # reddish purple
    "#F0E442",  # yellow
    "#000000",  # black
]
PROJECT_DIVERGING_CMAP = LinearSegmentedColormap.from_list(
    "project_diverging",
    ["#D55E00", "#f8fafc", "#0072B2"],
    N=256,
)
PROJECT_AVAILABILITY_CMAP = ListedColormap(["#e5e7eb", "#009E73"])


def build_color_map(value_columns: list[str]) -> dict[str, str]:
    """Assign a stable project color to each plotted series."""
    return {
        column: PROJECT_PALETTE[index % len(PROJECT_PALETTE)]
        for index, column in enumerate(value_columns)
    }


def split_legend_columns(legend_lines: list[str], legend_columns: int) -> list[list[str]]:
    """Split legend lines into balanced columns for a full-width footer."""
    if not legend_lines:
        return []

    effective_columns = max(1, min(legend_columns, len(legend_lines)))
    row_count = int(np.ceil(len(legend_lines) / effective_columns))
    return [
        legend_lines[start_index : start_index + row_count]
        for start_index in range(0, len(legend_lines), row_count)
    ]


def plot_time_series(
    dataframe: pd.DataFrame,
    date_column: str,
    value_columns: list[str],
    title: str,
    label_map: dict[str, str] | None = None,
    y_label: str | None = None,
    color_map: dict[str, str] | None = None,
):
    """Create a simple line plot for selected series."""
    effective_color_map = color_map or build_color_map(value_columns)
    fig, ax = plt.subplots(figsize=(10, 5))
    for column in value_columns:
        if column in dataframe.columns:
            ax.plot(
                dataframe[date_column],
                dataframe[column],
                label=(label_map or {}).get(column, column),
                color=effective_color_map.get(column),
                linewidth=2,
            )
    ax.set_title(title)
    if y_label:
        ax.set_ylabel(y_label)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.legend(frameon=False)
    fig.tight_layout()
    return fig


def plot_time_series_panels(
    dataframe: pd.DataFrame,
    date_column: str,
    value_columns: list[str],
    title: str,
    label_map: dict[str, str] | None = None,
    ylabels: dict[str, str] | None = None,
    color_map: dict[str, str] | None = None,
):
    """Create stacked line charts so variables with different units remain readable."""
    available = [column for column in value_columns if column in dataframe.columns]
    effective_color_map = color_map or build_color_map(available)
    if not available:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.set_title(title)
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        ax.axis("off")
        fig.tight_layout()
        return fig

    fig, axes = plt.subplots(len(available), 1, figsize=(12, 2.8 * len(available)), sharex=True)
    if len(available) == 1:
        axes = [axes]

    for axis, column in zip(axes, available):
        axis.plot(
            dataframe[date_column],
            dataframe[column],
            linewidth=2,
            color=effective_color_map.get(column, PROJECT_PALETTE[0]),
        )
        axis.set_title((label_map or {}).get(column, column), loc="left")
        if ylabels and column in ylabels:
            axis.set_ylabel(ylabels[column])
        axis.grid(True, alpha=0.3, linestyle="--")

    axes[-1].set_xlabel("Date")
    fig.suptitle(title)
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    return fig


def plot_heatmap(
    matrix: pd.DataFrame,
    title: str,
    cmap=PROJECT_DIVERGING_CMAP,
    value_format: str = ".2f",
    display_label_map: dict[str, str] | None = None,
    legend_lines: list[str] | None = None,
    legend_columns: int = 1,
    vmin: float | None = None,
    vmax: float | None = None,
    neutral_text_threshold: float = 0.2,
):
    """Create a simple annotated heatmap from a matrix dataframe."""
    if matrix.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.set_title(title)
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        ax.axis("off")
        fig.tight_layout()
        return fig

    values = matrix.to_numpy(dtype=float)
    fig_width = max(6, 1.2 * len(matrix.columns))
    fig_height = max(4, 0.9 * len(matrix.index))
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    image = ax.imshow(values, cmap=cmap, aspect="auto", vmin=vmin, vmax=vmax)

    ax.set_xticks(np.arange(len(matrix.columns)))
    ax.set_xticklabels(
        [(display_label_map or {}).get(column, column) for column in matrix.columns],
        rotation=45,
        ha="right",
    )
    ax.set_yticks(np.arange(len(matrix.index)))
    ax.set_yticklabels([(display_label_map or {}).get(index, index) for index in matrix.index])
    ax.set_title(title)

    for row_index in range(values.shape[0]):
        for column_index in range(values.shape[1]):
            value = values[row_index, column_index]
            if np.isnan(value):
                continue
            if abs(value) <= neutral_text_threshold:
                text_color = "black"
            else:
                rgba = image.cmap(image.norm(value))
                luminance = 0.2126 * rgba[0] + 0.7152 * rgba[1] + 0.0722 * rgba[2]
                text_color = "white" if luminance < 0.55 else "black"
            ax.text(
                column_index,
                row_index,
                format(value, value_format),
                ha="center",
                va="center",
                color=text_color,
            )

    fig.colorbar(image, ax=ax, shrink=0.85)
    if legend_lines:
        legend_columns_data = split_legend_columns(legend_lines, legend_columns)
        footer_rows = max(len(column_entries) for column_entries in legend_columns_data)
        footer_height = min(0.32, 0.06 + 0.035 * footer_rows)
        fig.tight_layout(rect=[0, footer_height, 1, 1])

        footer_ax = fig.add_axes([0.035, 0.015, 0.93, max(0.06, footer_height - 0.025)])
        footer_ax.set_axis_off()
        footer_ax.patch.set_visible(True)
        footer_ax.patch.set_facecolor("white")
        footer_ax.patch.set_edgecolor("#cbd5e1")
        footer_ax.patch.set_linewidth(0.8)

        column_width = 1.0 / len(legend_columns_data)
        for column_index, column_entries in enumerate(legend_columns_data):
            footer_ax.text(
                column_index * column_width + 0.02 * column_width,
                0.5,
                "\n".join(column_entries),
                ha="left",
                va="center",
                fontsize=8,
                family="monospace",
                transform=footer_ax.transAxes,
            )
    else:
        fig.tight_layout()
    return fig


def plot_stl_decomposition(
    series: pd.Series,
    title: str,
    y_label: str | None = None,
):
    """Plot an STL decomposition result with the project palette."""
    fig, axes = plt.subplots(4, 1, figsize=(12, 9), sharex=True)
    components = [
        ("Observed", series, PROJECT_PALETTE[0]),
        ("Trend", series.attrs["trend"], PROJECT_PALETTE[3]),
        ("Seasonal", series.attrs["seasonal"], PROJECT_PALETTE[2]),
        ("Remainder", series.attrs["resid"], PROJECT_PALETTE[4]),
    ]

    for axis, (label, values, color) in zip(axes, components):
        axis.plot(series.index, values, color=color, linewidth=2)
        axis.set_title(label, loc="left")
        axis.grid(True, alpha=0.3, linestyle="--")

    if y_label:
        axes[0].set_ylabel(y_label)
    axes[-1].set_xlabel("Date")
    fig.suptitle(title)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    return fig


def plot_data_availability(
    dataframe: pd.DataFrame,
    date_column: str,
    value_columns: list[str],
    title: str,
    label_map: dict[str, str] | None = None,
):
    """Visualize non-missing data availability over time."""
    available = [column for column in value_columns if column in dataframe.columns]
    if date_column not in dataframe.columns or not available:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.set_title(title)
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        ax.axis("off")
        fig.tight_layout()
        return fig

    frame = dataframe[[date_column] + available].copy()
    frame[date_column] = pd.to_datetime(frame[date_column], errors="coerce")
    availability = frame[available].notna().astype(int).transpose()

    fig, ax = plt.subplots(figsize=(12, max(3, 0.7 * len(available))))
    image = ax.imshow(
        availability.to_numpy(),
        aspect="auto",
        cmap=PROJECT_AVAILABILITY_CMAP,
        interpolation="nearest",
    )
    ax.set_yticks(np.arange(len(available)))
    ax.set_yticklabels([(label_map or {}).get(column, column) for column in available])

    tick_count = min(12, len(frame))
    tick_positions = np.linspace(0, len(frame) - 1, tick_count, dtype=int) if len(frame) else []
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(
        [frame.iloc[position][date_column].strftime("%Y-%m") for position in tick_positions],
        rotation=45,
        ha="right",
    )
    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel("Series")
    fig.colorbar(image, ax=ax, ticks=[0, 1], shrink=0.7)
    fig.tight_layout()
    return fig


def save_figure(fig, output_path: str | Path, dpi: int = 300) -> Path:
    """Persist a Matplotlib figure to disk."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    return path
