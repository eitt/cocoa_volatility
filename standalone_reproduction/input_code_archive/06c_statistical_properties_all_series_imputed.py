"""Report statistical properties for the imputed supply-chain and weather series."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_processing.imputation import (
    add_imputation_flags,
    build_imputation_audit,
    run_iterative_imputation,
    run_knn_imputation,
)
from src.descriptive.summary_stats import compute_extended_summary_statistics
from src.descriptive.visualization import plot_stl_decomposition, plot_time_series_panels
from src.descriptive.volatility_measures import compute_log_returns, compute_rolling_volatility
from src.econometrics.stationarity_tests import run_stationarity_suite
from src.econometrics.volatility_tests import compute_volatility_summary, run_arch_lm_suite
from src.outputs.export_figures import export_matplotlib_figure
from src.outputs.export_model_summaries import export_text_summary
from src.outputs.export_tables import export_dataframe_table
from src.utils.file_utils import load_yaml
from src.utils.logging_utils import get_project_logger

PATHS = load_yaml(ROOT / "config" / "paths.yaml")
CONFIG = load_yaml(ROOT / "config" / "project_config.yaml")
VARIABLE_DICTIONARY = load_yaml(ROOT / "config" / "variable_dictionary.yaml").get("variables", {})

WEATHER_COLUMNS = [
    "nasa_precipitation_mm_day",
    "nasa_temperature_c",
    "nasa_temperature_max_c",
    "nasa_temperature_min_c",
    "nasa_relative_humidity_pct",
    "nasa_wind_speed_ms",
    "nasa_surface_solar_radiation_mj_m2_day",
]


def build_label_maps(value_columns: list[str]) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Build readable labels, units, and source blocks for selected variables."""
    label_map: dict[str, str] = {}
    unit_map: dict[str, str] = {}
    block_map: dict[str, str] = {}
    for column in value_columns:
        metadata = VARIABLE_DICTIONARY.get(column, {})
        label_map[column] = metadata.get("label", column)
        unit_map[column] = metadata.get("unit", "")
        block_map[column] = metadata.get("source_block", "unmapped")
    return label_map, unit_map, block_map


def add_series_metadata(
    dataframe: pd.DataFrame,
    series_form: str,
    label_map: dict[str, str],
    unit_map: dict[str, str],
    block_map: dict[str, str],
) -> pd.DataFrame:
    """Add label, unit, and block metadata to an exported table."""
    if dataframe.empty:
        return dataframe

    enriched = dataframe.copy()
    if "variable" in enriched.columns:
        enriched["series_form"] = series_form
        enriched["base_variable"] = enriched["variable"].str.replace("_log_return", "", regex=False)
        enriched["label"] = enriched["base_variable"].map(label_map)
        enriched["unit"] = enriched["base_variable"].map(unit_map)
        enriched["source_block"] = enriched["base_variable"].map(block_map)
    return enriched


def compute_decomposition_strength(
    trend: pd.Series,
    seasonal: pd.Series,
    residual: pd.Series,
) -> tuple[float | None, float | None]:
    """Compute additive STL trend and seasonal strengths."""
    residual_variance = float(np.nanvar(residual))
    trend_denom = float(np.nanvar(trend + residual))
    seasonal_denom = float(np.nanvar(seasonal + residual))

    trend_strength = max(0.0, 1.0 - residual_variance / trend_denom) if trend_denom > 0 else None
    seasonal_strength = max(0.0, 1.0 - residual_variance / seasonal_denom) if seasonal_denom > 0 else None
    return trend_strength, seasonal_strength


def build_return_panel(dataframe: pd.DataFrame, value_columns: list[str]) -> pd.DataFrame:
    """Compute log-return panel for selected variables."""
    returns = dataframe[["date"]].copy()
    for column in value_columns:
        working = compute_log_returns(
            dataframe[["date", column]].copy(),
            value_column=column,
            date_column="date",
        )
        returns[f"{column}_log_return"] = working[f"{column}_log_return"]
    return returns


def build_overview_table(
    all_columns: list[str],
    label_map: dict[str, str],
    unit_map: dict[str, str],
    block_map: dict[str, str],
    level_summary: pd.DataFrame,
    return_summary: pd.DataFrame,
    stationarity_levels: pd.DataFrame,
    stationarity_returns: pd.DataFrame,
    volatility_summary: pd.DataFrame,
    arch_tests: pd.DataFrame,
    decomposition_strength: pd.DataFrame,
    imputed_panel: pd.DataFrame,
) -> pd.DataFrame:
    """Create a one-row-per-series overview table."""
    overview = pd.DataFrame(
        {
            "variable": all_columns,
            "label": [label_map.get(column, column) for column in all_columns],
            "unit": [unit_map.get(column, "") for column in all_columns],
            "source_block": [block_map.get(column, "unmapped") for column in all_columns],
        }
    )

    level_fields = [
        "count",
        "mean",
        "std",
        "min",
        "25%",
        "50%",
        "75%",
        "max",
        "missing_observations",
        "skewness",
        "kurtosis",
        "iqr",
        "coefficient_of_variation",
    ]
    level_slice = level_summary[["variable"] + level_fields].rename(
        columns={field: f"level_{field.replace('%', 'pct')}" for field in level_fields}
    )
    overview = overview.merge(level_slice, on="variable", how="left")

    return_fields = [
        "count",
        "mean",
        "std",
        "min",
        "25%",
        "50%",
        "75%",
        "max",
        "missing_observations",
        "skewness",
        "kurtosis",
        "iqr",
        "coefficient_of_variation",
    ]
    return_slice = return_summary[["base_variable"] + return_fields].rename(
        columns={
            "base_variable": "variable",
            **{field: f"return_{field.replace('%', 'pct')}" for field in return_fields},
        }
    )
    overview = overview.merge(return_slice, on="variable", how="left")

    for table, prefix in [
        (stationarity_levels, "level"),
        (stationarity_returns, "return"),
    ]:
        if table.empty:
            continue
        pivot = table.pivot_table(index="base_variable", columns="test", values="p_value", aggfunc="first")
        pivot.columns = [f"{prefix}_{column}_p_value" for column in pivot.columns]
        overview = overview.merge(
            pivot.reset_index().rename(columns={"base_variable": "variable"}),
            on="variable",
            how="left",
        )

        status = (
            table.pivot_table(index="base_variable", columns="test", values="status", aggfunc="first")
            .add_prefix(f"{prefix}_")
            .add_suffix("_status")
        )
        overview = overview.merge(
            status.reset_index().rename(columns={"base_variable": "variable"}),
            on="variable",
            how="left",
        )

    volatility_fields = [
        "observations",
        "mean_return",
        "std_dev",
        "annualized_volatility",
        "mean_abs_return",
        "max_abs_return",
        "min_return",
        "max_return",
        "rolling_volatility_mean",
        "rolling_volatility_max",
    ]
    volatility_slice = volatility_summary[["base_variable"] + volatility_fields].rename(
        columns={"base_variable": "variable"}
    )
    overview = overview.merge(volatility_slice, on="variable", how="left")

    arch_keep_columns = [
        column
        for column in ["base_variable", "lags", "statistic", "p_value", "f_statistic", "f_p_value", "status"]
        if column in arch_tests.columns
    ]
    arch_slice = arch_tests[arch_keep_columns].rename(
        columns={
            "base_variable": "variable",
            "statistic": "arch_lm_statistic",
            "p_value": "arch_lm_p_value",
            "f_statistic": "arch_lm_f_statistic",
            "f_p_value": "arch_lm_f_p_value",
            "status": "arch_lm_status",
        }
    )
    keep_arch_columns = [
        column
        for column in [
            "variable",
            "lags",
            "arch_lm_statistic",
            "arch_lm_p_value",
            "arch_lm_f_statistic",
            "arch_lm_f_p_value",
            "arch_lm_status",
        ]
        if column in arch_slice.columns
    ]
    overview = overview.merge(arch_slice[keep_arch_columns], on="variable", how="left")

    decomposition_slice = decomposition_strength[
        ["variable", "label", "trend_strength", "seasonal_strength", "residual_std"]
    ].copy()
    overview = overview.merge(decomposition_slice, on=["variable", "label"], how="left")

    imputed_counts = []
    for column in all_columns:
        flag_column = f"imputed_{column}"
        imputed_counts.append(
            int(imputed_panel[flag_column].sum()) if flag_column in imputed_panel.columns else 0
        )
    overview["imputed_observations"] = imputed_counts
    overview["imputation_context"] = np.where(
        overview["imputed_observations"] > 0,
        "iterative_block_specific",
        "not_needed",
    )
    if "source_block_x" in overview.columns:
        overview = overview.rename(columns={"source_block_x": "source_block"})
    if "source_block_y" in overview.columns:
        overview = overview.drop(columns=["source_block_y"])
    return overview


def main() -> None:
    """Generate weather and all-series statistical outputs from imputed aligned panels."""
    logger = get_project_logger("06c_statistical_properties_all_series_imputed", ROOT / PATHS["output_logs"])

    core_imputed_path = ROOT / PATHS["data_processed_final_series"] / "core_common_window_panel_imputed.csv"
    climate_path = ROOT / PATHS["data_processed_final_series"] / "climate_common_window_panel.csv"
    if not core_imputed_path.exists() or not climate_path.exists():
        logger.warning("Required imputed core or climate panel missing.")
        return

    core_imputed = pd.read_csv(core_imputed_path, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    climate_window = pd.read_csv(climate_path, parse_dates=["date"]).sort_values("date").reset_index(drop=True)

    weather_columns = [column for column in WEATHER_COLUMNS if column in climate_window.columns]
    if not weather_columns:
        logger.warning("No weather columns found in %s", climate_path)
        return

    core_columns = [
        CONFIG["series"]["domestic_price"],
        CONFIG["series"]["international_price"],
        CONFIG["series"]["eu_price"],
        CONFIG["series"]["exchange_rate"],
        CONFIG["series"]["oil_price"],
    ]
    core_columns = [column for column in core_columns if column in core_imputed.columns]
    all_columns = core_columns + weather_columns
    label_map, unit_map, block_map = build_label_maps(all_columns)

    weather_missingness = (
        climate_window[weather_columns]
        .isna()
        .sum()
        .rename_axis("variable")
        .reset_index(name="missing_observations")
    )
    export_dataframe_table(
        weather_missingness,
        ROOT / PATHS["output_tables"] / "table_weather_common_window_missingness.csv",
    )

    weather_knn = run_knn_imputation(climate_window, weather_columns, n_neighbors=5)
    weather_iterative = run_iterative_imputation(climate_window, weather_columns, random_state=42, max_iter=50)
    weather_knn_flagged = add_imputation_flags(climate_window, weather_knn, weather_columns)
    weather_iterative_flagged = add_imputation_flags(climate_window, weather_iterative, weather_columns)

    export_dataframe_table(
        weather_knn_flagged,
        ROOT / PATHS["data_processed_final_series"] / "weather_common_window_panel_imputed_knn.csv",
    )
    export_dataframe_table(
        weather_iterative_flagged,
        ROOT / PATHS["data_processed_final_series"] / "weather_common_window_panel_imputed_iterative.csv",
    )
    export_dataframe_table(
        weather_iterative_flagged,
        ROOT / PATHS["data_processed_final_series"] / "weather_common_window_panel_imputed.csv",
    )

    weather_audit = build_imputation_audit(
        climate_window,
        weather_columns,
        date_column="date",
        method_frames={"knn": weather_knn, "iterative": weather_iterative},
    )
    export_dataframe_table(
        weather_audit,
        ROOT / PATHS["output_tables"] / "table_weather_imputation_audit.csv",
    )

    weather_reference_correlations = climate_window[weather_columns].dropna().corr()
    weather_reference_correlations.index.name = "variable"
    export_dataframe_table(
        weather_reference_correlations.reset_index(),
        ROOT / PATHS["output_tables"] / "table_weather_imputation_reference_correlations.csv",
    )

    climate_keep = ["date"] + weather_columns + [f"imputed_{column}" for column in weather_columns]
    core_keep = ["date"] + core_columns + [f"imputed_{column}" for column in core_columns if f"imputed_{column}" in core_imputed.columns]
    all_series_imputed = core_imputed[core_keep].merge(
        weather_iterative_flagged[climate_keep],
        on="date",
        how="inner",
    )
    export_dataframe_table(
        all_series_imputed,
        ROOT / PATHS["data_processed_final_series"] / "all_series_common_window_panel_imputed.csv",
    )

    analysis_panel = all_series_imputed[["date"] + all_columns].copy()
    level_summary = add_series_metadata(
        compute_extended_summary_statistics(analysis_panel, all_columns),
        series_form="level",
        label_map=label_map,
        unit_map=unit_map,
        block_map=block_map,
    )
    export_dataframe_table(
        level_summary,
        ROOT / PATHS["output_tables"] / "table_statistical_properties_imputed_all_series_levels.csv",
    )
    export_dataframe_table(
        level_summary.loc[level_summary["base_variable"].isin(weather_columns)].reset_index(drop=True),
        ROOT / PATHS["output_tables"] / "table_statistical_properties_imputed_weather_levels.csv",
    )

    returns = build_return_panel(analysis_panel, all_columns)
    return_columns = [column for column in returns.columns if column.endswith("_log_return")]
    export_dataframe_table(
        returns,
        ROOT / PATHS["data_processed_final_series"] / "all_series_common_window_log_returns_imputed.csv",
    )

    return_summary = add_series_metadata(
        compute_extended_summary_statistics(returns, return_columns),
        series_form="log_return",
        label_map=label_map,
        unit_map=unit_map,
        block_map=block_map,
    )
    export_dataframe_table(
        return_summary,
        ROOT / PATHS["output_tables"] / "table_statistical_properties_imputed_all_series_log_returns.csv",
    )
    export_dataframe_table(
        return_summary.loc[return_summary["base_variable"].isin(weather_columns)].reset_index(drop=True),
        ROOT / PATHS["output_tables"] / "table_statistical_properties_imputed_weather_log_returns.csv",
    )

    stationarity_levels = add_series_metadata(
        run_stationarity_suite(analysis_panel, all_columns),
        series_form="level",
        label_map=label_map,
        unit_map=unit_map,
        block_map=block_map,
    )
    export_dataframe_table(
        stationarity_levels,
        ROOT / PATHS["output_tables"] / "table_stationarity_tests_imputed_all_series_levels.csv",
    )
    export_dataframe_table(
        stationarity_levels.loc[stationarity_levels["base_variable"].isin(weather_columns)].reset_index(drop=True),
        ROOT / PATHS["output_tables"] / "table_stationarity_tests_imputed_weather_levels.csv",
    )

    clean_returns = returns.dropna().reset_index(drop=True)
    stationarity_returns = add_series_metadata(
        run_stationarity_suite(clean_returns, return_columns),
        series_form="log_return",
        label_map=label_map,
        unit_map=unit_map,
        block_map=block_map,
    )
    export_dataframe_table(
        stationarity_returns,
        ROOT / PATHS["output_tables"] / "table_stationarity_tests_imputed_all_series_log_returns.csv",
    )
    export_dataframe_table(
        stationarity_returns.loc[stationarity_returns["base_variable"].isin(weather_columns)].reset_index(drop=True),
        ROOT / PATHS["output_tables"] / "table_stationarity_tests_imputed_weather_log_returns.csv",
    )

    volatility_panel = returns.copy()
    rolling_columns: list[str] = []
    for column in return_columns:
        volatility_panel = compute_rolling_volatility(
            volatility_panel,
            return_column=column,
            window=12,
        )
        rolling_columns.append(f"{column}_rolling_volatility")
    export_dataframe_table(
        volatility_panel,
        ROOT / PATHS["data_processed_final_series"] / "all_series_common_window_volatility_imputed.csv",
    )

    volatility_summary = add_series_metadata(
        compute_volatility_summary(volatility_panel, return_columns, rolling_window=12, periods_per_year=12),
        series_form="log_return",
        label_map=label_map,
        unit_map=unit_map,
        block_map=block_map,
    )
    export_dataframe_table(
        volatility_summary,
        ROOT / PATHS["output_tables"] / "table_volatility_summary_imputed_all_series_log_returns.csv",
    )
    export_dataframe_table(
        volatility_summary.loc[volatility_summary["base_variable"].isin(weather_columns)].reset_index(drop=True),
        ROOT / PATHS["output_tables"] / "table_volatility_summary_imputed_weather_log_returns.csv",
    )

    arch_tests = add_series_metadata(
        run_arch_lm_suite(clean_returns, return_columns, max_lags=6),
        series_form="log_return",
        label_map=label_map,
        unit_map=unit_map,
        block_map=block_map,
    )
    export_dataframe_table(
        arch_tests,
        ROOT / PATHS["output_tables"] / "table_arch_lm_tests_imputed_all_series_log_returns.csv",
    )
    export_dataframe_table(
        arch_tests.loc[arch_tests["base_variable"].isin(weather_columns)].reset_index(drop=True),
        ROOT / PATHS["output_tables"] / "table_arch_lm_tests_imputed_weather_log_returns.csv",
    )

    weather_rolling_columns = [
        f"{column}_log_return_rolling_volatility"
        for column in weather_columns
        if f"{column}_log_return_rolling_volatility" in volatility_panel.columns
    ]
    if weather_rolling_columns:
        rolling_labels = {
            column: f"{label_map.get(column.replace('_log_return_rolling_volatility', ''), column)} rolling volatility"
            for column in weather_rolling_columns
        }
        weather_rolling_figure = plot_time_series_panels(
            volatility_panel.dropna(how="all", subset=weather_rolling_columns),
            date_column="date",
            value_columns=weather_rolling_columns,
            title="Rolling 12-month volatility of the imputed weather block",
            label_map=rolling_labels,
            ylabels={column: "std. dev. of log returns" for column in weather_rolling_columns},
            color_map=None,
        )
        export_matplotlib_figure(
            weather_rolling_figure,
            ROOT / PATHS["output_figures"] / "figure_rolling_volatility_weather_imputed.png",
        )

    decomposition_records: list[dict[str, object]] = []
    decomposition_strength_records: list[dict[str, object]] = []
    for column in all_columns:
        series = analysis_panel.set_index("date")[column].astype(float)
        if len(series.dropna()) < 24:
            continue

        stl_result = STL(series, period=12, robust=True).fit()
        observed = series.copy()
        observed.attrs["trend"] = stl_result.trend
        observed.attrs["seasonal"] = stl_result.seasonal
        observed.attrs["resid"] = stl_result.resid

        trend_strength, seasonal_strength = compute_decomposition_strength(
            stl_result.trend,
            stl_result.seasonal,
            stl_result.resid,
        )
        decomposition_strength_records.append(
            {
                "variable": column,
                "label": label_map.get(column, column),
                "source_block": block_map.get(column, "unmapped"),
                "trend_strength": trend_strength,
                "seasonal_strength": seasonal_strength,
                "residual_std": float(pd.Series(stl_result.resid).std()),
            }
        )
        decomposition_records.extend(
            {
                "date": date,
                "variable": column,
                "observed": float(observed.loc[date]),
                "trend": float(stl_result.trend.loc[date]),
                "seasonal": float(stl_result.seasonal.loc[date]),
                "remainder": float(stl_result.resid.loc[date]),
            }
            for date in observed.index
        )

        decomposition_figure = plot_stl_decomposition(
            observed,
            title=f"STL decomposition of {label_map.get(column, column)}",
            y_label=unit_map.get(column),
        )
        export_matplotlib_figure(
            decomposition_figure,
            ROOT / PATHS["output_figures"] / f"figure_stl_decomposition_{column}_imputed.png",
        )

    decomposition_strength = pd.DataFrame.from_records(decomposition_strength_records)
    export_dataframe_table(
        pd.DataFrame.from_records(decomposition_records),
        ROOT / PATHS["data_processed_final_series"] / "stl_decomposition_components_all_series_imputed.csv",
    )
    export_dataframe_table(
        decomposition_strength,
        ROOT / PATHS["output_tables"] / "table_decomposition_strength_imputed_all_series.csv",
    )
    export_dataframe_table(
        decomposition_strength.loc[decomposition_strength["variable"].isin(weather_columns)].reset_index(drop=True),
        ROOT / PATHS["output_tables"] / "table_decomposition_strength_imputed_weather.csv",
    )

    overview = build_overview_table(
        all_columns=all_columns,
        label_map=label_map,
        unit_map=unit_map,
        block_map=block_map,
        level_summary=level_summary,
        return_summary=return_summary,
        stationarity_levels=stationarity_levels,
        stationarity_returns=stationarity_returns,
        volatility_summary=volatility_summary,
        arch_tests=arch_tests,
        decomposition_strength=decomposition_strength,
        imputed_panel=all_series_imputed,
    )
    export_dataframe_table(
        overview,
        ROOT / PATHS["output_tables"] / "table_statistical_properties_all_series_overview.csv",
    )
    export_dataframe_table(
        overview.loc[overview["variable"].isin(weather_columns)].reset_index(drop=True),
        ROOT / PATHS["output_tables"] / "table_statistical_properties_weather_overview.csv",
    )

    significant_arch_weather = arch_tests.loc[
        arch_tests["base_variable"].isin(weather_columns)
        & (pd.to_numeric(arch_tests.get("p_value"), errors="coerce") < 0.05),
        "base_variable",
    ].tolist()
    notes = [
        "All-series imputed statistical-properties report",
        f"Core panel source: {core_imputed_path.name}",
        f"Weather panel source: {climate_path.name}",
        f"Date span: {analysis_panel['date'].min().date().isoformat()} to {analysis_panel['date'].max().date().isoformat()}",
        f"All-series level observations: {len(analysis_panel)}",
        f"All-series return observations after differencing: {len(clean_returns)}",
        "",
        "Weather imputation notes:",
    ]
    if weather_audit.empty:
        notes.append("- No weather missing values required imputation.")
    else:
        for _, row in weather_audit.iterrows():
            notes.append(
                f"- {pd.Timestamp(row['date']).date().isoformat()} | {row['variable']} | "
                f"KNN {row['knn_imputed_value']:.6f} | Iterative {row['iterative_imputed_value']:.6f}"
            )

    if significant_arch_weather:
        notes.extend(["", "Weather ARCH-LM significant at p < 0.05:"])
        notes.extend([f"- {label_map.get(column, column)}" for column in significant_arch_weather])

    if not decomposition_strength.empty:
        weather_strength = decomposition_strength.loc[decomposition_strength["variable"].isin(weather_columns)]
        if not weather_strength.empty:
            strongest_weather_seasonality = weather_strength.sort_values("seasonal_strength", ascending=False).iloc[0]
            notes.extend(
                [
                    "",
                    "Weather decomposition highlight:",
                    f"- Strongest seasonal weather series: {strongest_weather_seasonality['label']} "
                    f"({strongest_weather_seasonality['seasonal_strength']:.3f})",
                ]
            )

    export_text_summary(
        "\n".join(notes),
        ROOT / PATHS["output_appendix"] / "statistical_properties_all_series_imputed_notes.txt",
    )
    logger.info(
        "Exported all-series imputed statistical-properties outputs for %s total series",
        len(all_columns),
    )


if __name__ == "__main__":
    main()
