"""Estimate ARIMA and rolling-volatility outputs."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.descriptive.visualization import plot_time_series
from src.descriptive.volatility_measures import compute_log_returns, compute_rolling_volatility
from src.econometrics.arima_models import estimate_arima_model
from src.outputs.export_figures import export_matplotlib_figure
from src.outputs.export_model_summaries import export_text_summary, model_result_to_text
from src.outputs.export_tables import export_dataframe_table
from src.utils.file_utils import load_yaml
from src.utils.logging_utils import get_project_logger

PATHS = load_yaml(ROOT / "config" / "paths.yaml")
CONFIG = load_yaml(ROOT / "config" / "project_config.yaml")


def main() -> None:
    """Run univariate volatility and ARIMA routines on the main domestic series."""
    logger = get_project_logger("08_arima_and_volatility", ROOT / PATHS["output_logs"])
    merged_path = ROOT / PATHS["data_processed_analysis_ready"] / "merged_cocoa_price_panel.csv"
    if not merged_path.exists():
        logger.warning("Merged dataset not found at %s", merged_path)
        return

    dataframe = pd.read_csv(merged_path, parse_dates=["date"])
    target_column = CONFIG["series"]["domestic_price"]
    if target_column not in dataframe.columns:
        logger.warning("Target series %s not found in merged panel", target_column)
        return

    returns = compute_log_returns(dataframe, value_column=target_column, date_column="date")
    returns = compute_rolling_volatility(returns, return_column=f"{target_column}_log_return", window=12)
    export_dataframe_table(
        returns,
        ROOT / PATHS["data_processed_final_series"] / "volatility_series.csv",
    )

    figure_columns = [f"{target_column}_log_return_rolling_volatility"]
    figure = plot_time_series(
        returns.dropna(subset=figure_columns),
        date_column="date",
        value_columns=figure_columns,
        title="Rolling volatility of Colombian cocoa prices",
    )
    export_matplotlib_figure(figure, ROOT / PATHS["output_figures"] / "figure_rolling_volatility.png")

    clean_series = dataframe[target_column].dropna()
    if len(clean_series) >= 24:
        order = tuple(CONFIG["analysis"]["arima_orders"][0])
        result = estimate_arima_model(clean_series, order=order)
        export_text_summary(
            model_result_to_text(result),
            ROOT / PATHS["output_appendix"] / "arima_model_summary.txt",
        )
        logger.info("Estimated ARIMA%s on %s", order, target_column)
    else:
        export_text_summary(
            f"Insufficient observations for ARIMA on {target_column}.",
            ROOT / PATHS["output_appendix"] / "arima_model_summary.txt",
        )
        logger.info("Skipped ARIMA because the target series is too short")


if __name__ == "__main__":
    main()
