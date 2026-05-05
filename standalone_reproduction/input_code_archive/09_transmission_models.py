"""Estimate the core transmission chapter for the cocoa supply chain."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.descriptive.visualization import plot_time_series
from src.econometrics.causality_tests import run_granger_causality
from src.econometrics.cointegration_tests import run_engle_granger_test
from src.econometrics.impulse_response import compute_impulse_response, save_impulse_response_plot
from src.econometrics.regression_reporting import (
    fit_hac_ols,
    summarize_model_fit,
    summarize_regression_result,
)
from src.econometrics.var_vecm_models import fit_var_model
from src.outputs.export_figures import export_matplotlib_figure
from src.outputs.export_model_summaries import export_text_summary, model_result_to_text
from src.outputs.export_tables import export_dataframe_table
from src.utils.file_utils import load_yaml
from src.utils.logging_utils import get_project_logger

PATHS = load_yaml(ROOT / "config" / "paths.yaml")
CONFIG = load_yaml(ROOT / "config" / "project_config.yaml")
VARIABLE_DICTIONARY = load_yaml(ROOT / "config" / "variable_dictionary.yaml").get("variables", {})


def get_label(column: str) -> str:
    """Return a readable label for a variable."""
    return VARIABLE_DICTIONARY.get(column, {}).get("label", column)


def add_log_and_return_columns(dataframe: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Append log levels and first log differences for positive-valued columns."""
    output = dataframe.copy()
    for column in columns:
        if column not in output.columns:
            continue
        output[f"log_{column}"] = np.log(output[column])
        output[f"dlog_{column}"] = output[f"log_{column}"].diff()
    return output


def build_sample_summary(sample_name: str, dataframe: pd.DataFrame, columns: list[str]) -> dict[str, object]:
    """Summarize a modeling sample."""
    return {
        "sample_name": sample_name,
        "rows": len(dataframe),
        "start_date": dataframe["date"].min().date().isoformat() if not dataframe.empty else None,
        "end_date": dataframe["date"].max().date().isoformat() if not dataframe.empty else None,
        "variables": ", ".join(columns),
    }


def run_pairwise_engle_granger(
    dataframe: pd.DataFrame,
    sample_variant: str,
    pair_definitions: list[tuple[str, str, str]],
) -> pd.DataFrame:
    """Run bivariate Engle-Granger tests for selected log-level pairs."""
    records: list[dict[str, object]] = []
    for model_id, y_column, x_column in pair_definitions:
        result = run_engle_granger_test(dataframe[y_column], dataframe[x_column])
        result.update(
            {
                "sample_variant": sample_variant,
                "model_id": model_id,
                "dependent_variable": y_column,
                "explanatory_variable": x_column,
            }
        )
        records.append(result)
    return pd.DataFrame.from_records(records)


def run_directional_granger(
    dataframe: pd.DataFrame,
    sample_variant: str,
    direction_definitions: list[tuple[str, str, str]],
    maxlag: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run directional Granger causality tests and build detail plus summary tables."""
    detail_records: list[dict[str, object]] = []
    summary_records: list[dict[str, object]] = []

    for direction_id, cause_column, effect_column in direction_definitions:
        result = run_granger_causality(
            dataframe,
            variables=[cause_column, effect_column],
            maxlag=maxlag,
        )
        result["sample_variant"] = sample_variant
        result["direction_id"] = direction_id
        result["cause_variable"] = cause_column
        result["effect_variable"] = effect_column
        detail_records.extend(result.to_dict(orient="records"))

        best_row = result.sort_values("p_value").iloc[0]
        summary_records.append(
            {
                "sample_variant": sample_variant,
                "direction_id": direction_id,
                "cause_variable": cause_column,
                "effect_variable": effect_column,
                "best_lag": int(best_row["lag"]),
                "best_statistic": float(best_row["statistic"]),
                "best_p_value": float(best_row["p_value"]),
            }
        )

    return pd.DataFrame.from_records(detail_records), pd.DataFrame.from_records(summary_records)


def build_actual_vs_fitted_figure(
    dataframe: pd.DataFrame,
    fitted_values: pd.Series,
    y_column: str,
    title: str,
):
    """Create an actual-versus-fitted line chart."""
    figure_frame = dataframe.loc[fitted_values.index, ["date", y_column]].copy()
    figure_frame["fitted_value"] = fitted_values.values
    return plot_time_series(
        figure_frame,
        date_column="date",
        value_columns=[y_column, "fitted_value"],
        title=title,
        label_map={
            y_column: f"Observed {get_label(y_column)}",
            "fitted_value": "Model fitted value",
        },
    )


def main() -> None:
    """Run the baseline core transmission chapter."""
    logger = get_project_logger("09_transmission_models", ROOT / PATHS["output_logs"])
    balanced_path = ROOT / PATHS["data_processed_final_series"] / "core_common_sample_panel.csv"
    imputed_path = ROOT / PATHS["data_processed_final_series"] / "core_common_window_panel_imputed.csv"

    if not balanced_path.exists() or not imputed_path.exists():
        logger.warning("Required aligned core panels are missing.")
        return

    balanced = pd.read_csv(balanced_path, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    imputed = pd.read_csv(imputed_path, parse_dates=["date"]).sort_values("date").reset_index(drop=True)

    domestic = CONFIG["series"]["domestic_price"]
    world = CONFIG["series"]["international_price"]
    eu = CONFIG["series"]["eu_price"]
    fx = CONFIG["series"]["exchange_rate"]
    brent = CONFIG["series"]["oil_price"]
    core_columns = [domestic, world, eu, fx, brent]

    balanced = add_log_and_return_columns(balanced, core_columns)
    imputed = add_log_and_return_columns(imputed, core_columns)

    sample_summary = pd.DataFrame.from_records(
        [
            build_sample_summary("balanced_non_imputed", balanced, core_columns),
            build_sample_summary("imputed_shared_window", imputed, core_columns),
        ]
    )
    export_dataframe_table(
        sample_summary,
        ROOT / PATHS["output_tables"] / "table_core_transmission_samples.csv",
    )

    model_definitions = [
        {
            "model_id": "core_domestic_levels",
            "dependent": f"log_{domestic}",
            "x_columns": [f"log_{world}", f"log_{fx}", f"log_{brent}"],
            "specification": "log_domestic ~ log_world + log_fx + log_brent",
        },
        {
            "model_id": "core_domestic_returns",
            "dependent": f"dlog_{domestic}",
            "x_columns": [f"dlog_{world}", f"dlog_{fx}", f"dlog_{brent}"],
            "specification": "dlog_domestic ~ dlog_world + dlog_fx + dlog_brent",
        },
        {
            "model_id": "core_eu_levels",
            "dependent": f"log_{eu}",
            "x_columns": [f"log_{world}", f"log_{domestic}"],
            "specification": "log_eu ~ log_world + log_domestic",
        },
        {
            "model_id": "core_eu_returns",
            "dependent": f"dlog_{eu}",
            "x_columns": [f"dlog_{world}", f"dlog_{domestic}"],
            "specification": "dlog_eu ~ dlog_world + dlog_domestic",
        },
    ]

    coefficient_tables: list[pd.DataFrame] = []
    fit_tables: list[pd.DataFrame] = []
    result_lookup: dict[str, object] = {}
    result_index_lookup: dict[str, pd.Index] = {}

    for sample_variant, panel in [("balanced_non_imputed", balanced), ("imputed_shared_window", imputed)]:
        for definition in model_definitions:
            result, used_index = fit_hac_ols(
                panel,
                y_column=definition["dependent"],
                x_columns=definition["x_columns"],
                maxlags=1,
            )
            coefficient_tables.append(
                summarize_regression_result(
                    result,
                    model_id=definition["model_id"],
                    chapter="core_transmission",
                    sample_variant=sample_variant,
                    dependent_variable=definition["dependent"],
                    specification=definition["specification"],
                )
            )
            fit_tables.append(
                summarize_model_fit(
                    result,
                    model_id=definition["model_id"],
                    chapter="core_transmission",
                    sample_variant=sample_variant,
                    dependent_variable=definition["dependent"],
                    specification=definition["specification"],
                )
            )
            result_lookup[f"{definition['model_id']}::{sample_variant}"] = result
            result_index_lookup[f"{definition['model_id']}::{sample_variant}"] = used_index

            export_text_summary(
                model_result_to_text(result),
                ROOT
                / PATHS["output_appendix"]
                / f"{definition['model_id']}_{sample_variant}_summary.txt",
            )

    coefficient_table = pd.concat(coefficient_tables, ignore_index=True)
    fit_table = pd.concat(fit_tables, ignore_index=True)
    export_dataframe_table(
        coefficient_table,
        ROOT / PATHS["output_tables"] / "table_core_transmission_coefficients.csv",
    )
    export_dataframe_table(
        fit_table,
        ROOT / PATHS["output_tables"] / "table_core_transmission_model_fit.csv",
    )

    compatibility_coefficients = coefficient_table.loc[
        (coefficient_table["model_id"] == "core_domestic_returns")
        & (coefficient_table["sample_variant"] == "imputed_shared_window")
    ].reset_index(drop=True)
    export_dataframe_table(
        compatibility_coefficients,
        ROOT / PATHS["output_tables"] / "table_pass_through_results.csv",
    )

    domestic_return_result = result_lookup["core_domestic_returns::imputed_shared_window"]
    domestic_return_index = result_index_lookup["core_domestic_returns::imputed_shared_window"]
    domestic_return_figure = build_actual_vs_fitted_figure(
        imputed,
        domestic_return_result.fittedvalues,
        y_column=f"dlog_{domestic}",
        title="Core domestic transmission model: observed vs fitted returns",
    )
    export_matplotlib_figure(
        domestic_return_figure,
        ROOT / PATHS["output_figures"] / "figure_core_domestic_return_actual_vs_fitted.png",
    )

    eu_return_result = result_lookup["core_eu_returns::imputed_shared_window"]
    eu_return_figure = build_actual_vs_fitted_figure(
        imputed,
        eu_return_result.fittedvalues,
        y_column=f"dlog_{eu}",
        title="Core EU transmission model: observed vs fitted returns",
    )
    export_matplotlib_figure(
        eu_return_figure,
        ROOT / PATHS["output_figures"] / "figure_core_eu_return_actual_vs_fitted.png",
    )

    engle_granger_pairs = [
        ("world_to_colombia_levels", f"log_{domestic}", f"log_{world}"),
        ("world_to_eu_levels", f"log_{eu}", f"log_{world}"),
        ("colombia_to_eu_levels", f"log_{eu}", f"log_{domestic}"),
    ]
    engle_granger_table = pd.concat(
        [
            run_pairwise_engle_granger(balanced, "balanced_non_imputed", engle_granger_pairs),
            run_pairwise_engle_granger(imputed, "imputed_shared_window", engle_granger_pairs),
        ],
        ignore_index=True,
    )
    export_dataframe_table(
        engle_granger_table,
        ROOT / PATHS["output_tables"] / "table_core_engle_granger_pairs.csv",
    )
    export_dataframe_table(
        engle_granger_table.loc[engle_granger_table["sample_variant"] == "imputed_shared_window"].reset_index(drop=True),
        ROOT / PATHS["output_tables"] / "table_engle_granger_results.csv",
    )

    granger_directions = [
        ("world_to_colombia", f"dlog_{world}", f"dlog_{domestic}"),
        ("colombia_to_world", f"dlog_{domestic}", f"dlog_{world}"),
        ("colombia_to_eu", f"dlog_{domestic}", f"dlog_{eu}"),
        ("eu_to_colombia", f"dlog_{eu}", f"dlog_{domestic}"),
        ("world_to_eu", f"dlog_{world}", f"dlog_{eu}"),
        ("eu_to_world", f"dlog_{eu}", f"dlog_{world}"),
    ]
    granger_detail, granger_summary = run_directional_granger(
        imputed,
        sample_variant="imputed_shared_window",
        direction_definitions=granger_directions,
        maxlag=3,
    )
    export_dataframe_table(
        granger_detail,
        ROOT / PATHS["output_tables"] / "table_core_granger_causality_detail.csv",
    )
    export_dataframe_table(
        granger_summary,
        ROOT / PATHS["output_tables"] / "table_core_granger_causality_summary.csv",
    )
    export_dataframe_table(
        granger_detail.loc[granger_detail["direction_id"] == "world_to_colombia"].reset_index(drop=True),
        ROOT / PATHS["output_tables"] / "table_granger_causality.csv",
    )

    var_return_columns = [f"dlog_{world}", f"dlog_{domestic}", f"dlog_{eu}"]
    irf_acronym_map = {
        f"dlog_{world}": "R_WLD",
        f"dlog_{domestic}": "R_COL",
        f"dlog_{eu}": "R_EUC",
    }
    irf_label_map = {
        f"dlog_{world}": "World cocoa return",
        f"dlog_{domestic}": "Colombian cocoa return",
        f"dlog_{eu}": "EU chocolate return",
    }
    var_system = imputed[var_return_columns].dropna().copy()
    var_notes: list[str] = []
    if len(var_system) >= 24:
        try:
            var_result = fit_var_model(var_system, maxlags=min(3, CONFIG["analysis"]["max_var_lags"]))
            export_text_summary(
                model_result_to_text(var_result),
                ROOT / PATHS["output_appendix"] / "core_var_return_model_summary.txt",
            )
            export_text_summary(
                model_result_to_text(var_result),
                ROOT / PATHS["output_appendix"] / "var_model_summary.txt",
            )
            irf = compute_impulse_response(var_result, steps=CONFIG["analysis"]["impulse_response_horizon"])
            save_impulse_response_plot(
                irf,
                ROOT / PATHS["output_figures"] / "figure_core_return_impulse_response.png",
                variable_names=var_return_columns,
                acronym_map=irf_acronym_map,
                label_map=irf_label_map,
                title="Core return impulse-response matrix",
            )
            save_impulse_response_plot(
                irf,
                ROOT / PATHS["output_figures"] / "figure_impulse_response.png",
                variable_names=var_return_columns,
                acronym_map=irf_acronym_map,
                label_map=irf_label_map,
                title="Core return impulse-response matrix",
            )
            var_notes.append(f"VAR on core returns estimated with lag order {var_result.k_ar}.")
        except Exception as error:  # pragma: no cover
            export_text_summary(
                f"VAR estimation skipped because {error}",
                ROOT / PATHS["output_appendix"] / "core_var_return_model_summary.txt",
            )
            export_text_summary(
                f"VAR estimation skipped because {error}",
                ROOT / PATHS["output_appendix"] / "var_model_summary.txt",
            )
            var_notes.append(f"VAR estimation skipped because {error}.")

    key_world_domestic = compatibility_coefficients.loc[
        compatibility_coefficients["parameter"] == f"dlog_{world}"
    ].iloc[0]
    key_long_run = coefficient_table.loc[
        (coefficient_table["model_id"] == "core_domestic_levels")
        & (coefficient_table["sample_variant"] == "imputed_shared_window")
        & (coefficient_table["parameter"] == f"log_{world}")
    ].iloc[0]
    cointegration_row = engle_granger_table.loc[
        (engle_granger_table["sample_variant"] == "imputed_shared_window")
        & (engle_granger_table["model_id"] == "world_to_colombia_levels")
    ].iloc[0]
    granger_row = granger_summary.loc[granger_summary["direction_id"] == "world_to_colombia"].iloc[0]

    chapter_lines = [
        "# Chapter 1: Core Supply-Chain Transmission",
        "",
        "## Modeling sample",
        "",
        f"- Balanced non-imputed sample: {len(balanced)} monthly observations",
        f"- Imputed shared-window sample: {len(imputed)} monthly observations",
        f"- Date span: {imputed['date'].min().date().isoformat()} to {imputed['date'].max().date().isoformat()}",
        "",
        "## Main core findings",
        "",
        f"- In the imputed short-run domestic return model, the world cocoa return coefficient is {key_world_domestic['coefficient']:.3f} "
        f"(p = {key_world_domestic['p_value']:.4f}), which is the clearest transmission signal in the core system.",
        f"- In the imputed long-run domestic log-level model, the world cocoa elasticity is {key_long_run['coefficient']:.3f}.",
        f"- The bivariate Engle-Granger test for world cocoa and Colombian cocoa does not show strong cointegration in this short aligned sample "
        f"(p = {cointegration_row['p_value']:.4f}).",
        f"- Granger causality from world cocoa returns to Colombian cocoa returns is strongest at lag {int(granger_row['best_lag'])} "
        f"with p = {granger_row['best_p_value']:.4f}.",
        "",
        "## Interpretation",
        "",
        f"- The short-run evidence is more convincing than the long-run cointegration evidence in the current sample.",
        f"- This supports a cautious transmission reading: Colombian cocoa prices appear exposed to global cocoa shocks, but the short aligned span still limits strong long-run claims.",
        f"- EU downstream prices move more slowly and show weaker short-run response to the producing-side system in this aligned window.",
    ]
    if var_notes:
        chapter_lines.extend(["", "## VAR diagnostics", ""])
        chapter_lines.extend([f"- {note}" for note in var_notes])
    chapter_lines.extend(
        [
            "",
            "## Main chapter outputs",
            "",
            "- `outputs/tables/table_core_transmission_coefficients.csv`",
            "- `outputs/tables/table_core_transmission_model_fit.csv`",
            "- `outputs/tables/table_core_engle_granger_pairs.csv`",
            "- `outputs/tables/table_core_granger_causality_summary.csv`",
            "- `outputs/figures/figure_core_domestic_return_actual_vs_fitted.png`",
            "- `outputs/figures/figure_core_return_impulse_response.png`",
        ]
    )
    export_text_summary(
        "\n".join(chapter_lines),
        ROOT / PATHS["output_appendix"] / "chapter_1_core_transmission_results.md",
    )

    logger.info("Exported core transmission chapter outputs")


if __name__ == "__main__":
    main()
