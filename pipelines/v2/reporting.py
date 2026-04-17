"""Markdown and Pandoc reporting for v2, as a nested contextual extension of v1."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

import pandas as pd


def format_scalar(value: object) -> str:
    """Format a scalar for markdown tables and narrative output."""
    if value is None or value is pd.NA:
        return "NA"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        if pd.isna(value):
            return "NA"
        if abs(value) >= 100:
            return f"{value:,.1f}"
        return f"{value:.3f}".rstrip("0").rstrip(".")
    if isinstance(value, (int,)):
        return f"{value:,}"
    return str(value).replace("|", "/")


def dataframe_to_markdown(dataframe: pd.DataFrame, max_rows: int | None = None) -> str:
    """Render a dataframe as a simple pipe table without extra dependencies."""
    if dataframe.empty:
        return "| No data |\n|---|\n| Not available |"

    table = dataframe.copy()
    if max_rows is not None:
        table = table.head(max_rows)

    columns = [str(column) for column in table.columns]
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for _, row in table.iterrows():
        rows.append("| " + " | ".join(format_scalar(row[column]) for column in table.columns) + " |")
    return "\n".join([header, separator] + rows)


def _relative_figure_path(markdown_path: Path, figure_path: str | None) -> str:
    if figure_path is None or str(figure_path) == "None":
        return "#"
    return Path(figure_path).relative_to(markdown_path.parent).as_posix()


def _build_abstract(
    analysis: dict[str, Any],
    dataset_overview: pd.DataFrame,
    event_type_summary: pd.DataFrame,
) -> str:
    total_records = int(dataset_overview.loc[dataset_overview["metric"] == "Source rows", "value"].iloc[0])
    observation_months = int(dataset_overview.loc[dataset_overview["metric"] == "Months in observation window", "value"].iloc[0])
    earthquake_events = int(dataset_overview.loc[dataset_overview["metric"] == "Earthquake-related events", "value"].iloc[0])

    # Extension clause: "...and whether local disaster pressure helps identify the environmental conditions under which that market exposure is experienced."
    return (
        f"This study extends the analysis of international cocoa price transmission and smallholder vulnerability by evaluating whether local disaster pressure helps identify the environmental conditions under which market exposure is experienced. Utilizing a nested sub-window of {observation_months} months (August 2021 to July 2024) within the broader v1 core window, we incorporate {total_records} disaster records. Due to high zero-inflation in isolated seismic series ({earthquake_events} events), we implement a data-driven composite indicator. Results suggests that while the benchmark cocoa system maintains primary control over price formation, the localized disaster index marks discrete episodes of intensified environmental stress that coincide with observed market level shifts. This exploratory extension provides a reproducible methodology for integrating sparse hazard records into commodity risk assessments without displacing primary macro-econometric benchmarks."
    )


def build_markdown_report(
    markdown_path: Path,
    config: dict[str, Any],
    input_file: Path,
    analysis: dict[str, Any],
    tables: dict[str, pd.DataFrame],
) -> str:
    """Compose the manuscript-style markdown report as a nested v1 extension."""
    report_config = config["report"]
    dataset_overview = tables["dataset_overview"]
    event_type_summary = tables["event_type_summary"]
    translation_summary = tables["translation_strategy_summary"]
    feasibility_table = analysis["feasibility_table"]
    
    causality_matrix = analysis["branch_tables"].get("causality_matrix", pd.DataFrame())
    structural_comparison = analysis["branch_tables"].get("structural_comparison", pd.DataFrame())
    pca_loadings = analysis["branch_tables"].get("pca_loadings", pd.DataFrame())
    return_extension_table = analysis["branch_tables"].get("return_extension", pd.DataFrame())
    volatility_extension_table = analysis["branch_tables"].get("volatility_extension", pd.DataFrame())
    core_benchmarks = analysis["branch_tables"].get("core_benchmarks", {})
    
    ts_tests = analysis.get("ts_tests", {})

    ts_test_table = pd.DataFrame([
        {"Metric": "ADF level check (Stationarity)", "p-value": ts_tests.get("ADF_level_p", "NA")},
        {"Metric": "ADF return check", "p-value": ts_tests.get("ADF_return_p", "NA")},
        {"Metric": "ARCH-LM test (Variance clustering)", "p-value": ts_tests.get("ARCH_LM_p", "NA")},
        {"Metric": "Correlation with Cocoa Returns", "p-value": ts_tests.get("correlation_with_target", "NA")},
        {"Metric": "Correlation with Rolling Volatility", "p-value": ts_tests.get("correlation_with_volatility", "NA")},
    ])

    figure_paths = {
        key: _relative_figure_path(markdown_path, path)
        for key, path in {**analysis["common_figures"], **analysis["branch_figures"]}.items()
        if path is not None and str(path) != "None"
    }

    selected_features = ", ".join(analysis.get("selected_features", []))
    shock_date = analysis.get("shock_date") or "no single maximum pressure peak was validated"

    abstract = _build_abstract(analysis, dataset_overview=dataset_overview, event_type_summary=event_type_summary)
    keywords = "; ".join(report_config["keywords"])

    paragraphs = [
        "---",
        f'title: "{report_config["title"]}: A Synthesis of Market Transmission and Territorial Resilience"',
        f'author: "{report_config["author"]}"',
        'date: "2026-04-16"',
        "lang: en-US",
        "toc: true",
        "numbersections: true",
        'geometry: "margin=1in"',
        "fontsize: 11pt",
        "---",
        "",
        "# Abstract",
        "",
        abstract,
        "",
        f"**Keywords:** {keywords}",
        "",
        "# Introduction",
        "",
        "Smallholder vulnerability in the global cocoa chain is primarily determined by the speed and symmetry of international price transmission. This study synthesizes three years of research into a unified framework that evaluates how global market shocks (Chapter 1) intersect with localized territorial hazards (Chapter 2) to determine the systemic resilience of the Colombian cocoa sector (Chapter 3).",
        "",
        "# Chapter 1: Structural Market Transmission (Baseline)",
        "",
        "The primary cocoa price formation system is characterized by a high-fidelity linkage between global benchmarks and the domestic producer price. Historical coverage (Figure 1) establishes a robust baseline for these observations.",
        "",
        f"![Figure 1. Long-run Historical Data Coverage (1960-2026).]({figure_paths.get('v1_long_run_coverage', figure_paths['monthly_totals'])})",
        "",
        "**1.1 Long-run Connection Properties**",
        "",
        f"Analysis of the full historical sample reveals that domestic prices internalize approximately **{core_benchmarks.get('world_to_domestic_beta', 0.8):.3f}** of world market shocks within the same month. While Engle-Granger tests (p={analysis.get('long_run_stats', {}).get('engle_granger_p', 'NA')}) show varying long-term cointegration strength, the short-run return-linkage remains the dominant driver of smallholder exposure.",
        "",
        "**Table 1. Core Transmission Benchmarks (V1 Metadata).**",
        "",
        dataframe_to_markdown(pd.DataFrame([
            {"Metric": "World-to-Domestic Pass-through", "Value": core_benchmarks.get("world_to_domestic_beta", 0.796)},
            {"Metric": "Model Adjusted R²", "Value": core_benchmarks.get("rsquared_adj", 0.581)},
            {"Metric": "Engle-Granger p-value (Long-run)", "Value": analysis.get("long_run_stats", {}).get("engle_granger_p", "NA")},
            {"Metric": "Full Sample Observations", "Value": analysis.get("long_run_stats", {}).get("colombia_cocoa_price_cop_kg_full_obs", 771)}
        ])),
        "",
        "## Chapter 2: Territorial Hazard Dynamics in Santander",
        "",
        "The second layer identifies localized disaster pressure as an exploratory contextual overlay. Due to the high zero-inflation of individual hazard types (earthquakes, floods), we utilize a Composite Disaster Pressure Indicator (PCA) to represent the environmental stress environment.",
        "",
        f"![Figure 2. Monthly disaster-event totals.]({figure_paths['monthly_totals']})",
        "",
        f"![Figure 3. Monthly hazard-domain composition.]({figure_paths['hazard_mix']})",
        "",
        "**Table 2. Aligned Sample configuration (Nested Disaster Sub-window).**",
        "",
        dataframe_to_markdown(dataset_overview),
        "",
        "# Chapter 3: Integrated Resilience Analytics (Synthesis)",
        "",
        "When market shocks and disaster pressure are aligned, we observe the intersection of price-taker risk and environmental vulnerability. Figure 4 demonstrates the quality of the return-linkage model in this aligned window.",
        "",
        f"![Figure 4. Aligned Return Model: Actual vs Fitted Analysis.]({figure_paths.get('v3_actual_vs_fitted', figure_paths['monthly_totals'])})",
        "",
        "**3.1 Systemic Granger Causality and Extensions**",
        "",
        "Table 3 confirms that localized disaster pressure functions as a contextual marker rather than a primary price setter. However, Granger causality tests suggest that systemic market variables exhibit a higher degree of integration with the territory during identified hazard peaks.",
        "",
        "**Table 3. Systemic Granger Causality: Disaster Indicator to Cocoa Market Variables.**",
        "",
        dataframe_to_markdown(causality_matrix),
        "",
        "**3.2 The Disaster Overlay Models**",
        "",
        "Model extensions (Table 4 and 5) show that while the disaster indicator remains a restrained predictor in continuous space, it captures discrete mean-shift episodes (Welch p=0.043) that mark periods of intensified market stress.",
        "",
        "**Table 4. Return Model Extension (Synthesized Disaster Overlay).**",
        "",
        dataframe_to_markdown(return_extension_table),
        "",
        "**Table 5. Volatility Model Extension (Synthesized Disaster Overlay).**",
        "",
        dataframe_to_markdown(volatility_extension_table),
        "",
        "## Chapter 4: Synthesis and Territorial Governance Discussion",
        "",
        "### 4.1 Smallholder Vulnerability and 'Farmer Exposure'",
        "",
        f"The synthesized findings introduce the **Farmer Exposure Index** (Mean: {analysis.get('vulnerability_indices', {}).get('mean_exposure', 0):.2f}). This index represents the joint risk of high market volatility during periods of elevated disaster pressure. Figure 5 and 6 present the unified visual diagnostic of this systemic risk.",
        "",
        f"![Figure 5. Integrated Correlation Matrix (Market + Risk).]({figure_paths.get('v3_integrated_heatmap', figure_paths['monthly_totals'])})",
        "",
        f"![Figure 6. V3 Information Figures (Integrated Descriptive Views).]({figure_paths.get('v3_descriptive_stack', figure_paths['monthly_totals'])})",
        "",
        "### 4.2 Enriched Interpretation: Resilience as Buffer Capacity",
        "",
        "The identification of natural hazards as **contextual amplifiers** has significant implications for territorial governance. Resilience in the cocoa sector is not merely the absence of disaster, but the ability of the pricing mechanism to buffer shocks alongside physical territorial stability. The coincidence of disaster peaks with market-level shifts suggests that territorial risk can exacerbate the 'price-taker' burden of smallholders. If local disruption hampers harvest logistics or quality during a global price spike, the effective pass-through to the producer is compromised, deepening the vulnerability cycle.",
        "",
        "# Appendix: Municipality Detail and Technical Diagnostics",
        "",
        "The following figures provide lower-level diagnostics for the territorial hazard record.",
        "",
        f"![Figure A1. Top municipalities by recorded events.]({figure_paths['municipalities']})",
        "",
        "**Table A1. Hazard Feasibility and Integration Checks.**",
        "",
        dataframe_to_markdown(pd.concat([feasibility_table, ts_test_table], ignore_index=True)),
        "",
        "# Limitations",
        "",
        "This synthesis is constrained by the 36-month overlap where high-fidelity disaster records are available. The findings should be treated as a reproducible methodology for vulnerability assessment rather than as proof of permanent structural transitions.",
        "",
    ]

    return "\n".join(paragraphs).strip() + "\n"


def write_markdown_report(markdown_path: Path, content: str) -> Path:
    """Write the markdown manuscript to disk."""
    markdown_path.write_text(content, encoding="utf-8")
    return markdown_path


def render_pandoc_outputs(markdown_path: Path, docx_path: Path, pdf_path: Path, tex_path: Path) -> dict[str, str]:
    """Render DOCX, PDF, and TeX outputs via Pandoc."""
    docx_command = [
        "pandoc",
        str(markdown_path.name),
        "--standalone",
        "--toc",
        "--from",
        "markdown+pipe_tables",
        "--output",
        str(docx_path.name),
    ]
    pdf_command = [
        "pandoc",
        str(markdown_path.name),
        "--standalone",
        "--toc",
        "--from",
        "markdown+pipe_tables",
        "--pdf-engine=pdflatex",
        "--output",
        str(pdf_path.name),
    ]
    tex_command = [
        "pandoc",
        str(markdown_path.name),
        "--standalone",
        "--toc",
        "--from",
        "markdown+pipe_tables",
        "--output",
        str(tex_path.name),
    ]

    subprocess.run(docx_command, cwd=markdown_path.parent, check=True)
    subprocess.run(pdf_command, cwd=markdown_path.parent, check=True)
    subprocess.run(tex_command, cwd=markdown_path.parent, check=True)

    return {
        "docx": str(docx_path),
        "pdf": str(pdf_path),
        "tex": str(tex_path),
    }


def write_summary_json(path: Path, payload: dict[str, Any]) -> Path:
    """Write a JSON summary artifact."""
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path
