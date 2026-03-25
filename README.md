# Cocoa Volatility and Supply Chain Vulnerability

This repository contains a reproducible research workflow for studying how global cocoa price volatility moves from Colombian farm-linked markets into European downstream markets, and how that transmission can be interpreted in terms of smallholder vulnerability.

## Research Question

How does volatility in international cocoa commodity prices transmit through Colombian domestic cocoa markets and European cocoa or chocolate price indicators, and what does that imply for the exposure of smallholder cocoa farmers to global market shocks?

## Main Contributions

- Colombian domestic price evidence built from official and quasi-official agricultural market sources.
- Integration of international cocoa benchmark prices with Colombian market data.
- European downstream market coverage using consumer or producer price indicators.
- Time-series econometric analysis of volatility, stationarity, co-integration, transmission, and dynamics.
- Vulnerability-oriented interpretation that links market exposure to smallholder livelihood risks.

## Reproducibility

Install dependencies with either `pip` or Conda:

```bash
pip install -r requirements.txt
```

```bash
conda env create -f environment.yml
conda activate cocoa-volatility
```

Run the pipeline scripts in sequence from the repository root:

```bash
python scripts/01_build_raw_registry.py
python scripts/02_clean_domestic_prices.py
python scripts/03_clean_international_prices.py
python scripts/04_clean_eu_prices.py
python scripts/05_build_merged_dataset.py
python scripts/06_descriptive_analysis.py
python scripts/07_stationarity_and_cointegration.py
python scripts/08_arima_and_volatility.py
python scripts/09_transmission_models.py
python scripts/10_vulnerability_metrics.py
python scripts/11_export_results.py
```

Most scripts are designed to fail gracefully when raw inputs are not yet available, so the scaffold can be extended incrementally.

## Folder Map

- `config/`: YAML configuration for paths, variables, sources, and model defaults.
- `data/raw/`: untouched original downloads grouped by source family.
- `data/interim/`: cleaned and harmonized intermediate outputs.
- `data/processed/`: analysis-ready series and model inputs.
- `docs/`: project specification, dataset search protocol, methodology notes, manuscript planning, and citation rationale.
- `src/`: reusable functional Python modules.
- `scripts/`: sequential entry points that orchestrate the pipeline.
- `outputs/`: tables, figures, logs, appendix items, and other deliverables.
- `references/`: BibTeX bibliography used by the manuscript and notes.
- `tests/`: lightweight validation tests for core transformations and merges.

## Data Sources

The repository is structured to work with the following target sources:

- SIPSA / DANE wholesale agricultural price data for Colombia.
- ICCO benchmark cocoa market statistics.
- World Bank Commodities Price Data (Pink Sheet).
- Eurostat HICP and related price indicators.
- UN Comtrade trade flows for cocoa and chocolate HS codes.
- Colombian exchange rate and inflation series.
- NASA POWER climate data for robustness extensions.

## Empirical Workflow

1. Collect raw data and register source metadata.
2. Clean domestic, international, EU, trade, and climate inputs.
3. Harmonize units, currencies, dates, and frequencies.
4. Merge all selected series into a common monthly analysis panel.
5. Test stationarity with ADF, KPSS, and optional Phillips-Perron.
6. Estimate ARIMA and volatility measures for key price series.
7. Test co-integration, pass-through, and dynamic transmission.
8. Construct vulnerability indicators for smallholder exposure.
9. Export manuscript-ready tables, figures, and supporting files.

## Outputs

Final artifacts are written to `outputs/` and `data/processed/`, including:

- final merged datasets
- descriptive statistics tables
- stationarity and co-integration tables
- ARIMA and transmission summaries
- volatility and trend figures
- vulnerability indicator tables
- bibliography assets for manuscript integration

## Citation Assets

The bibliography file lives at `references/cocoa_volatility.bib`, and a plain-language explanation of why each citation is included lives at `docs/citation_justification.md`.
