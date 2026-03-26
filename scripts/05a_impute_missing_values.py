"""Impute missing values in the aligned common-window panel."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_processing.imputation import (
    add_imputation_flags,
    build_imputation_audit,
    run_iterative_imputation,
    run_knn_imputation,
)
from src.outputs.export_model_summaries import export_text_summary
from src.outputs.export_tables import export_dataframe_table
from src.utils.file_utils import load_yaml
from src.utils.logging_utils import get_project_logger

PATHS = load_yaml(ROOT / "config" / "paths.yaml")
CONFIG = load_yaml(ROOT / "config" / "project_config.yaml")


def build_overlap_window(
    dataframe: pd.DataFrame,
    date_column: str,
    value_columns: list[str],
) -> tuple[pd.DataFrame, pd.Timestamp | None, pd.Timestamp | None]:
    """Build the shared calendar window across selected series."""
    starts = []
    ends = []

    for column in value_columns:
        observed = dataframe.loc[dataframe[column].notna(), date_column]
        if observed.empty:
            return pd.DataFrame(columns=[date_column] + value_columns), None, None
        starts.append(observed.min())
        ends.append(observed.max())

    overlap_start = max(starts)
    overlap_end = min(ends)
    window = (
        dataframe.loc[(dataframe[date_column] >= overlap_start) & (dataframe[date_column] <= overlap_end), [date_column] + value_columns]
        .copy()
        .reset_index(drop=True)
    )
    return window, overlap_start, overlap_end


def main() -> None:
    """Impute missing values in the common-window panel using two transparent methods."""
    logger = get_project_logger("05a_impute_missing_values", ROOT / PATHS["output_logs"])
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
    common_window, overlap_start, overlap_end = build_overlap_window(dataframe, "date", core_columns)
    if common_window.empty:
        logger.warning("No shared common window could be built for imputation.")
        return

    missingness = (
        common_window[core_columns]
        .isna()
        .sum()
        .rename_axis("variable")
        .reset_index(name="missing_observations")
    )
    export_dataframe_table(
        missingness,
        ROOT / PATHS["output_tables"] / "table_common_window_missingness.csv",
    )

    knn_imputed = run_knn_imputation(common_window, core_columns, n_neighbors=5)
    iterative_imputed = run_iterative_imputation(common_window, core_columns, random_state=42, max_iter=50)

    knn_flagged = add_imputation_flags(common_window, knn_imputed, core_columns)
    iterative_flagged = add_imputation_flags(common_window, iterative_imputed, core_columns)
    primary_imputed = iterative_flagged.copy()

    export_dataframe_table(
        knn_flagged,
        ROOT / PATHS["data_processed_final_series"] / "core_common_window_panel_imputed_knn.csv",
    )
    export_dataframe_table(
        iterative_flagged,
        ROOT / PATHS["data_processed_final_series"] / "core_common_window_panel_imputed_iterative.csv",
    )
    export_dataframe_table(
        primary_imputed,
        ROOT / PATHS["data_processed_final_series"] / "core_common_window_panel_imputed.csv",
    )

    audit = build_imputation_audit(
        common_window,
        core_columns,
        date_column="date",
        method_frames={
            "knn": knn_imputed,
            "iterative": iterative_imputed,
        },
    )
    export_dataframe_table(
        audit,
        ROOT / PATHS["output_tables"] / "table_imputation_audit.csv",
    )

    reference_correlations = common_window[core_columns].dropna().corr()
    reference_correlations.index.name = "variable"
    export_dataframe_table(
        reference_correlations.reset_index(),
        ROOT / PATHS["output_tables"] / "table_imputation_reference_correlations.csv",
    )

    if audit.empty:
        notes = [
            "No missing values were present in the common-window panel.",
            f"Window checked: {overlap_start.date().isoformat()} to {overlap_end.date().isoformat()}",
        ]
    else:
        first_row = audit.iloc[0]
        notes = [
            f"Common-window dates: {overlap_start.date().isoformat()} to {overlap_end.date().isoformat()}",
            f"Missing cell: {pd.Timestamp(first_row['date']).date().isoformat()} | {first_row['variable']}",
            f"KNN estimate: {first_row['knn_imputed_value']:.6f}",
            f"Iterative multivariate estimate: {first_row['iterative_imputed_value']:.6f}",
            "Primary imputed panel exported with the iterative multivariate estimate.",
        ]

    export_text_summary(
        "\n".join(notes),
        ROOT / PATHS["output_appendix"] / "imputation_notes.txt",
    )
    logger.info("Exported imputed common-window panels and audit tables")


if __name__ == "__main__":
    main()
