"""Run stationarity and co-integration diagnostics."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.econometrics.cointegration_tests import run_engle_granger_test, run_johansen_test
from src.econometrics.stationarity_tests import run_stationarity_suite
from src.outputs.export_model_summaries import export_text_summary
from src.outputs.export_tables import export_dataframe_table
from src.utils.file_utils import load_yaml
from src.utils.logging_utils import get_project_logger

PATHS = load_yaml(ROOT / "config" / "paths.yaml")
CONFIG = load_yaml(ROOT / "config" / "project_config.yaml")


def main() -> None:
    """Run stationarity tests and baseline co-integration checks."""
    logger = get_project_logger("07_stationarity_and_cointegration", ROOT / PATHS["output_logs"])
    merged_path = ROOT / PATHS["data_processed_analysis_ready"] / "merged_cocoa_price_panel.csv"
    if not merged_path.exists():
        logger.warning("Merged dataset not found at %s", merged_path)
        return

    dataframe = pd.read_csv(merged_path, parse_dates=["date"])
    candidate_columns = [
        CONFIG["series"]["domestic_price"],
        CONFIG["series"]["international_price"],
        CONFIG["series"]["eu_price"],
    ]
    available_columns = [column for column in candidate_columns if column in dataframe.columns]

    stationarity_table = run_stationarity_suite(dataframe, available_columns)
    export_dataframe_table(stationarity_table, ROOT / PATHS["output_tables"] / "table_stationarity_tests.csv")

    notes = [f"Stationarity variables: {', '.join(available_columns) or 'none'}"]

    if len(available_columns) >= 2:
        pair = dataframe[available_columns[:2]].dropna()
        if len(pair) >= 24:
            engle_granger_result = pd.DataFrame(
                [run_engle_granger_test(pair.iloc[:, 0], pair.iloc[:, 1])]
            )
            export_dataframe_table(
                engle_granger_result,
                ROOT / PATHS["output_tables"] / "table_engle_granger_results.csv",
            )
            notes.append(f"Engle-Granger run on {available_columns[0]} and {available_columns[1]}.")

    if len(available_columns) >= 2:
        system = dataframe[available_columns].dropna()
        if len(system) >= 24:
            johansen_table = run_johansen_test(system, k_ar_diff=1)
            export_dataframe_table(
                johansen_table,
                ROOT / PATHS["output_tables"] / "table_johansen_results.csv",
            )
            notes.append(f"Johansen run on {', '.join(available_columns)}.")

    export_text_summary(
        "\n".join(notes),
        ROOT / PATHS["output_appendix"] / "stationarity_and_cointegration_notes.txt",
    )
    logger.info("Completed stationarity and co-integration diagnostics")


if __name__ == "__main__":
    main()
