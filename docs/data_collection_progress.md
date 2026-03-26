# Data Collection and Integration Progress

## Completed on 2026-03-26

- [x] Rebuilt the merged monthly panel so the NASA POWER climate block is included directly in the analysis-ready dataset.
- [x] Standardized the tabular export workflow so project datasets are written as both CSV and JSON.
- [x] Generated same-length descriptive outputs for the shared monthly core window `2021-08-01` to `2025-12-01`.
- [x] Confirmed the shared core window contains `53` calendar months and `52` complete monthly observations across the five core series.
- [x] Confirmed the climate-augmented common sample falls to `51` monthly observations because the core block is missing `2025-09-01` for Colombia and the climate block is missing `2025-12-01` for solar radiation.
- [x] Added a transparent imputation workflow for the single missing core value in `2025-09-01`.
- [x] Exported both KNN and iterative multivariate candidate estimates in `outputs/tables/table_imputation_audit.csv`.
- [x] Set the primary imputed aligned core panel to the iterative multivariate estimate and saved the alternative KNN panel as a sensitivity artifact.
- [x] Added climate-only processed panels, climate summary tables, and climate correlation outputs.
- [x] Standardized figure presentation with the Okabe-Ito palette, fixed `-1` to `1` heatmap scales, near-zero black heatmap labels, and full-width acronym keys for dense correlation plots.
- [x] Exported core statistical-properties outputs from the imputed aligned supply-chain panel.
- [x] Imputed the weather block within the shared window and exported weather-specific statistical-properties outputs.
- [x] Exported a one-row-per-series overview table covering all supply-chain and weather series together.
- [x] Generated STL decomposition figures for every core and weather time series.
- [x] Estimated the core supply-chain transmission chapter with balanced and imputed aligned-sample regressions, Engle-Granger tests, Granger causality, and a compact return VAR.
- [x] Estimated the separate weather-vulnerability chapter with selected weather covariates, domestic-volatility sensitivity tests, and exploratory farmer-exposure and livelihood-risk indicators.

## Integration Output Summary

- Merged monthly panel: `795` rows from `1960-01-01` to `2026-03-01`.
- Shared core calendar window: `53` rows from `2021-08-01` to `2025-12-01`.
- Balanced common sample across the five core series: `52` rows.
- Climate-augmented common sample: `51` rows.
- Climate monthly coverage:
  - `312` observations for precipitation, temperature, humidity, and wind variables
  - `311` observations for surface solar radiation

## Integration Files Created or Refreshed

- `data/processed/analysis_ready/merged_cocoa_price_panel.csv`
- `data/processed/analysis_ready/merged_cocoa_price_panel.json`
- `data/processed/final_series/core_common_window_panel.csv`
- `data/processed/final_series/core_common_sample_panel.csv`
- `data/processed/final_series/core_common_window_panel_imputed.csv`
- `data/processed/final_series/core_common_window_panel_imputed_knn.csv`
- `data/processed/final_series/core_common_window_panel_imputed_iterative.csv`
- `data/processed/final_series/climate_monthly_panel.csv`
- `data/processed/final_series/climate_common_window_panel.csv`
- `outputs/tables/table_common_sample_windows.csv`
- `outputs/tables/table_imputation_audit.csv`
- `outputs/tables/table_climate_summary_statistics.csv`
- `outputs/tables/table_climate_core_correlation_common_sample.csv`
- `outputs/tables/table_statistical_properties_all_series_overview.csv`
- `outputs/tables/table_statistical_properties_weather_overview.csv`
- `outputs/tables/table_stationarity_tests_imputed_weather_levels.csv`
- `outputs/tables/table_volatility_summary_imputed_weather_log_returns.csv`
- `outputs/tables/table_core_transmission_coefficients.csv`
- `outputs/tables/table_core_granger_causality_summary.csv`
- `outputs/tables/table_weather_vulnerability_coefficients.csv`
- `outputs/tables/table_weather_vs_core_model_comparison.csv`
- `outputs/tables/table_vulnerability_metrics.csv`
- `outputs/figures/figure_core_series_panels_common_window.png`
- `outputs/figures/figure_indexed_core_series_common_window_imputed.png`
- `outputs/figures/figure_climate_series_panels.png`
- `outputs/figures/figure_climate_core_correlation_common_sample.png`
- `outputs/figures/figure_core_return_impulse_response.png`
- `outputs/figures/figure_weather_vulnerability_index.png`
- `outputs/figures/figure_stl_decomposition_nasa_precipitation_mm_day_imputed.png`
- `outputs/figures/figure_stl_decomposition_nasa_surface_solar_radiation_mj_m2_day_imputed.png`

## Completed on 2026-03-25: Climate Block

- [x] Confirmed the climate-extension paper already cited in the repository: *Optimizing Cocoa Biomass Density through Integrated Irrigation and Drainage Management under Water Stress: A Linear Programming Approach* (Ecological Informatics, 2025, DOI: `10.1016/j.ecoinf.2025.103262`).
- [x] Verified the NASA POWER temporal API structure for monthly and daily point-series downloads.
- [x] Configured San Vicente de Chucuri, Santander, Colombia as the first climate download target.
- [x] Documented the working centroid used for the API requests: latitude `6.9287793`, longitude `-73.5207543`.
- [x] Downloaded monthly NASA POWER series for `PRECTOTCORR`, `T2M`, `T2M_MAX`, `T2M_MIN`, `RH2M`, `WS2M`, and `ALLSKY_SFC_SW_DWN` for 2000-2025.
- [x] Downloaded daily NASA POWER series for the same variables for `2000-01-01` through `2026-03-24`.
- [x] Saved raw NASA POWER JSON responses in `data/raw/climate/`.
- [x] Saved harmonized long and wide climate tables in `data/interim/harmonized/`.
- [x] Wrote a NASA POWER download manifest in `data/raw/metadata/2026-03-25_nasa_power_download_manifest.csv`.
- [x] Refreshed `data/raw/metadata/raw_file_registry.csv` so the raw climate downloads are registered.

## Completed on 2026-03-25: International Cocoa Block

- [x] Verified a practical daily and monthly cocoa futures source through Yahoo Finance `CC=F`.
- [x] Verified the official World Bank Pink Sheet monthly workbook already cited in the repository and extracted the cocoa benchmark series from it.
- [x] Downloaded Yahoo Finance cocoa futures history at daily frequency from `2000-01-03` through `2026-03-25`.
- [x] Downloaded Yahoo Finance cocoa futures history at monthly frequency from `2000-01-01` through `2026-03-01`.
- [x] Downloaded the World Bank monthly cocoa benchmark from `1960-01-01` through `2026-02-01`.
- [x] Saved raw international source files in `data/raw/international/`.
- [x] Saved harmonized international source tables in `data/interim/harmonized/`.
- [x] Cleaned the official monthly benchmark into `data/interim/cleaned/world_cocoa_prices_cleaned.csv`.
- [x] Cleaned the Yahoo Finance futures series into `data/interim/cleaned/world_cocoa_futures_prices_cleaned.csv`.
- [x] Wrote `data/raw/metadata/2026-03-25_international_cocoa_download_manifest.csv` and refreshed `data/raw/metadata/raw_file_registry.csv`.

## Completed on 2026-03-25: Colombian Domestic Block

- [x] Verified the official AgroNet weekly cacao reference page published by the Ministerio de Agricultura y Desarrollo Rural.
- [x] Parsed the AgroNet weekly cacao table into a reproducible domestic price time series.
- [x] Downloaded the weekly domestic cacao series from `2021-08-23` through `2026-03-29`.
- [x] Aggregated the weekly domestic cacao series to monthly means from `2021-08-01` through `2026-03-01`.
- [x] Saved the raw AgroNet HTML page plus machine-readable weekly and monthly CSV/JSON snapshots in `data/raw/colombia/`.
- [x] Saved harmonized weekly and monthly domestic cacao tables in `data/interim/harmonized/`.
- [x] Cleaned the weekly domestic cacao series into `data/interim/cleaned/colombia_cocoa_prices_cleaned.csv`.
- [x] Wrote `data/raw/metadata/2026-03-25_colombia_cocoa_download_manifest.csv` and refreshed `data/raw/metadata/raw_file_registry.csv`.
- [x] Checked the official DANE SIPSA historical-workbook path and confirmed it is better treated as supplementary wholesale context because recent files surface chocolate products more clearly than cacao beans.

## Completed on 2026-03-25: EU Downstream Block

- [x] Verified the official Eurostat HICP monthly API path for the EU downstream price block.
- [x] Confirmed the implemented primary item code as `CP01183` (`Chocolate`) for `EU27_2020`.
- [x] Downloaded the official Eurostat EU27 chocolate HICP monthly index from `2016-12-01` through `2025-12-01`.
- [x] Downloaded additional Eurostat downstream robustness indicators for `EU27_2020`: `CP01213`, `CP0118`, and `CP01184`.
- [x] Downloaded a longer country-level Eurostat chocolate series for France (`FR`, `CP01183`) from `1996-01-01` through `2025-12-01`.
- [x] Saved the raw Eurostat JSON responses in `data/raw/eu/`.
- [x] Saved the harmonized Eurostat monthly tables in `data/interim/harmonized/`.
- [x] Cleaned the EU downstream series into `data/interim/cleaned/eu_price_indicators_cleaned.csv`.
- [x] Wrote `data/raw/metadata/2026-03-25_eu_price_download_manifest.csv` and refreshed `data/raw/metadata/raw_file_registry.csv`.
- [x] Documented the Eurostat January 2026 ECOICOP 2 classification transition so the current `2025-12` endpoint is explicit rather than hidden.

## Completed on 2026-03-25: Macro Controls Block

- [x] Verified the official Banco de la Republica historical TRM service for daily `COP/USD`.
- [x] Verified the official EIA Brent history pages for daily and monthly Europe Brent spot prices.
- [x] Downloaded the BanRep TRM daily series from `1991-11-27` through `2026-03-26`.
- [x] Downloaded the EIA Brent daily series from `1987-05-20` through `2026-03-23`.
- [x] Downloaded the EIA Brent monthly series from `1987-05-01` through `2026-02-01`.
- [x] Saved raw BanRep JSON and raw EIA HTML plus machine-readable CSV/JSON snapshots in `data/raw/macro/`.
- [x] Cleaned the macro controls into `data/interim/cleaned/macro_controls_cleaned.csv`.
- [x] Extended the latest Brent monthly observation to `2026-03-01` by aggregating the official daily EIA series because the official monthly page currently ends at `2026-02-01`.
- [x] Wrote `data/raw/metadata/2026-03-25_macro_controls_download_manifest.csv` and refreshed `data/raw/metadata/raw_file_registry.csv`.
