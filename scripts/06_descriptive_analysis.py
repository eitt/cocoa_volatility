"""Run descriptive analysis on the merged cocoa price panel."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.descriptive.summary_stats import compute_summary_statistics
from src.descriptive.visualization import plot_time_series
from src.outputs.export_figures import export_matplotlib_figure
from src.outputs.export_tables import export_dataframe_table
from src.utils.file_utils import load_yaml
from src.utils.logging_utils import get_project_logger

PATHS = load_yaml(ROOT / "config" / "paths.yaml")


def main() -> None:
    """Generate descriptive tables and a basic trend figure."""
    logger = get_project_logger("06_descriptive_analysis", ROOT / PATHS["output_logs"])
    merged_path = ROOT / PATHS["data_processed_analysis_ready"] / "merged_cocoa_price_panel.csv"
    if not merged_path.exists():
        logger.warning("Merged dataset not found at %s", merged_path)
        return

    dataframe = pd.read_csv(merged_path, parse_dates=["date"])
    numeric_columns = dataframe.select_dtypes(include="number").columns.tolist()

    summary_table = compute_summary_statistics(dataframe, numeric_columns)
    export_dataframe_table(summary_table, ROOT / PATHS["output_tables"] / "table_summary_statistics.csv")
    logger.info("Wrote summary statistics for %s numeric columns", len(numeric_columns))

    price_columns = [column for column in numeric_columns if not column.startswith("log_")]
    if "date" in dataframe.columns and price_columns:
        figure = plot_time_series(
            dataframe=dataframe,
            date_column="date",
            value_columns=price_columns[:3],
            title="Monthly cocoa price indicators",
        )
        export_matplotlib_figure(figure, ROOT / PATHS["output_figures"] / "figure_price_trends.png")
        logger.info("Exported descriptive trend figure")


if __name__ == "__main__":
    main()
