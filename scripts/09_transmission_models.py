"""Estimate pass-through and dynamic transmission models."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.econometrics.causality_tests import run_granger_causality
from src.econometrics.impulse_response import compute_impulse_response, save_impulse_response_plot
from src.econometrics.pass_through_models import estimate_pass_through_elasticity, summarize_pass_through_result
from src.econometrics.var_vecm_models import fit_var_model
from src.outputs.export_model_summaries import export_text_summary, model_result_to_text
from src.outputs.export_tables import export_dataframe_table
from src.utils.file_utils import load_yaml
from src.utils.logging_utils import get_project_logger

PATHS = load_yaml(ROOT / "config" / "paths.yaml")
CONFIG = load_yaml(ROOT / "config" / "project_config.yaml")


def main() -> None:
    """Run baseline transmission models on available monthly series."""
    logger = get_project_logger("09_transmission_models", ROOT / PATHS["output_logs"])
    merged_path = ROOT / PATHS["data_processed_analysis_ready"] / "merged_cocoa_price_panel.csv"
    if not merged_path.exists():
        logger.warning("Merged dataset not found at %s", merged_path)
        return

    dataframe = pd.read_csv(merged_path, parse_dates=["date"])
    y_column = CONFIG["series"]["domestic_price"]
    x_columns = [
        CONFIG["series"]["international_price"],
        CONFIG["series"]["eu_price"],
    ]
    available_x = [column for column in x_columns if column in dataframe.columns]

    if y_column in dataframe.columns and available_x:
        result = estimate_pass_through_elasticity(dataframe, y_column=y_column, x_columns=available_x)
        coefficient_table = summarize_pass_through_result(result)
        export_dataframe_table(
            coefficient_table,
            ROOT / PATHS["output_tables"] / "table_pass_through_results.csv",
        )
        export_text_summary(
            model_result_to_text(result),
            ROOT / PATHS["output_appendix"] / "pass_through_summary.txt",
        )
        logger.info("Estimated pass-through model with %s regressors", len(available_x))

    granger_pair = [CONFIG["series"]["international_price"], CONFIG["series"]["domestic_price"]]
    if all(column in dataframe.columns for column in granger_pair):
        test_data = dataframe[granger_pair].dropna()
        if len(test_data) >= 24:
            granger_table = run_granger_causality(test_data, variables=granger_pair, maxlag=6)
            export_dataframe_table(
                granger_table,
                ROOT / PATHS["output_tables"] / "table_granger_causality.csv",
            )
            logger.info("Computed Granger causality for %s", ", ".join(granger_pair))

    system_columns = [column for column in [y_column, *available_x] if column in dataframe.columns]
    system = dataframe[system_columns].dropna()
    if len(system_columns) >= 2 and len(system) >= 24:
        try:
            var_result = fit_var_model(system, maxlags=CONFIG["analysis"]["max_var_lags"])
            export_text_summary(
                model_result_to_text(var_result),
                ROOT / PATHS["output_appendix"] / "var_model_summary.txt",
            )
            irf = compute_impulse_response(var_result, steps=CONFIG["analysis"]["impulse_response_horizon"])
            save_impulse_response_plot(
                irf,
                ROOT / PATHS["output_figures"] / "figure_impulse_response.png",
            )
            logger.info("Estimated VAR and exported impulse-response figure")
        except Exception as error:  # pragma: no cover
            export_text_summary(
                f"VAR estimation skipped because {error}",
                ROOT / PATHS["output_appendix"] / "var_model_summary.txt",
            )
            logger.warning("VAR estimation failed: %s", error)


if __name__ == "__main__":
    main()
