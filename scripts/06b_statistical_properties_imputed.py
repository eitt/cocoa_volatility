"""Report statistical properties of the imputed aligned core time series."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.descriptive.summary_stats import compute_extended_summary_statistics
from src.descriptive.visualization import build_color_map, plot_stl_decomposition, plot_time_series_panels
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


def build_label_maps(value_columns: list[str]) -> tuple[dict[str, str], dict[str, str]]:
    """Build readable labels and unit labels for selected variables."""
    label_map: dict[str, str] = {}
    unit_map: dict[str, str] = {}
    for column in value_columns:
        metadata = VARIABLE_DICTIONARY.get(column, {})
        label_map[column] = metadata.get("label", column)
        unit_map[column] = metadata.get("unit", "")
    return label_map, unit_map


def add_series_metadata(
    dataframe: pd.DataFrame,
    series_form: str,
) -> pd.DataFrame:
    """Add form and base-variable metadata to an exported table."""
    if dataframe.empty:
        return dataframe

    enriched = dataframe.copy()
    if "variable" in enriched.columns:
        enriched["series_form"] = series_form
        enriched["base_variable"] = enriched["variable"].str.replace("_log_return", "", regex=False)
    return enriched


def compute_decomposition_strength(
    trend: pd.Series,
    seasonal: pd.Series,
    residual: pd.Series,
) -> tuple[float | None, float | None]:
    """Compute trend and seasonal strength from an additive decomposition."""
    residual_variance = float(np.nanvar(residual))
    trend_denom = float(np.nanvar(trend + residual))
    seasonal_denom = float(np.nanvar(seasonal + residual))

    trend_strength = max(0.0, 1.0 - residual_variance / trend_denom) if trend_denom > 0 else None
    seasonal_strength = max(0.0, 1.0 - residual_variance / seasonal_denom) if seasonal_denom > 0 else None
    return trend_strength, seasonal_strength


def main() -> None:
    """Generate descriptive, stationarity, volatility, and decomposition outputs on the imputed panel."""
    logger = get_project_logger("06b_statistical_properties_imputed", ROOT / PATHS["output_logs"])
    imputed_path = ROOT / PATHS["data_processed_final_series"] / "core_common_window_panel_imputed.csv"
    if not imputed_path.exists():
        logger.warning("Imputed aligned panel not found at %s", imputed_path)
        return

    dataframe = pd.read_csv(imputed_path, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    core_columns = [
        CONFIG["series"]["domestic_price"],
        CONFIG["series"]["international_price"],
        CONFIG["series"]["eu_price"],
        CONFIG["series"]["exchange_rate"],
        CONFIG["series"]["oil_price"],
    ]
    core_columns = [column for column in core_columns if column in dataframe.columns]
    if not core_columns:
        logger.warning("No configured core series found in %s", imputed_path)
        return

    label_map, unit_map = build_label_maps(core_columns)
    color_map = build_color_map(core_columns)

    level_summary = add_series_metadata(
        compute_extended_summary_statistics(dataframe, core_columns),
        series_form="level",
    )
    export_dataframe_table(
        level_summary,
        ROOT / PATHS["output_tables"] / "table_statistical_properties_imputed_levels.csv",
    )

    returns = dataframe[["date"]].copy()
    for column in core_columns:
        working = compute_log_returns(
            dataframe[["date", column]].copy(),
            value_column=column,
            date_column="date",
        )
        return_column = f"{column}_log_return"
        returns[return_column] = working[return_column]

    return_columns = [column for column in returns.columns if column.endswith("_log_return")]
    export_dataframe_table(
        returns,
        ROOT / PATHS["data_processed_final_series"] / "core_common_window_log_returns_imputed.csv",
    )

    return_summary = add_series_metadata(
        compute_extended_summary_statistics(returns, return_columns),
        series_form="log_return",
    )
    export_dataframe_table(
        return_summary,
        ROOT / PATHS["output_tables"] / "table_statistical_properties_imputed_log_returns.csv",
    )

    stationarity_levels = add_series_metadata(
        run_stationarity_suite(dataframe, core_columns),
        series_form="level",
    )
    export_dataframe_table(
        stationarity_levels,
        ROOT / PATHS["output_tables"] / "table_stationarity_tests_imputed_levels.csv",
    )

    stationarity_returns = add_series_metadata(
        run_stationarity_suite(returns.dropna(), return_columns),
        series_form="log_return",
    )
    export_dataframe_table(
        stationarity_returns,
        ROOT / PATHS["output_tables"] / "table_stationarity_tests_imputed_log_returns.csv",
    )

    volatility_panel = returns.copy()
    rolling_columns: list[str] = []
    for column in return_columns:
        volatility_panel = compute_rolling_volatility(
            volatility_panel,
            return_column=column,
            window=12,
        )
        rolling_columns.append(f"{column}_log_return_rolling_volatility".replace("_log_return_log_return", "_log_return"))

    export_dataframe_table(
        volatility_panel,
        ROOT / PATHS["data_processed_final_series"] / "core_common_window_volatility_imputed.csv",
    )

    volatility_summary = add_series_metadata(
        compute_volatility_summary(volatility_panel, return_columns, rolling_window=12, periods_per_year=12),
        series_form="log_return",
    )
    export_dataframe_table(
        volatility_summary,
        ROOT / PATHS["output_tables"] / "table_volatility_summary_imputed_log_returns.csv",
    )

    arch_tests = add_series_metadata(
        run_arch_lm_suite(returns.dropna(), return_columns, max_lags=6),
        series_form="log_return",
    )
    export_dataframe_table(
        arch_tests,
        ROOT / PATHS["output_tables"] / "table_arch_lm_tests_imputed_log_returns.csv",
    )

    valid_rolling_columns = [column for column in rolling_columns if column in volatility_panel.columns]
    if valid_rolling_columns:
        rolling_labels = {
            column: f"{label_map.get(column.replace('_log_return_rolling_volatility', ''), column)} rolling volatility"
            for column in valid_rolling_columns
        }
        rolling_figure = plot_time_series_panels(
            volatility_panel.dropna(how="all", subset=valid_rolling_columns),
            date_column="date",
            value_columns=valid_rolling_columns,
            title="Rolling 12-month volatility of the imputed aligned core series",
            label_map=rolling_labels,
            ylabels={column: "std. dev. of log returns" for column in valid_rolling_columns},
            color_map={
                column: color_map.get(column.replace("_log_return_rolling_volatility", ""), list(color_map.values())[0])
                for column in valid_rolling_columns
            },
        )
        export_matplotlib_figure(
            rolling_figure,
            ROOT / PATHS["output_figures"] / "figure_rolling_volatility_core_imputed.png",
        )

    decomposition_records: list[dict[str, object]] = []
    decomposition_strength_records: list[dict[str, object]] = []
    for column in core_columns:
        series = dataframe.set_index("date")[column].astype(float)
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

    export_dataframe_table(
        pd.DataFrame.from_records(decomposition_records),
        ROOT / PATHS["data_processed_final_series"] / "stl_decomposition_components_imputed.csv",
    )
    export_dataframe_table(
        pd.DataFrame.from_records(decomposition_strength_records),
        ROOT / PATHS["output_tables"] / "table_decomposition_strength_imputed.csv",
    )

    notes = [
        "Imputed statistical-properties report",
        f"Sample file: {imputed_path.name}",
        f"Date span: {dataframe['date'].min().date().isoformat()} to {dataframe['date'].max().date().isoformat()}",
        f"Level observations: {len(dataframe)}",
        f"Return observations after differencing: {len(returns.dropna())}",
        "",
        "Series covered:",
    ]
    for column in core_columns:
        notes.append(f"- {label_map.get(column, column)}")

    significant_arch = arch_tests.loc[
        pd.to_numeric(arch_tests.get("p_value"), errors="coerce") < 0.05,
        "base_variable",
    ].tolist() if not arch_tests.empty else []
    if significant_arch:
        notes.extend(
            [
                "",
                "ARCH-LM significant at p < 0.05:",
                *[f"- {label_map.get(column, column)}" for column in significant_arch],
            ]
        )

    if decomposition_strength_records:
        strongest_trend = max(
            decomposition_strength_records,
            key=lambda record: record.get("trend_strength") or float("-inf"),
        )
        strongest_seasonality = max(
            decomposition_strength_records,
            key=lambda record: record.get("seasonal_strength") or float("-inf"),
        )
        notes.extend(
            [
                "",
                f"Strongest trend component: {strongest_trend['label']} ({strongest_trend['trend_strength']:.3f})",
                f"Strongest seasonal component: {strongest_seasonality['label']} ({strongest_seasonality['seasonal_strength']:.3f})",
            ]
        )

    export_text_summary(
        "\n".join(notes),
        ROOT / PATHS["output_appendix"] / "statistical_properties_imputed_notes.txt",
    )
    logger.info("Exported imputed statistical-properties outputs for %s series", len(core_columns))


if __name__ == "__main__":
    main()
