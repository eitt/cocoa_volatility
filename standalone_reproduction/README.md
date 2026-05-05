# Standalone Article Reproduction

This folder contains a one-command reproduction capsule for the cocoa-volatility manuscript in `final_draft/main.tex`.

The runner regenerates the article figures and tables from the organized project datasets, writes fresh outputs under `standalone_reproduction/outputs/`, and audits those outputs against the current manuscript-side figures and table text.

## Requirements

Python 3.10 or newer is recommended.

Install the standalone dependencies from this folder:

```bash
pip install -r requirements.txt
```

## Expected Inputs

The script does not download data and does not call external APIs. It expects the repository to contain the organized datasets already produced by the project:

- `data/processed/analysis_ready/merged_cocoa_price_panel.csv`
- `data/processed/final_series/core_common_window_panel_imputed.csv`
- `data/processed/final_series/all_series_common_window_panel_imputed.csv`
- `reports/v2/intermediate/03_classified_events.csv`
- `reports/v2/intermediate/04_monthly_event_panel.csv`

Current manuscript figures are used only as comparison references after regeneration. The static map is copied when local geospatial base layers are unavailable.

## Run

From the repository root:

```bash
cd standalone_reproduction
python run_reproduction.py
```

## Outputs

The runner writes:

- regenerated figures to `outputs/figures/`
- regenerated tables to `outputs/tables/` as both `.csv` and `.tex`
- audit files to `outputs/audit/`

The main audit is:

- `outputs/audit/reproduction_audit.md`

Machine-readable comparison files are also written in `outputs/audit/`.

## Reading The Audit

The audit reports which datasets were used, which figures and tables were regenerated, whether any item was copied as static, and how regenerated outputs compare with the current draft references.

Small visual differences can occur from Matplotlib rendering, fonts, or operating-system image backends. These are marked as minor differences when the analytical output exists and the file dimensions or simple image-difference metrics remain close. Major differences or missing items should be inspected before manuscript submission.

`input_code_archive/` contains original project scripts used to create the current results. These files are for traceability only; the evaluator should run `run_reproduction.py`.
