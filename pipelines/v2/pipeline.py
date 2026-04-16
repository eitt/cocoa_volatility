"""Orchestration for the v2 disaster analytics pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from pipelines.v2.aggregation import (
    aggregate_monthly_events,
    build_dataset_overview,
    build_event_type_summary,
    build_municipality_summary,
    build_translation_strategy_summary,
)
from pipelines.v2.analysis import run_analysis
from pipelines.v2.classification import build_semantic_event_model
from pipelines.v2.config import ensure_output_directories, find_input_file, load_v2_config, resolve_paths
from pipelines.v2.io import clean_records, read_source_csv
from pipelines.v2.reporting import build_markdown_report, render_pandoc_outputs, write_markdown_report, write_summary_json
from pipelines.v2.translation import load_translation_dictionary, translate_categorical_fields
from src.outputs.export_tables import export_dataframe_table
from src.utils.logging_utils import get_project_logger, log_dataframe_shape


def _export_intermediate_tables(
    paths: dict[str, Path],
    cleaned: pd.DataFrame,
    translated: pd.DataFrame,
    classified: pd.DataFrame,
    monthly: pd.DataFrame,
    event_type_matrix: pd.DataFrame,
    translation_audit: pd.DataFrame,
) -> None:
    export_dataframe_table(cleaned, paths["intermediate_dir"] / "01_cleaned_events.csv")
    export_dataframe_table(translated, paths["intermediate_dir"] / "02_translated_events.csv")
    export_dataframe_table(classified, paths["intermediate_dir"] / "03_classified_events.csv")
    export_dataframe_table(monthly, paths["intermediate_dir"] / "04_monthly_event_panel.csv")
    export_dataframe_table(event_type_matrix, paths["intermediate_dir"] / "05_event_type_monthly_matrix.csv")
    export_dataframe_table(translation_audit, paths["intermediate_dir"] / "translation_audit.csv")


def run_v2_pipeline(root: Path, render_outputs: bool = True) -> dict[str, Any]:
    """Run the full isolated v2 workflow."""
    config = load_v2_config(root)
    paths = resolve_paths(root, config)
    ensure_output_directories(paths)

    logger = get_project_logger("v2_disaster_pipeline", paths["logs_dir"])
    input_file = find_input_file(root, config)
    logger.info("Running v2 pipeline on %s", input_file)

    raw = read_source_csv(input_file, encoding=config["project"]["source_encoding"])
    cleaned = clean_records(raw, schema=config["schema_definition"], source_file=input_file)
    log_dataframe_shape(logger, "cleaned_registry", cleaned)

    translation_dictionary = load_translation_dictionary(str(paths["translation_dictionary"]))
    categorical_columns = config["schema_definition"]["groups"]["categorical_columns"]
    translated, translation_audit = translate_categorical_fields(cleaned, categorical_columns=categorical_columns, dictionary=translation_dictionary)
    log_dataframe_shape(logger, "translated_registry", translated)

    classified = build_semantic_event_model(
        translated,
        search_fields=config["analysis"]["earthquake_search_fields"],
        earthquake_terms=config["analysis"]["earthquake_terms"],
    )
    classified["_filter_date"] = pd.to_datetime(classified["occurrence_date"], errors="coerce")
    classified = classified[(classified["_filter_date"] >= "2021-08-01") & (classified["_filter_date"] <= "2025-12-31")].drop(columns=["_filter_date"]).copy()
    log_dataframe_shape(logger, "classified_registry", classified)

    monthly, event_type_matrix = aggregate_monthly_events(classified)
    log_dataframe_shape(logger, "monthly_panel", monthly)

    dataset_overview = build_dataset_overview(classified)
    event_type_summary = build_event_type_summary(classified)
    municipality_summary = build_municipality_summary(classified)
    translation_strategy_summary = build_translation_strategy_summary(translation_audit)

    volatility_panel_path = root / "data" / "processed" / "final_series" / "volatility_series.csv"
    if not volatility_panel_path.exists():
        logger.error("Required v1 input not found: %s", volatility_panel_path)
        raise FileNotFoundError(f"Missing v1 dataset: {volatility_panel_path}")
    volatility_df = pd.read_csv(volatility_panel_path, parse_dates=["date"])

    analysis = run_analysis(
        classified=classified,
        monthly=monthly,
        volatility_df=volatility_df,
        event_type_matrix=event_type_matrix,
        municipality_summary=municipality_summary,
        config=config["analysis"],
        figures_dir=paths["figures_dir"],
    )

    _export_intermediate_tables(
        paths=paths,
        cleaned=cleaned,
        translated=translated,
        classified=classified,
        monthly=monthly,
        event_type_matrix=event_type_matrix,
        translation_audit=translation_audit,
    )

    tables = {
        "dataset_overview": dataset_overview,
        "event_type_summary": event_type_summary,
        "municipality_summary": municipality_summary,
        "translation_strategy_summary": translation_strategy_summary,
        "earthquake_feasibility": analysis["feasibility_table"],
    }
    export_dataframe_table(dataset_overview, paths["tables_dir"] / "table_dataset_overview.csv")
    export_dataframe_table(event_type_summary, paths["tables_dir"] / "table_event_type_summary.csv")
    export_dataframe_table(municipality_summary, paths["tables_dir"] / "table_municipality_summary.csv")
    export_dataframe_table(translation_strategy_summary, paths["tables_dir"] / "table_translation_strategy_summary.csv")
    export_dataframe_table(analysis["feasibility_table"], paths["tables_dir"] / "table_earthquake_feasibility.csv")
    if "structural_comparison" in analysis["branch_tables"]:
        export_dataframe_table(analysis["branch_tables"]["structural_comparison"], paths["tables_dir"] / "table_structural_comparison.csv")
    if not analysis.get("pca_loadings", pd.DataFrame()).empty:
        export_dataframe_table(analysis["pca_loadings"], paths["tables_dir"] / "table_pca_loadings.csv")

    markdown_content = build_markdown_report(
        markdown_path=paths["manuscript_markdown"],
        config=config,
        input_file=input_file,
        analysis=analysis,
        tables=tables,
    )
    write_markdown_report(paths["manuscript_markdown"], markdown_content)

    rendered_outputs: dict[str, str] = {}
    if render_outputs:
        rendered_outputs = render_pandoc_outputs(
            markdown_path=paths["manuscript_markdown"],
            docx_path=paths["manuscript_docx"],
            pdf_path=paths["manuscript_pdf"],
        )
        logger.info("Rendered Pandoc outputs: %s", rendered_outputs)

    summary_payload = {
        "input_file": str(input_file),
        "branch": analysis["branch"],
        "branch_label": analysis["branch_label"],
        "branch_reason": analysis["branch_reason"],
        "earthquake_feasibility": analysis["feasibility"],
        "selected_features": analysis.get("selected_features", []),
        "explained_variance_ratio": analysis.get("explained_variance_ratio"),
        "shock_date": analysis.get("shock_date"),
        "change_dates": analysis.get("change_dates", []),
        "artifacts": {
            "markdown": str(paths["manuscript_markdown"]),
            **rendered_outputs,
        },
    }
    write_summary_json(paths["summary_json"], summary_payload)
    logger.info("Completed v2 pipeline using branch=%s", analysis["branch"])
    return summary_payload

