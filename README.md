# Cocoa Volatility and Supply Chain Vulnerability

This repository contains a reproducible research workflow for studying how global cocoa price volatility moves from Colombian farm-linked markets into European downstream markets, and how that transmission can be interpreted in terms of smallholder vulnerability. The current implementation now includes completed acquisition, cleaning, and descriptive integration for Colombian domestic prices, international cocoa benchmarks, EU downstream indicators, macro controls, and a NASA POWER climate block for San Vicente de Chucuri, Santander.

## Research Question

How does volatility in international cocoa commodity prices transmit through Colombian domestic cocoa markets and European cocoa or chocolate price indicators, and what does that imply for the exposure of smallholder cocoa farmers to global market shocks?

## Main Contributions

- Colombian domestic price evidence built from an official AgroNet cacao reference series.
- Integration of international cocoa benchmark prices with Colombian market data.
- European downstream market coverage using official Eurostat chocolate and cocoa-related indicators.
- Macro control integration using official `COP/USD` and Brent oil series.
- Climate-context integration using NASA POWER monthly weather variables.
- Time-series econometric workflow for descriptive analysis, stationarity, volatility, and transmission.

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
python scripts/00_download_nasa_power_climate.py
python scripts/00_download_international_cocoa_prices.py
python scripts/00_download_colombia_cocoa_prices.py
python scripts/00_download_eu_prices.py
python scripts/00_download_macro_controls.py
python scripts/01_build_raw_registry.py
python scripts/02_clean_domestic_prices.py
python scripts/03_clean_international_prices.py
python scripts/04_clean_eu_prices.py
python scripts/04_clean_macro_controls.py
python scripts/05_build_merged_dataset.py
python scripts/05a_impute_missing_values.py
python scripts/06_descriptive_analysis.py
python scripts/06b_statistical_properties_imputed.py
python scripts/06c_statistical_properties_all_series_imputed.py
python scripts/07_stationarity_and_cointegration.py
python scripts/08_arima_and_volatility.py
python scripts/09_transmission_models.py
python scripts/10_vulnerability_metrics.py
python scripts/11_export_results.py
```

Most scripts are designed to fail gracefully when raw inputs are not yet available, so the scaffold can be extended incrementally.

## Current Implementation Status

- Completed raw, harmonized, cleaned, and metadata-tracked acquisition for AgroNet, World Bank, Yahoo Finance, Eurostat, BanRep, EIA, and NASA POWER source blocks.
- Standardized the tabular export layer so CSV datasets also write matching JSON files.
- Built a merged monthly panel with `795` rows from `1960-01-01` to `2026-03-01`.
- Integrated the climate block directly into the merged panel with precipitation, mean/max/min temperature, humidity, wind speed, and solar radiation.
- Constrained comparative descriptive work to the shared monthly core window `2021-08-01` to `2025-12-01`.
- Confirmed:
  - `53` rows in the shared core calendar window
  - `52` complete monthly observations across the five core series
  - `51` complete monthly observations when the full climate block is required
- Added a transparent imputation step for the one missing core observation in `2025-09`, exporting both KNN and iterative multivariate estimates.
- Expanded descriptive outputs to include same-length core and climate panels, indexed series, availability figures, level and log-return corrplots, and imputation-audit tables.
- Added an imputed statistical-properties reporting step with:
  - extended descriptive statistics
  - level and log-return stationarity tests
  - volatility summaries and ARCH-LM diagnostics
  - one STL decomposition plot per core series
- Added a parallel weather-and-all-series statistical-properties reporting step with:
  - block-specific weather imputation in the shared window
  - one STL decomposition plot per weather series
  - weather-specific stationarity and volatility tables
  - one aggregated overview table covering all core and weather series
- Added a dedicated core transmission chapter with:
  - balanced and imputed aligned-sample pass-through models
  - pairwise Engle-Granger tests
  - directional Granger causality tables
  - a core return VAR and impulse-response figure
- Added a separate weather-vulnerability chapter with:
  - weather-extended domestic level and return models
  - weather-versus-core fit comparisons
  - domestic-volatility sensitivity to world volatility and weather stress
  - exploratory farmer-exposure and livelihood-risk indicators
- Standardized figure presentation with the Okabe-Ito colorblind-safe palette, fixed `-1` to `1` correlation heatmap scales, black annotation text for values between `-0.2` and `0.2`, and full-width acronym keys for dense heatmaps.

## Folder Map

- `config/`: YAML configuration for paths, variables, sources, and project defaults.
- `data/raw/`: untouched original downloads grouped by source family.
- `data/interim/`: cleaned and harmonized intermediate outputs.
- `data/processed/`: analysis-ready series and model inputs.
- `docs/`: project specification, progress logs, methodology notes, manuscript planning, and citation rationale.
- `src/`: reusable functional Python modules.
- `scripts/`: sequential entry points that orchestrate the pipeline.
- `outputs/`: tables, figures, logs, appendix items, and other deliverables.
- `references/`: BibTeX bibliography used by the manuscript and notes.
- `tests/`: lightweight validation tests for core transformations and merges.

## Data Sources

The repository is structured around the following implemented or planned source blocks:

- AgroNet weekly cacao reference prices for Colombia.
- SIPSA / DANE wholesale agricultural price data for supplementary Colombian market context.
- World Bank Commodities Price Data (Pink Sheet) for the core monthly international cocoa benchmark.
- Yahoo Finance ICE cocoa futures history for daily and monthly market observations.
- Eurostat HICP and related price indicators for the EU downstream block.
- BanRep TRM and EIA Brent series for macro controls.
- UN Comtrade trade flows for cocoa and chocolate HS codes.
- NASA POWER climate data for contextual and robustness extensions.

The first completed climate acquisition is centered on San Vicente de Chucuri, Santander and uses the NASA POWER point API with the `AG` community configuration.
The first completed international market acquisition combines the World Bank monthly cocoa benchmark with Yahoo Finance `CC=F` cocoa futures history.
The first completed domestic market acquisition uses the official AgroNet weekly cacao reference table and monthly means derived from that weekly series.
The first completed EU downstream acquisition uses Eurostat's official HICP monthly chocolate index for `EU27_2020`, with coverage currently running through `2025-12` in the legacy COICOP API series before the documented January 2026 ECOICOP 2 transition.
The first completed macro-control acquisition uses BanRep's official `COP/USD` series and EIA Brent history.

## Empirical Workflow

1. Collect raw data and register source metadata.
2. Clean domestic, international, EU, macro, and climate inputs.
3. Harmonize units, currencies, dates, and frequencies.
4. Merge all selected series into a common monthly analysis panel.
5. Build shared-window and balanced-sample descriptive panels.
6. Export non-imputed and imputed aligned variants when missing values interrupt the common window.
7. Test stationarity with ADF, KPSS, and optional Phillips-Perron.
8. Estimate ARIMA and volatility measures for key price series.
9. Estimate the baseline core transmission chapter on the aligned monthly core system.
10. Estimate the separate weather-vulnerability chapter on the imputed all-series aligned panel.
11. Export manuscript-ready tables, figures, and supporting files.

## Outputs

Final artifacts are written to `outputs/` and `data/processed/`, including:

- raw download manifests and source registries
- harmonized and cleaned CSV/JSON datasets
- final merged datasets and aligned final-series panels
- descriptive statistics, coverage, overlap, correlation, imputation, stationarity, volatility, and decomposition tables
- core, macro, climate, indexed, availability, and rolling-volatility figures
- stationarity, ARIMA, transmission, and weather-vulnerability chapter outputs
- bibliography assets for manuscript integration

## Citation Assets

The bibliography file lives at `references/cocoa_volatility.bib`, and a plain-language explanation of why each citation is included lives at `docs/citation_justification.md`. Operational source provenance is also documented in `config/source_registry.yaml`, `data/raw/metadata/`, and `docs/data_collection_progress.md`.
