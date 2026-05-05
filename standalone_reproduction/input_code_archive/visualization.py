"""Plotting utilities for v2 report artifacts."""

from __future__ import annotations

from pathlib import Path

import matplotlib
import pandas as pd

from src.outputs.export_figures import export_matplotlib_figure


matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np

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
def plot_v3_integrated_heatmap(correlation_matrix: pd.DataFrame, output_path: Path, title: str) -> Path:
    """Plot an integrated correlation heatmap (V1 style)."""
    import numpy as np
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(correlation_matrix.to_numpy(), cmap="RdBu_r", vmin=-1, vmax=1)
    
    ax.set_xticks(np.arange(len(correlation_matrix.columns)))
    ax.set_yticks(np.arange(len(correlation_matrix.index)))
    ax.set_xticklabels(correlation_matrix.columns, rotation=45, ha="right")
    ax.set_yticklabels(correlation_matrix.index)
    
    # Annotate
    for i in range(len(correlation_matrix.index)):
        for j in range(len(correlation_matrix.columns)):
            text = ax.text(j, i, f"{correlation_matrix.iloc[i, j]:.2f}",
                           ha="center", va="center", color="black" if abs(correlation_matrix.iloc[i, j]) < 0.5 else "white")
            
    ax.set_title(title)
    fig.colorbar(im, ax=ax, label="Pearson Correlation")
    fig.tight_layout()
    return _save_figure(fig, output_path)


def plot_v3_integrated_panels(dataframe: pd.DataFrame, columns: list[str], output_path: Path, title: str) -> Path:
    """Plot integrated time-series panels (V1 style)."""
    fig, axes = plt.subplots(len(columns), 1, figsize=(10, 2.5 * len(columns)), sharex=True)
    if len(columns) == 1:
        axes = [axes]
    
    for ax, col in zip(axes, columns):
        ax.plot(dataframe["month"] if "month" in dataframe.columns else dataframe.index, dataframe[col], color=COLOR_MAP["primary"], linewidth=1.5)
        ax.set_ylabel(col.replace("_", " ").title())
        ax.grid(True, alpha=0.3)
        
    axes[0].set_title(title)
    axes[-1].set_xlabel("Date")
    fig.tight_layout()
    return _save_figure(fig, output_path)


def plot_data_availability_v3(
    dataframe: pd.DataFrame,
    date_column: str,
    value_columns: list[str],
    title: str,
    label_map: dict[str, str] | None = None,
    output_path: Path | None = None,
) -> Path:
    """Visualize non-missing data availability (V1 style)."""
    available = [column for column in value_columns if column in dataframe.columns]
    if not available:
        return Path()

    # Build matrix
    frame = dataframe[[date_column] + available].copy()
    frame[date_column] = pd.to_datetime(frame[date_column])
    availability = frame[available].notna().astype(int).transpose()

    # Discrete colormap: gray for missing, success color for available
    cmap = ListedColormap(["#e5e7eb", COLOR_MAP["success"]])

    fig, ax = plt.subplots(figsize=(10, max(3, 0.45 * len(available))))
    image = ax.imshow(availability.to_numpy(), aspect="auto", cmap=cmap, interpolation="nearest")
    
    ax.set_yticks(np.arange(len(available)))
    ax.set_yticklabels([(label_map or {}).get(column, column) for column in available])
    
    # Date ticks
    tick_count = min(12, len(frame))
    tick_positions = np.linspace(0, len(frame) - 1, tick_count, dtype=int) if len(frame) else []
    ax.set_xticks(tick_positions)
    ax.set_xticklabels([frame.iloc[pos][date_column].strftime("%Y-%m") for pos in tick_positions], rotation=45, ha="right")
    
    ax.set_title(title)
    fig.colorbar(image, ax=ax, ticks=[0, 1], shrink=0.7, label="Data Availability")
    fig.tight_layout()
    
    if output_path:
        return _save_figure(fig, output_path)
    return fig


def plot_time_series_panels_v3(
    dataframe: pd.DataFrame,
    date_column: str,
    value_columns: list[str],
    title: str,
    label_map: dict[str, str] | None = None,
    unit_map: dict[str, str] | None = None,
    output_path: Path | None = None,
) -> Path:
    """Enhanced V1-style panels with support for units and custom colors."""
    available = [column for column in value_columns if column in dataframe.columns]
    if not available:
        return Path()

    fig, axes = plt.subplots(len(available), 1, figsize=(11, 2.6 * len(available)), sharex=True)
    if len(available) == 1:
        axes = [axes]
        
    for ax, col in zip(axes, available):
        ax.plot(dataframe[date_column], dataframe[col], color=COLOR_MAP["primary"], linewidth=1.8)
        label = (label_map or {}).get(col, col)
        unit = (unit_map or {}).get(col, "")
        ax.set_ylabel(f"{label}\n({unit})" if unit else label, fontsize=9)
        ax.grid(True, alpha=0.3, linestyle="--")
        
    axes[0].set_title(title)
    axes[-1].set_xlabel("Date")
    fig.tight_layout()
    
    if output_path:
        return _save_figure(fig, output_path)


def plot_actual_vs_fitted(y_true: pd.Series, y_pred: pd.Series, dates: pd.Series, output_path: Path, title: str) -> Path:
    """Plot actual observations versus model predictions."""
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(dates, y_true, label="Observed", color=COLOR_MAP["primary"], alpha=0.7)
    ax.plot(dates, y_pred, label="Fitted", color=COLOR_MAP["accent"], linestyle="--")
    ax.set_title(title)
    ax.set_ylabel("Returns")
    ax.legend(loc="upper left")
    return _save_figure(fig, output_path)


def plot_v1_long_run_heatmap(full_df: pd.DataFrame, columns: list[str], output_path: Path) -> Path:
    """Plot historical data coverage over the long-run window."""
    subset = full_df[columns].notna().astype(int)
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Use a binary colormap
    cmap = ListedColormap(["#f8f9fa", COLOR_MAP["primary"]])
    ax.imshow(subset.T, aspect="auto", cmap=cmap, interpolation="none", 
              extent=[full_df["date"].min().year, full_df["date"].max().year, 0, len(columns)])
    
    ax.set_yticks(np.arange(len(columns)) + 0.5)
    ax.set_yticklabels(columns[::-1])
    ax.set_title("Long-run Historical Data Coverage (1960-2026)")
    ax.grid(False)
    return _save_figure(fig, output_path)


def plot_v1_rolling_correlation(df: pd.DataFrame, col1: str, col2: str, window: int, output_path: Path) -> Path:
    """Plot rolling correlation between two variables."""
    rolling_corr = df[col1].rolling(window).corr(df[col2])
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(df.index, rolling_corr, color=COLOR_MAP["success"], linewidth=2)
    ax.axhline(rolling_corr.mean(), color=COLOR_MAP["danger"], linestyle=":", label=f"Mean: {rolling_corr.mean():.2f}")
    ax.set_title(f"Rolling {window}-month Correlation: {col1} vs {col2}")
    ax.set_ylim(-1, 1)
    ax.legend()
    return _save_figure(fig, output_path)
    return fig
