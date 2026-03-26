# Project Implementation Summary

## Title

**Cocoa volatility and supply chain vulnerability of smallholder cocoa farmers to global commodity price volatility: From Colombian farms to European markets**

## Objective

The repository now implements a transparent empirical workflow that links Colombian cocoa-related prices, international cocoa benchmarks, European downstream indicators, macro controls, and a climate context block in a way that supports reproducible descriptive analysis, cautious econometric extension, and manuscript-ready outputs.

## Implemented Scope

- Colombian domestic cocoa prices from the official AgroNet weekly cacao reference series, aggregated to monthly means.
- International cocoa benchmark prices from the World Bank Pink Sheet, plus Yahoo Finance futures history for higher-frequency market diagnostics.
- European downstream indicators from Eurostat HICP, including the main EU27 chocolate series and auxiliary chocolate-adjacent robustness indicators.
- Macro controls from official `COP/USD` and Brent oil series.
- Climate and agronomic extensions from NASA POWER, currently centered on San Vicente de Chucuri, Santander.
- Shared-window descriptive analysis, correlation diagnostics, and imputation sensitivity for the aligned monthly sample.
- Two chapter-style reduced-form modeling layers:
  - a core supply-chain transmission chapter
  - a separate weather-vulnerability chapter

## Repository Design

The repository follows a functional programming style:

- reusable small functions
- explicit inputs and outputs
- no classes
- no hidden state
- script entry points that orchestrate module functions
- YAML configuration for paths, variables, and source mappings

## Completed Outputs

- analysis-ready merged monthly dataset
- descriptive tables and figures for both full-history and aligned common-window samples
- stationarity test table
- ARIMA summaries
- co-integration and transmission results
- vulnerability indicators
- chapter-ready markdown summaries for the core transmission and weather-vulnerability stages
- bibliography and citation rationale notes
- NASA POWER raw climate downloads, harmonized tables, and download manifests
- AgroNet raw domestic cacao downloads, harmonized weekly/monthly tables, and download manifests
- World Bank, Yahoo Finance, Eurostat, BanRep, and EIA raw downloads plus cleaned and harmonized tables
- CSV and JSON export parity for tabular datasets
- imputation audit tables and imputed aligned panels

## Completed Data-Collection and Presentation Activities

- Downloaded the official World Bank monthly cocoa benchmark from the Pink Sheet workbook and converted it to a monthly USD-per-metric-ton series.
- Downloaded Yahoo Finance `CC=F` cocoa futures history at both daily and monthly frequencies for market-volatility analysis.
- Split the international cocoa block into an official benchmark path and a practical futures-market path so monthly merged analysis can stay source-consistent while higher-frequency work remains available.
- Downloaded the official AgroNet weekly cacao reference series for Colombia and converted it into both weekly and monthly domestic price tables.
- Downloaded the official Eurostat EU27 chocolate HICP monthly index and cleaned it into the EU downstream block used by the merged panel.
- Added auxiliary Eurostat downstream indicators for cocoa and powdered chocolate, confectionery, a broader sweets aggregate, and a longer France chocolate series for robustness analysis.
- Documented that the currently implemented Eurostat `prc_hicp_midx` chocolate series runs through `2025-12`, while Eurostat's published January 2026 classification change moves the continuation path into the ECOICOP 2 folder.
- Downloaded the official BanRep TRM series for `COP/USD` and the official EIA Brent oil history series, then aligned them as macro controls for the merged panel.
- Verified the NASA POWER temporal API request structure and response format for both daily and monthly point-series endpoints.
- Geocoded San Vicente de Chucuri, Santander as the first climate acquisition point and stored its documented centroid in project configuration.
- Downloaded daily and monthly NASA POWER time series for precipitation, temperature, humidity, wind speed, and irradiance.
- Merged the climate block into the main monthly panel and exported climate-only processed panels for descriptive analysis.
- Standardized the tabular export layer so project datasets are written as both CSV and JSON.
- Constrained the descriptive stage to the shared monthly window `2021-08-01` to `2025-12-01`, producing:
  - a `53`-month shared core calendar window
  - a `52`-observation balanced common sample across the five core series
  - a `51`-observation common sample when the complete climate block is required
- Added a transparent imputation workflow for the one missing core observation in `2025-09`, exporting both KNN and iterative multivariate estimates.
- Added a dedicated imputed statistical-properties stage that reports descriptive statistics, level and return stationarity tests, volatility diagnostics, ARCH-LM tests, and STL decomposition outputs for each core series.
- Added a parallel all-series statistical-properties stage that imputes the weather block within its own shared window, exports weather-only statistical tables, writes STL decomposition figures for every core and weather series, and produces a one-row-per-series overview across the full supply-chain and weather system.
- Standardized figures with the Okabe-Ito palette, fixed `-1` to `1` correlation heatmap scales, near-zero black annotation text, and full-width acronym keys for dense heatmaps.
- Estimated a core transmission chapter on the aligned cocoa supply-chain system with HAC-robust level and return regressions, Engle-Granger tests, directional Granger causality, and a compact return VAR.
- Estimated a separate weather-vulnerability chapter that extends the domestic-price equations with selected weather variables, compares weather-extended and core fit, and exports exploratory farmer-exposure and livelihood-risk indicators.

## Current Modeling Status

1. The aligned descriptive and statistical-properties stages are complete for both the core and weather blocks.
2. The core transmission stage is now implemented as a parsimonious monthly reduced-form chapter rather than a large multivariate system.
3. The weather block is currently implemented as a separate vulnerability chapter, not as a forced regressor set in every transmission model.
4. The next major extension should focus on robustness and identification, especially if a longer Colombian domestic series can be recovered.
5. Auxiliary EU indicators and futures data remain available for robustness checks without changing the main benchmark system.

## Output Standards

Each collected dataset now records or is expected to record:

- source institution
- raw filename
- download date
- transformed filename
- units
- frequency
- missing-data handling
- transformation steps
- manuscript citation
- CSV and JSON export paths when the artifact is tabular

Each model output now records or is expected to record:

- sample period
- variables used
- lag rule
- diagnostic tests
- interpretation limits
- whether the sample is full-history, shared-window, balanced, or imputed
- whether the result belongs to the core transmission chapter or the weather-vulnerability chapter
