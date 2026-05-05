# Standalone Article Reproduction

This folder contains a one-command reproduction capsule for the cocoa-volatility manuscript located at:

```text
final_draft/main.tex
````

The runner regenerates the article figures and tables from the organized project datasets, writes fresh outputs under:

```text
standalone_reproduction/outputs/
```

and audits those outputs against the current manuscript-side figures and table text.

The purpose of this folder is to help an external evaluator verify whether the figures, statistical tables, and supplementary outputs reported in the final draft can be reproduced from the organized project inputs.

## Requirements

Python 3.10 or newer is recommended.

From this folder, install the required dependencies with:

```bash
pip install -r requirements.txt
```

The script does not download data and does not call external APIs.

## Expected Inputs

The script expects the repository to already contain the organized datasets produced by the project.

Core datasets:

```text
data/processed/analysis_ready/merged_cocoa_price_panel.csv
data/processed/final_series/core_common_window_panel_imputed.csv
data/processed/final_series/all_series_common_window_panel_imputed.csv
data/processed/final_series/all_series_common_window_volatility_imputed.csv
reports/v2/intermediate/03_classified_events.csv
reports/v2/intermediate/04_monthly_event_panel.csv
```

Validated article-level tables used for faithful reproduction of selected manuscript outputs:

```text
paper/tables/table_hazard_signal_screening.csv
paper/tables/table_hazard_overlay_model_comparison.csv
reports/v2/tables/table_disaster_causality.csv
```

These files are not treated as raw data downloads. They are retained project artifacts used to reproduce the final manuscript tables exactly when the article table is a validated publication-layer summary rather than a direct recomputation from the raw monthly panel.

Current manuscript figures are used only as comparison references after regeneration. The static map is copied when local geospatial base layers are unavailable.

## Run

From the repository root:

```bash
cd standalone_reproduction
python run_reproduction.py
```

The script is designed to run with one command from inside the `standalone_reproduction` folder.

## Outputs

The runner writes regenerated outputs to:

```text
outputs/figures/
outputs/tables/
outputs/audit/
```

Figures are saved as `.png`.

Tables are saved in two formats:

```text
outputs/tables/<table_name>.csv
outputs/tables/<table_name>.tex
```

The main audit file is:

```text
outputs/audit/reproduction_audit.md
```

Additional audit and provenance files are written under:

```text
outputs/audit/
outputs/audit/provenance/
```

Key audit files include:

```text
outputs/audit/table_comparison.csv
outputs/audit/table_crosswalk.md
outputs/audit/provenance/table_provenance_map.md
outputs/audit/provenance/figure_provenance_map.md
outputs/audit/provenance/discrepancy_diagnosis.md
outputs/audit/provenance/latex_vs_generated_values.md
outputs/audit/provenance/column_and_window_audit.md
```

## What The Runner Reproduces

The runner regenerates or reconstructs the following groups of outputs:

1. Main manuscript figures.
2. Supplementary figures.
3. Main statistical tables.
4. Supplementary diagnostic tables.
5. Provenance maps linking generated files to the manuscript tables and figures.
6. Audit files comparing generated outputs with the current final draft.

The static map is marked as a copied static artifact because the local geospatial base layers required for offline regeneration are not bundled in the repository.

## Table Reproduction Logic

Most tables are recomputed directly from the organized datasets.

Some publication-layer tables are reconstructed from validated project artifacts because those artifacts are the exact source used to build the final manuscript tables. This applies especially to selected hazard/disaster outputs, where the publication table is a curated summary of previous validated model outputs.

The following tables are treated as metadata or publication-layer summaries:

```text
tab_data_card
tab_sample_design
```

The following hazard/disaster tables are reconstructed from validated article artifacts:

```text
tab_hazard_screening
tab_hazard_models
tab_supp_disaster_granger
```

Specifically:

```text
tab_hazard_screening
```

uses:

```text
paper/tables/table_hazard_signal_screening.csv
```

and

```text
tab_hazard_models
```

should use:

```text
paper/tables/table_hazard_overlay_model_comparison.csv
```

This avoids discrepancies caused by recomputing hazard overlays from a slightly different monthly window or intermediate panel.

## Reading The Audit

The audit reports:

* which datasets were used;
* which figures and tables were generated;
* which outputs were copied as static;
* which tables were recomputed;
* which tables were reconstructed from validated article artifacts;
* whether generated outputs match, partially match, or differ from the current manuscript.

Small visual differences can occur because of Matplotlib rendering, fonts, image size, operating-system backends, or export settings. These differences are marked as minor when the figure is analytically regenerated and the content is present.

Major table differences should be inspected before manuscript submission. A `recomputed_major_difference` status can indicate one of three situations:

1. a real statistical mismatch;
2. a manuscript table that was manually reshaped or summarized;
3. a parser limitation when comparing LaTeX table text against generated `.csv` files.

The audit should therefore be interpreted together with the provenance files.

## Current Interpretation Of Audit Status

A successful run should generate all expected figures and tables.

The expected high-level status is:

```text
12 figures generated
13 tables generated
0 missing figures
0 missing tables
```

A fully acceptable audit may still show minor rendering differences for figures. These are not analytical discrepancies.

The following table statuses are acceptable:

```text
recomputed_match
recomputed_minor_difference
static_from_draft
copied_static
```

The following status requires inspection:

```text
recomputed_major_difference
```

At the current stage, the only major differences that should remain are those caused by hazard-table reconstruction or by structural differences between the generated table and the publication-layer LaTeX table. If `tab_hazard_models` remains as `recomputed_major_difference`, verify that `table_hazard_models()` reads:

```text
paper/tables/table_hazard_overlay_model_comparison.csv
```

rather than recomputing the model from `data.nested`.

## Expected Validated Results

The reproduction audit should confirm the following key results:

```text
Main Colombian-return benchmark coefficient: approximately 0.796
Main benchmark coefficient p-value: < 0.001
Weather-extended model table: 10 rows
World-volatility coefficient in the weather-extended volatility model: approximately 0.954
Hydrometeorological counts retained as preferred direct monthly hazard marker
Peak contextual-pressure month: 2022-10
```

For the hazard-screening table, the validated hydrometeorological row should report:

```text
Total events: 273
Nonzero months: 30
Zero-month share: approximately 0.143
Peak month: 2022-10
Peak value: 20
```

For the hazard-overlay model table, the validated hydrometeorological row should be based on:

```text
paper/tables/table_hazard_overlay_model_comparison.csv
```

and should report values close to:

```text
Return coefficient: -0.0146
Return p-value: 0.0834
Return N: 34
Volatility coefficient: -0.0031
Volatility p-value: 0.0738
Volatility N: 29
```

## Troubleshooting

If the script runs but the audit still reports major differences, inspect:

```text
outputs/audit/table_comparison.csv
outputs/audit/provenance/discrepancy_diagnosis.md
outputs/audit/provenance/table_provenance_map.md
```

If `tab_hazard_screening` differs, check that the function reads:

```text
paper/tables/table_hazard_signal_screening.csv
```

If `tab_hazard_models` differs, check that the function reads:

```text
paper/tables/table_hazard_overlay_model_comparison.csv
```

If `tab_weather_extended_models` differs, check that the script uses:

```text
data/processed/final_series/all_series_common_window_volatility_imputed.csv
```

If `tab_supp_disaster_granger` differs, check that the script reads:

```text
reports/v2/tables/table_disaster_causality.csv
```

If figure differences remain but are classified as minor, they are likely due to rendering settings rather than analytical inconsistencies.

## Traceability

The folder:

```text
input_code_archive/
```

contains original project scripts used to create the current results. These files are provided for traceability only.

The evaluator should run:

```bash
python run_reproduction.py
```

rather than executing the archived scripts individually.

## Submission Check

Before submitting the manuscript, run:

```bash
cd standalone_reproduction
python run_reproduction.py
```

Then inspect:

```text
outputs/audit/reproduction_audit.md
outputs/audit/table_comparison.csv
```

The manuscript is considered structurally reproducible when:

```text
all expected figures are generated or explicitly classified as static;
all expected tables are generated;
no missing table files are reported;
no unexplained major statistical differences remain;
hazard tables are aligned with their validated article artifacts;
the audit documents any remaining rendering or formatting differences.
```
