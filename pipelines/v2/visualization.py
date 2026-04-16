"""Plotting utilities for v2 report artifacts."""

from __future__ import annotations

from pathlib import Path

import matplotlib
import pandas as pd

from src.outputs.export_figures import export_matplotlib_figure


matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.style.use("seaborn-v0_8-whitegrid")


COLOR_MAP = {
    "primary": "#1b4965",
    "secondary": "#5fa8d3",
    "accent": "#ca6702",
    "danger": "#9b2226",
    "success": "#2a9d8f",
}


def _save_figure(fig, output_path: Path) -> Path:
    path = export_matplotlib_figure(fig, output_path)
    plt.close(fig)
    return path


def plot_monthly_event_totals(monthly: pd.DataFrame, output_path: Path) -> Path:
    """Plot monthly total events."""
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(monthly["month"], monthly["total_events"], color=COLOR_MAP["primary"], linewidth=2.2)
    ax.fill_between(monthly["month"], monthly["total_events"], color=COLOR_MAP["secondary"], alpha=0.25)
    ax.set_title("Monthly disaster-event totals")
    ax.set_xlabel("Month")
    ax.set_ylabel("Event count")
    return _save_figure(fig, output_path)


def plot_hazard_domain_mix(monthly: pd.DataFrame, output_path: Path) -> Path:
    """Plot monthly hazard-domain composition."""
    domain_columns = [
        ("geophysical_events", "Geophysical", "#8d99ae"),
        ("hydrometeorological_events", "Hydrometeorological", "#2a9d8f"),
        ("infrastructure_service_events", "Infrastructure and service disruption", "#e9c46a"),
        ("technological_anthropogenic_events", "Technological and anthropogenic", "#f4a261"),
        ("other_events", "Other or unclassified", "#6c757d"),
    ]
    available = [(column, label, color) for column, label, color in domain_columns if column in monthly.columns]

    fig, ax = plt.subplots(figsize=(10, 5.2))
    if available:
        values = [monthly[column] for column, _, _ in available]
        labels = [label for _, label, _ in available]
        colors = [color for _, _, color in available]
        ax.stackplot(monthly["month"], values, labels=labels, colors=colors, alpha=0.85)
        ax.legend(loc="upper left", ncol=2, frameon=False)
    else:
        ax.text(0.5, 0.5, "No hazard-domain data available", ha="center", va="center")
    ax.set_title("Monthly hazard-domain composition")
    ax.set_xlabel("Month")
    ax.set_ylabel("Event count")
    return _save_figure(fig, output_path)


def plot_top_municipalities(summary_df: pd.DataFrame, output_path: Path) -> Path:
    """Plot the municipalities with the largest event counts."""
    fig, ax = plt.subplots(figsize=(9, 5.5))
    plotting = summary_df.sort_values("event_count", ascending=True)
    ax.barh(plotting["municipality_en"], plotting["event_count"], color=COLOR_MAP["primary"])
    ax.set_title("Top municipalities by recorded events")
    ax.set_xlabel("Event count")
    ax.set_ylabel("Municipality")
    return _save_figure(fig, output_path)


def plot_stl_decomposition(decomposition_df: pd.DataFrame, output_path: Path, title: str) -> Path:
    """Plot STL decomposition components."""
    fig, axes = plt.subplots(4, 1, figsize=(10, 8), sharex=True)
    components = [
        ("observed", "Observed", COLOR_MAP["primary"]),
        ("trend", "Trend", COLOR_MAP["secondary"]),
        ("seasonal", "Seasonal", COLOR_MAP["accent"]),
        ("residual", "Residual", COLOR_MAP["danger"]),
    ]
    for axis, (column, label, color) in zip(axes, components):
        axis.plot(decomposition_df["month"], decomposition_df[column], color=color, linewidth=1.8)
        axis.set_ylabel(label)
    axes[0].set_title(title)
    axes[-1].set_xlabel("Month")
    return _save_figure(fig, output_path)


def plot_rolling_diagnostics(rolling_df: pd.DataFrame, output_path: Path, value_label: str) -> Path:
    """Plot the level, rolling mean, and rolling variance."""
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    axes[0].plot(rolling_df["month"], rolling_df["value"], color=COLOR_MAP["primary"], linewidth=1.8, label=value_label)
    axes[0].plot(rolling_df["month"], rolling_df["rolling_mean"], color=COLOR_MAP["accent"], linewidth=1.8, label="Rolling mean")
    axes[0].legend(frameon=False)
    axes[0].set_ylabel(value_label)
    axes[0].set_title(f"{value_label}: level and rolling mean")

    axes[1].plot(rolling_df["month"], rolling_df["rolling_variance"], color=COLOR_MAP["danger"], linewidth=1.8)
    axes[1].set_ylabel("Rolling variance")
    axes[1].set_xlabel("Month")
    axes[1].set_title(f"{value_label}: rolling variance")
    return _save_figure(fig, output_path)


def plot_change_points(
    series_df: pd.DataFrame,
    output_path: Path,
    value_column: str,
    value_label: str,
    change_dates: list[pd.Timestamp],
    shock_date: pd.Timestamp | None,
) -> Path:
    """Plot a series together with change points and the selected shock date."""
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(series_df["month"], series_df[value_column], color=COLOR_MAP["primary"], linewidth=2.0, label=value_label)
    
    labeled_change = False
    for change_date in change_dates:
        ax.axvline(
            change_date,
            color=COLOR_MAP["accent"],
            linestyle="--",
            linewidth=1.5,
            label="Secondary exogenous disruption" if not labeled_change else None
        )
        labeled_change = True
        
    if shock_date is not None:
        ax.axvline(shock_date, color=COLOR_MAP["danger"], linestyle="-", linewidth=2.0, label="Primary disaster shock month")
        
    ax.legend(loc="upper right", frameon=False, fontsize=9)
    ax.set_title(f"{value_label} evaluated against identified crisis disruptions")
    ax.set_xlabel("Month")
    ax.set_ylabel(value_label)
    return _save_figure(fig, output_path)


def plot_pca_loadings(loadings_df: pd.DataFrame, output_path: Path) -> Path:
    """Plot PCA feature loadings."""
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    plotting = loadings_df.sort_values("loading", ascending=True)
    colors = [COLOR_MAP["danger"] if value < 0 else COLOR_MAP["success"] for value in plotting["loading"]]
    ax.barh(plotting["feature"], plotting["loading"], color=colors)
    ax.set_title("PCA loadings for the crisis indicator")
    ax.set_xlabel("Loading")
    ax.set_ylabel("Monthly feature")
    return _save_figure(fig, output_path)
