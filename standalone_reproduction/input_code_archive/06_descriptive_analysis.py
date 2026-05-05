"""Run descriptive analysis on the merged cocoa price panel."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.descriptive.summary_stats import (
    compute_correlation_matrix,
    compute_pairwise_overlap_matrix,
    compute_series_coverage,
    compute_summary_statistics,
)
from src.descriptive.visualization import (
    build_color_map,
    plot_data_availability,
    plot_heatmap,
    plot_time_series,
    plot_time_series_panels,
)
from src.descriptive.volatility_measures import compute_log_returns
from src.outputs.export_figures import export_matplotlib_figure
from src.outputs.export_model_summaries import export_text_summary
from src.outputs.export_tables import export_dataframe_table
from src.utils.file_utils import load_yaml
from src.utils.logging_utils import get_project_logger

PATHS = load_yaml(ROOT / "config" / "paths.yaml")
CONFIG = load_yaml(ROOT / "config" / "project_config.yaml")
VARIABLE_DICTIONARY = load_yaml(ROOT / "config" / "variable_dictionary.yaml").get("variables", {})


def build_label_maps(value_columns: list[str]) -> tuple[dict[str, str], dict[str, str]]:
    """Build readable labels and unit labels for selected variables."""
    label_map: dict[str, str] = {}
    unit_map: dict[str, str] = {}

    for column in value_columns:
        metadata = VARIABLE_DICTIONARY.get(column, {})
        label_map[column] = metadata.get("label", column)
        unit_map[column] = metadata.get("unit", "")

    return label_map, unit_map


def build_acronym_maps(value_columns: list[str], label_map: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    """Build short plot labels plus an explicit legend list."""
    default_acronyms = {
        CONFIG["series"]["domestic_price"]: "COL",
        CONFIG["series"]["international_price"]: "WLD",
        CONFIG["series"]["eu_price"]: "EUC",
        CONFIG["series"]["exchange_rate"]: "FX",
        CONFIG["series"]["oil_price"]: "BRN",
    }

    acronym_map: dict[str, str] = {}
    legend_lines: list[str] = []
    for column in value_columns:
        acronym = default_acronyms.get(column, column.upper()[:6])
        acronym_map[column] = acronym
        legend_lines.append(f"{acronym} = {label_map.get(column, column)}")
    return acronym_map, legend_lines


def build_custom_acronym_maps(
    value_columns: list[str],
    label_map: dict[str, str],
    default_acronyms: dict[str, str],
) -> tuple[dict[str, str], list[str]]:
    """Build short labels from a provided acronym mapping."""
    acronym_map: dict[str, str] = {}
    legend_lines: list[str] = []
    for column in value_columns:
        acronym = default_acronyms.get(column, column.upper()[:6])
        acronym_map[column] = acronym
        legend_lines.append(f"{acronym} = {label_map.get(column, column)}")
    return acronym_map, legend_lines


def build_return_acronym_maps(
    return_columns: list[str],
    base_acronym_map: dict[str, str],
    return_label_map: dict[str, str],
) -> tuple[dict[str, str], list[str]]:
    """Build short labels for return-based plots and heatmaps."""
    acronym_map: dict[str, str] = {}
    legend_lines: list[str] = []

    for column in return_columns:
        base_column = column.replace("_log_return", "")
        acronym = f"R_{base_acronym_map.get(base_column, base_column.upper()[:3])}"
        acronym_map[column] = acronym
        legend_lines.append(f"{acronym} = {return_label_map.get(column, column)}")
    return acronym_map, legend_lines


def matrix_to_table(matrix: pd.DataFrame) -> pd.DataFrame:
    """Flatten a square matrix dataframe into an exportable table."""
    if matrix.empty:
        return matrix
    exportable = matrix.copy()
    exportable.index.name = "variable"
    return exportable.reset_index()


def build_log_return_panel(dataframe: pd.DataFrame, date_column: str, value_columns: list[str]) -> pd.DataFrame:
    """Compute log returns for each selected series."""
    returns = dataframe[[date_column]].copy()
    for column in value_columns:
        if column not in dataframe.columns:
            continue
        working = compute_log_returns(
            dataframe[[date_column, column]].copy(),
            value_column=column,
            date_column=date_column,
        )
        returns[f"{column}_log_return"] = working[f"{column}_log_return"]
    return returns


def build_overlap_window(
    dataframe: pd.DataFrame,
    date_column: str,
    value_columns: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp | None, pd.Timestamp | None]:
    """Build a shared calendar window and a fully balanced common sample."""
    available = [column for column in value_columns if column in dataframe.columns]
    if date_column not in dataframe.columns or not available:
        empty = pd.DataFrame(columns=[date_column] + available)
        return empty, empty, None, None

    starts = []
    ends = []
    for column in available:
        observed_dates = dataframe.loc[dataframe[column].notna(), date_column]
        if observed_dates.empty:
            empty = pd.DataFrame(columns=[date_column] + available)
            return empty, empty, None, None
        starts.append(observed_dates.min())
        ends.append(observed_dates.max())

    overlap_start = max(starts)
    overlap_end = min(ends)
    common_window = (
        dataframe.loc[(dataframe[date_column] >= overlap_start) & (dataframe[date_column] <= overlap_end), [date_column] + available]
        .copy()
        .reset_index(drop=True)
    )
    common_sample = common_window.dropna().reset_index(drop=True)
    return common_window, common_sample, overlap_start, overlap_end


def summarize_sample_window(
    dataframe: pd.DataFrame,
    date_column: str,
    sample_name: str,
    value_columns: list[str],
) -> dict[str, object]:
    """Summarize the common non-missing window for a set of variables."""
    available = [column for column in value_columns if column in dataframe.columns]
    subset = dataframe[[date_column] + available].dropna() if available else pd.DataFrame()
    if subset.empty:
        return {
            "sample_name": sample_name,
            "variables": ", ".join(available),
            "rows": 0,
            "start_date": None,
            "end_date": None,
            "span_months": None,
        }

    start_date = subset[date_column].min()
    end_date = subset[date_column].max()
    span_months = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1
    return {
        "sample_name": sample_name,
        "variables": ", ".join(available),
        "rows": len(subset),
        "start_date": start_date.date().isoformat(),
        "end_date": end_date.date().isoformat(),
        "span_months": span_months,
    }


def index_series_to_100(
    dataframe: pd.DataFrame,
    date_column: str,
    value_columns: list[str],
) -> pd.DataFrame:
    """Index each series to 100 at its first observation in the supplied window."""
    indexed = dataframe[[date_column] + value_columns].copy()
    for column in value_columns:
        first_value = indexed[column].dropna().iloc[0] if indexed[column].notna().any() else None
        if first_value in {None, 0}:
            indexed[column] = pd.NA
        else:
            indexed[column] = indexed[column] / first_value * 100.0
    return indexed


def describe_top_correlation(matrix: pd.DataFrame, label_map: dict[str, str]) -> str | None:
    """Return a readable description of the strongest off-diagonal correlation."""
    if matrix.empty or len(matrix.columns) < 2:
        return None

    melted = matrix.where(~pd.DataFrame(False, index=matrix.index, columns=matrix.columns)).copy()
    for column in melted.columns:
        melted.loc[column, column] = pd.NA
    stacked = melted.stack().sort_values(key=lambda series: series.abs(), ascending=False)
    if stacked.empty:
        return None

    pair = stacked.index[0]
    value = stacked.iloc[0]
    return (
        f"Strongest absolute common-sample correlation: "
        f"{label_map.get(pair[0], pair[0])} vs {label_map.get(pair[1], pair[1])} = {value:.3f}"
    )


def main() -> None:
    """Generate descriptive tables, coverage diagnostics, and figures."""
    logger = get_project_logger("06_descriptive_analysis", ROOT / PATHS["output_logs"])
    merged_path = ROOT / PATHS["data_processed_analysis_ready"] / "merged_cocoa_price_panel.csv"
    if not merged_path.exists():
        logger.warning("Merged dataset not found at %s", merged_path)
        return

    dataframe = pd.read_csv(merged_path, parse_dates=["date"]).sort_values("date").reset_index(drop=True)

    core_columns = [
        CONFIG["series"]["domestic_price"],
        CONFIG["series"]["international_price"],
        CONFIG["series"]["eu_price"],
        CONFIG["series"]["exchange_rate"],
        CONFIG["series"]["oil_price"],
    ]
    core_columns = [column for column in core_columns if column in dataframe.columns]
    climate_columns = [
        column
        for column in [
            "nasa_precipitation_mm_day",
            "nasa_temperature_c",
            "nasa_temperature_max_c",
            "nasa_temperature_min_c",
            "nasa_relative_humidity_pct",
            "nasa_wind_speed_ms",
            "nasa_surface_solar_radiation_mj_m2_day",
        ]
        if column in dataframe.columns
    ]
    log_columns = [f"log_{column}" for column in core_columns if f"log_{column}" in dataframe.columns]
    label_map, unit_map = build_label_maps(core_columns + climate_columns)
    core_color_map = build_color_map(core_columns)
    core_acronym_map, core_acronym_legend = build_acronym_maps(core_columns, label_map)
    common_window, common_level_sample, overlap_start, overlap_end = build_overlap_window(
        dataframe,
        "date",
        core_columns,
    )

    summary_table = compute_summary_statistics(dataframe, core_columns)
    export_dataframe_table(summary_table, ROOT / PATHS["output_tables"] / "table_summary_statistics.csv")

    log_summary_table = compute_summary_statistics(dataframe, log_columns)
    export_dataframe_table(log_summary_table, ROOT / PATHS["output_tables"] / "table_log_summary_statistics.csv")

    coverage_table = compute_series_coverage(dataframe, "date", core_columns)
    export_dataframe_table(coverage_table, ROOT / PATHS["output_tables"] / "table_series_coverage.csv")

    overlap_matrix = compute_pairwise_overlap_matrix(dataframe, core_columns)
    export_dataframe_table(
        matrix_to_table(overlap_matrix),
        ROOT / PATHS["output_tables"] / "table_pairwise_overlap_counts.csv",
    )

    common_window_summary = compute_summary_statistics(common_window, core_columns)
    export_dataframe_table(
        common_window_summary,
        ROOT / PATHS["output_tables"] / "table_summary_statistics_common_window.csv",
    )

    common_sample_summary = compute_summary_statistics(common_level_sample, core_columns)
    export_dataframe_table(
        common_sample_summary,
        ROOT / PATHS["output_tables"] / "table_summary_statistics_common_sample.csv",
    )

    common_window_coverage = compute_series_coverage(common_window, "date", core_columns)
    export_dataframe_table(
        common_window_coverage,
        ROOT / PATHS["output_tables"] / "table_series_coverage_common_window.csv",
    )

    common_window_overlap = compute_pairwise_overlap_matrix(common_window, core_columns)
    export_dataframe_table(
        matrix_to_table(common_window_overlap),
        ROOT / PATHS["output_tables"] / "table_pairwise_overlap_counts_common_window.csv",
    )

    export_dataframe_table(
        common_window,
        ROOT / PATHS["data_processed_final_series"] / "core_common_window_panel.csv",
    )
    export_dataframe_table(
        common_level_sample,
        ROOT / PATHS["data_processed_final_series"] / "core_common_sample_panel.csv",
    )

    if not common_window.empty:
        common_window_missing = common_window.loc[common_window.isna().any(axis=1)].copy()
    else:
        common_window_missing = pd.DataFrame(columns=["date"] + core_columns)
    export_dataframe_table(
        common_window_missing,
        ROOT / PATHS["output_tables"] / "table_common_window_missing_rows.csv",
    )

    if climate_columns:
        climate_full = dataframe[["date"] + climate_columns].dropna(how="all", subset=climate_columns).reset_index(drop=True)
        climate_window = (
            dataframe.loc[(dataframe["date"] >= overlap_start) & (dataframe["date"] <= overlap_end), ["date"] + climate_columns]
            .copy()
            .reset_index(drop=True)
            if overlap_start is not None and overlap_end is not None
            else pd.DataFrame(columns=["date"] + climate_columns)
        )

        export_dataframe_table(
            climate_full,
            ROOT / PATHS["data_processed_final_series"] / "climate_monthly_panel.csv",
        )
        export_dataframe_table(
            climate_window,
            ROOT / PATHS["data_processed_final_series"] / "climate_common_window_panel.csv",
        )

        climate_summary = compute_summary_statistics(climate_full, climate_columns)
        export_dataframe_table(
            climate_summary,
            ROOT / PATHS["output_tables"] / "table_climate_summary_statistics.csv",
        )
        climate_window_summary = compute_summary_statistics(climate_window, climate_columns)
        export_dataframe_table(
            climate_window_summary,
            ROOT / PATHS["output_tables"] / "table_climate_summary_statistics_common_window.csv",
        )

        climate_coverage = compute_series_coverage(climate_full, "date", climate_columns)
        export_dataframe_table(
            climate_coverage,
            ROOT / PATHS["output_tables"] / "table_climate_series_coverage.csv",
        )

        climate_color_map = build_color_map(climate_columns)
        climate_figure = plot_time_series_panels(
            climate_full,
            date_column="date",
            value_columns=climate_columns,
            title="Monthly weather and climate series",
            label_map=label_map,
            ylabels=unit_map,
            color_map=climate_color_map,
        )
        export_matplotlib_figure(
            climate_figure,
            ROOT / PATHS["output_figures"] / "figure_climate_series_panels.png",
        )

        climate_window_figure = plot_time_series_panels(
            climate_window,
            date_column="date",
            value_columns=climate_columns,
            title="Monthly weather and climate series in the shared calendar window",
            label_map=label_map,
            ylabels=unit_map,
            color_map=climate_color_map,
        )
        export_matplotlib_figure(
            climate_window_figure,
            ROOT / PATHS["output_figures"] / "figure_climate_series_panels_common_window.png",
        )

        climate_availability_figure = plot_data_availability(
            climate_full,
            date_column="date",
            value_columns=climate_columns,
            title="Weather-series availability across the monthly panel",
            label_map=label_map,
        )
        export_matplotlib_figure(
            climate_availability_figure,
            ROOT / PATHS["output_figures"] / "figure_climate_data_availability.png",
        )

        climate_core_common = (
            dataframe.loc[(dataframe["date"] >= overlap_start) & (dataframe["date"] <= overlap_end), ["date"] + core_columns + climate_columns]
            .dropna()
            .reset_index(drop=True)
            if overlap_start is not None and overlap_end is not None
            else pd.DataFrame(columns=["date"] + core_columns + climate_columns)
        )
        if not climate_core_common.empty:
            climate_core_correlation = compute_correlation_matrix(
                climate_core_common,
                core_columns + climate_columns,
            )
            export_dataframe_table(
                matrix_to_table(climate_core_correlation),
                ROOT / PATHS["output_tables"] / "table_climate_core_correlation_common_sample.csv",
            )

            climate_acronym_map, climate_acronym_legend = build_custom_acronym_maps(
                climate_columns,
                label_map,
                {
                    "nasa_precipitation_mm_day": "PRC",
                    "nasa_temperature_c": "TMP",
                    "nasa_temperature_max_c": "TMX",
                    "nasa_temperature_min_c": "TMN",
                    "nasa_relative_humidity_pct": "HUM",
                    "nasa_wind_speed_ms": "WND",
                    "nasa_surface_solar_radiation_mj_m2_day": "RAD",
                },
            )
            climate_core_display_map = {**core_acronym_map, **climate_acronym_map}
            climate_core_heatmap = plot_heatmap(
                climate_core_correlation,
                title="Price, macro, and weather correlations in the shared sample",
                value_format=".2f",
                display_label_map=climate_core_display_map,
                legend_lines=core_acronym_legend + climate_acronym_legend,
                legend_columns=4,
                vmin=-1.0,
                vmax=1.0,
            )
            export_matplotlib_figure(
                climate_core_heatmap,
                ROOT / PATHS["output_figures"] / "figure_climate_core_correlation_common_sample.png",
            )

    sample_windows = pd.DataFrame.from_records(
        [
            {
                "sample_name": "merged_panel_calendar",
                "variables": ", ".join(core_columns),
                "rows": len(dataframe),
                "start_date": dataframe["date"].min().date().isoformat(),
                "end_date": dataframe["date"].max().date().isoformat(),
                "span_months": (
                    (dataframe["date"].max().year - dataframe["date"].min().year) * 12
                    + dataframe["date"].max().month
                    - dataframe["date"].min().month
                    + 1
                ),
            },
            summarize_sample_window(
                dataframe,
                "date",
                "price_system_overlap",
                core_columns[:3],
            ),
            summarize_sample_window(
                dataframe,
                "date",
                "full_controls_overlap",
                core_columns,
            ),
            {
                "sample_name": "common_calendar_window",
                "variables": ", ".join(core_columns),
                "rows": len(common_window),
                "start_date": overlap_start.date().isoformat() if overlap_start is not None else None,
                "end_date": overlap_end.date().isoformat() if overlap_end is not None else None,
                "span_months": (
                    (overlap_end.year - overlap_start.year) * 12 + overlap_end.month - overlap_start.month + 1
                )
                if overlap_start is not None and overlap_end is not None
                else None,
            },
            {
                "sample_name": "balanced_common_sample",
                "variables": ", ".join(core_columns),
                "rows": len(common_level_sample),
                "start_date": common_level_sample["date"].min().date().isoformat() if not common_level_sample.empty else None,
                "end_date": common_level_sample["date"].max().date().isoformat() if not common_level_sample.empty else None,
                "span_months": (
                    (common_level_sample["date"].max().year - common_level_sample["date"].min().year) * 12
                    + common_level_sample["date"].max().month
                    - common_level_sample["date"].min().month
                    + 1
                )
                if not common_level_sample.empty
                else None,
            },
        ]
    )
    export_dataframe_table(sample_windows, ROOT / PATHS["output_tables"] / "table_common_sample_windows.csv")

    level_correlation = compute_correlation_matrix(common_level_sample, core_columns)
    export_dataframe_table(
        matrix_to_table(level_correlation),
        ROOT / PATHS["output_tables"] / "table_correlation_matrix_levels.csv",
    )
    export_dataframe_table(
        matrix_to_table(level_correlation),
        ROOT / PATHS["output_tables"] / "table_correlation_matrix_levels_common_sample.csv",
    )

    returns = build_log_return_panel(dataframe, "date", core_columns)
    return_columns = [column for column in returns.columns if column.endswith("_log_return")]
    export_dataframe_table(
        returns,
        ROOT / PATHS["data_processed_final_series"] / "core_log_return_series.csv",
    )

    return_summary = compute_summary_statistics(returns, return_columns)
    export_dataframe_table(
        return_summary,
        ROOT / PATHS["output_tables"] / "table_log_return_summary_statistics.csv",
    )

    common_window_returns = (
        build_log_return_panel(common_window, "date", core_columns)
        if return_columns and not common_window.empty
        else pd.DataFrame(columns=["date"] + return_columns)
    )
    common_return_sample = common_window_returns.dropna() if return_columns else pd.DataFrame()
    export_dataframe_table(
        common_window_returns,
        ROOT / PATHS["data_processed_final_series"] / "core_common_window_log_returns.csv",
    )

    common_return_summary = compute_summary_statistics(common_return_sample, return_columns)
    export_dataframe_table(
        common_return_summary,
        ROOT / PATHS["output_tables"] / "table_log_return_summary_statistics_common_sample.csv",
    )

    return_correlation = compute_correlation_matrix(common_return_sample, return_columns)
    export_dataframe_table(
        matrix_to_table(return_correlation),
        ROOT / PATHS["output_tables"] / "table_correlation_matrix_log_returns.csv",
    )
    export_dataframe_table(
        matrix_to_table(return_correlation),
        ROOT / PATHS["output_tables"] / "table_correlation_matrix_log_returns_common_sample.csv",
    )

    if not common_level_sample.empty:
        indexed_common_sample = index_series_to_100(common_level_sample, "date", core_columns)
        export_dataframe_table(
            indexed_common_sample,
            ROOT / PATHS["data_processed_final_series"] / "indexed_core_series.csv",
        )

        indexed_figure = plot_time_series(
            indexed_common_sample,
            date_column="date",
            value_columns=core_columns,
            title=f"Indexed core series ({common_level_sample['date'].min().strftime('%Y-%m')} = 100)",
            label_map=label_map,
            y_label="Index (base = 100)",
            color_map=core_color_map,
        )
        export_matplotlib_figure(
            indexed_figure,
            ROOT / PATHS["output_figures"] / "figure_indexed_core_series.png",
        )
        export_matplotlib_figure(
            indexed_figure,
            ROOT / PATHS["output_figures"] / "figure_indexed_core_series_common_sample.png",
        )

    panels_figure = plot_time_series_panels(
        dataframe,
        date_column="date",
        value_columns=core_columns,
        title="Core monthly series in original units",
        label_map=label_map,
        ylabels=unit_map,
        color_map=core_color_map,
    )
    export_matplotlib_figure(
        panels_figure,
        ROOT / PATHS["output_figures"] / "figure_core_series_panels.png",
    )

    common_window_panels = plot_time_series_panels(
        common_window,
        date_column="date",
        value_columns=core_columns,
        title="Core monthly series in the shared calendar window",
        label_map=label_map,
        ylabels=unit_map,
        color_map=core_color_map,
    )
    export_matplotlib_figure(
        common_window_panels,
        ROOT / PATHS["output_figures"] / "figure_core_series_panels_common_window.png",
    )

    macro_columns = [
        column
        for column in [CONFIG["series"]["exchange_rate"], CONFIG["series"]["oil_price"]]
        if column in dataframe.columns
    ]
    if macro_columns:
        macro_figure = plot_time_series_panels(
            dataframe,
            date_column="date",
            value_columns=macro_columns,
            title="Macro control series",
            label_map=label_map,
            ylabels=unit_map,
            color_map=core_color_map,
        )
        export_matplotlib_figure(
            macro_figure,
            ROOT / PATHS["output_figures"] / "figure_macro_controls_panels.png",
        )
        common_window_macro_figure = plot_time_series_panels(
            common_window,
            date_column="date",
            value_columns=macro_columns,
            title="Macro controls in the shared calendar window",
            label_map=label_map,
            ylabels=unit_map,
            color_map=core_color_map,
        )
        export_matplotlib_figure(
            common_window_macro_figure,
            ROOT / PATHS["output_figures"] / "figure_macro_controls_panels_common_window.png",
        )

    availability_figure = plot_data_availability(
        dataframe,
        date_column="date",
        value_columns=core_columns,
        title="Data availability across the merged monthly panel",
        label_map=label_map,
    )
    export_matplotlib_figure(
        availability_figure,
        ROOT / PATHS["output_figures"] / "figure_data_availability.png",
    )
    common_window_availability = plot_data_availability(
        common_window,
        date_column="date",
        value_columns=core_columns,
        title="Data availability within the shared calendar window",
        label_map=label_map,
    )
    export_matplotlib_figure(
        common_window_availability,
        ROOT / PATHS["output_figures"] / "figure_data_availability_common_window.png",
    )

    if not level_correlation.empty:
        level_heatmap = plot_heatmap(
            level_correlation,
            title="Common-sample correlation matrix of core level series",
            value_format=".2f",
            display_label_map=core_acronym_map,
            legend_lines=core_acronym_legend,
            vmin=-1.0,
            vmax=1.0,
        )
        export_matplotlib_figure(
            level_heatmap,
            ROOT / PATHS["output_figures"] / "figure_correlation_heatmap_levels.png",
        )
        export_matplotlib_figure(
            level_heatmap,
            ROOT / PATHS["output_figures"] / "figure_correlation_heatmap_levels_common_sample.png",
        )

    if not return_correlation.empty:
        return_label_map = {
            column: f"{label_map.get(column.replace('_log_return', ''), column.replace('_log_return', ''))} log return"
            for column in return_columns
        }
        return_color_map = {
            column: core_color_map.get(column.replace("_log_return", ""), list(core_color_map.values())[0])
            for column in return_columns
        }
        return_acronym_map, return_acronym_legend = build_return_acronym_maps(
            return_columns,
            core_acronym_map,
            return_label_map,
        )
        return_heatmap = plot_heatmap(
            return_correlation,
            title="Common-sample correlation matrix of monthly log returns",
            value_format=".2f",
            display_label_map=return_acronym_map,
            legend_lines=return_acronym_legend,
            vmin=-1.0,
            vmax=1.0,
        )
        export_matplotlib_figure(
            return_heatmap,
            ROOT / PATHS["output_figures"] / "figure_correlation_heatmap_log_returns.png",
        )
        export_matplotlib_figure(
            return_heatmap,
            ROOT / PATHS["output_figures"] / "figure_correlation_heatmap_log_returns_common_sample.png",
        )

        return_panels = plot_time_series_panels(
            returns.dropna(how="all", subset=return_columns),
            date_column="date",
            value_columns=return_columns,
            title="Monthly log returns of the core series",
            label_map=return_label_map,
            ylabels={column: "log return" for column in return_columns},
            color_map=return_color_map,
        )
        export_matplotlib_figure(
            return_panels,
            ROOT / PATHS["output_figures"] / "figure_core_log_returns_panels.png",
        )
        common_window_return_panels = plot_time_series_panels(
            common_window_returns,
            date_column="date",
            value_columns=return_columns,
            title="Monthly log returns in the shared calendar window",
            label_map=return_label_map,
            ylabels={column: "log return" for column in return_columns},
            color_map=return_color_map,
        )
        export_matplotlib_figure(
            common_window_return_panels,
            ROOT / PATHS["output_figures"] / "figure_core_log_returns_panels_common_window.png",
        )

    imputed_path = ROOT / PATHS["data_processed_final_series"] / "core_common_window_panel_imputed.csv"
    if imputed_path.exists():
        imputed_window = pd.read_csv(imputed_path, parse_dates=["date"])
        imputed_window = imputed_window.sort_values("date").reset_index(drop=True)
        imputed_core = imputed_window[["date"] + core_columns].copy()
        imputed_summary = compute_summary_statistics(imputed_core, core_columns)
        export_dataframe_table(
            imputed_summary,
            ROOT / PATHS["output_tables"] / "table_summary_statistics_common_window_imputed.csv",
        )

        imputed_correlation = compute_correlation_matrix(imputed_core, core_columns)
        export_dataframe_table(
            matrix_to_table(imputed_correlation),
            ROOT / PATHS["output_tables"] / "table_correlation_matrix_levels_common_window_imputed.csv",
        )

        imputed_returns = build_log_return_panel(imputed_core, "date", core_columns)
        imputed_return_columns = [column for column in imputed_returns.columns if column.endswith("_log_return")]
        imputed_return_summary = compute_summary_statistics(imputed_returns.dropna(), imputed_return_columns)
        export_dataframe_table(
            imputed_return_summary,
            ROOT / PATHS["output_tables"] / "table_log_return_summary_statistics_common_window_imputed.csv",
        )

        imputed_return_correlation = compute_correlation_matrix(imputed_returns.dropna(), imputed_return_columns)
        export_dataframe_table(
            matrix_to_table(imputed_return_correlation),
            ROOT / PATHS["output_tables"] / "table_correlation_matrix_log_returns_common_window_imputed.csv",
        )

        imputed_panels = plot_time_series_panels(
            imputed_core,
            date_column="date",
            value_columns=core_columns,
            title="Core monthly series in the shared calendar window (imputed)",
            label_map=label_map,
            ylabels=unit_map,
            color_map=core_color_map,
        )
        export_matplotlib_figure(
            imputed_panels,
            ROOT / PATHS["output_figures"] / "figure_core_series_panels_common_window_imputed.png",
        )

        imputed_indexed = index_series_to_100(imputed_core, "date", core_columns)
        export_dataframe_table(
            imputed_indexed,
            ROOT / PATHS["data_processed_final_series"] / "indexed_core_series_common_window_imputed.csv",
        )
        imputed_indexed_figure = plot_time_series(
            imputed_indexed,
            date_column="date",
            value_columns=core_columns,
            title=f"Indexed core series with imputation ({imputed_core['date'].min().strftime('%Y-%m')} = 100)",
            label_map=label_map,
            y_label="Index (base = 100)",
            color_map=core_color_map,
        )
        export_matplotlib_figure(
            imputed_indexed_figure,
            ROOT / PATHS["output_figures"] / "figure_indexed_core_series_common_window_imputed.png",
        )

        imputed_level_heatmap = plot_heatmap(
            imputed_correlation,
            title="Correlation matrix in the shared calendar window (imputed)",
            value_format=".2f",
            display_label_map=core_acronym_map,
            legend_lines=core_acronym_legend,
            vmin=-1.0,
            vmax=1.0,
        )
        export_matplotlib_figure(
            imputed_level_heatmap,
            ROOT / PATHS["output_figures"] / "figure_correlation_heatmap_levels_common_window_imputed.png",
        )

        if imputed_return_columns:
            imputed_return_label_map = {
                column: f"{label_map.get(column.replace('_log_return', ''), column.replace('_log_return', ''))} log return"
                for column in imputed_return_columns
            }
            imputed_return_color_map = {
                column: core_color_map.get(column.replace("_log_return", ""), list(core_color_map.values())[0])
                for column in imputed_return_columns
            }
            imputed_return_acronym_map, imputed_return_acronym_legend = build_return_acronym_maps(
                imputed_return_columns,
                core_acronym_map,
                imputed_return_label_map,
            )
            imputed_return_heatmap = plot_heatmap(
                imputed_return_correlation,
                title="Log-return correlation matrix in the shared calendar window (imputed)",
                value_format=".2f",
                display_label_map=imputed_return_acronym_map,
                legend_lines=imputed_return_acronym_legend,
                vmin=-1.0,
                vmax=1.0,
            )
            export_matplotlib_figure(
                imputed_return_heatmap,
                ROOT / PATHS["output_figures"] / "figure_correlation_heatmap_log_returns_common_window_imputed.png",
            )

            imputed_return_panels = plot_time_series_panels(
                imputed_returns,
                date_column="date",
                value_columns=imputed_return_columns,
                title="Monthly log returns in the shared calendar window (imputed)",
                label_map=imputed_return_label_map,
                ylabels={column: "log return" for column in imputed_return_columns},
                color_map=imputed_return_color_map,
            )
            export_matplotlib_figure(
                imputed_return_panels,
                ROOT / PATHS["output_figures"] / "figure_core_log_returns_panels_common_window_imputed.png",
            )

    notes = [
        f"Merged panel rows: {len(dataframe)}",
        f"Merged panel date range: {dataframe['date'].min().date().isoformat()} to {dataframe['date'].max().date().isoformat()}",
        f"Shared calendar window: {overlap_start.date().isoformat() if overlap_start is not None else 'n/a'} to {overlap_end.date().isoformat() if overlap_end is not None else 'n/a'}",
        f"Balanced common sample rows: {len(common_level_sample)}",
        "",
        "Series coverage:",
    ]
    for record in coverage_table.to_dict(orient="records"):
        notes.append(
            f"- {label_map.get(record['variable'], record['variable'])}: "
            f"{record['non_missing_observations']} observations, "
            f"{record['first_observation']} to {record['last_observation']}"
        )

    if climate_columns:
        climate_coverage_table = compute_series_coverage(dataframe[["date"] + climate_columns], "date", climate_columns)
        notes.extend(["", "Weather-series coverage:"])
        for record in climate_coverage_table.to_dict(orient="records"):
            notes.append(
                f"- {label_map.get(record['variable'], record['variable'])}: "
                f"{record['non_missing_observations']} observations, "
                f"{record['first_observation']} to {record['last_observation']}"
            )

    notes.extend(["", "Common sample windows:"])
    for record in sample_windows.to_dict(orient="records"):
        notes.append(
            f"- {record['sample_name']}: {record['rows']} rows, "
            f"{record['start_date']} to {record['end_date']}"
        )

    if not common_window_missing.empty:
        notes.extend(["", "Rows still missing inside the shared calendar window:"])
        for _, row in common_window_missing.iterrows():
            missing_columns = [label_map.get(column, column) for column in core_columns if pd.isna(row[column])]
            notes.append(
                f"- {row['date'].date().isoformat()}: missing {', '.join(missing_columns)}"
            )

    top_level_correlation = describe_top_correlation(level_correlation, label_map)
    if top_level_correlation:
        notes.extend(["", top_level_correlation])

    export_text_summary(
        "\n".join(notes),
        ROOT / PATHS["output_appendix"] / "descriptive_analysis_notes.txt",
    )

    logger.info(
        "Exported descriptive tables for %s core series and %s return series",
        len(core_columns),
        len(return_columns),
    )


if __name__ == "__main__":
    main()
