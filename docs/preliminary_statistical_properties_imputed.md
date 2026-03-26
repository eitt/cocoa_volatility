# Preliminary Statistical Properties on the Imputed Aligned Panel

## Scope

This note summarizes the preliminary statistical outputs generated from the aligned monthly sample `2021-08-01` to `2025-12-01`.

- Core supply-chain panel:
  - `53` level observations after imputing the single missing Colombian cocoa value in `2025-09-01`
  - `52` monthly log-return observations after differencing
- Weather panel:
  - `53` level observations after imputing the single missing solar-radiation value in `2025-12-01`
  - `52` monthly log-return observations after differencing

## Imputation Assumptions

- The core supply-chain block and the weather block are imputed separately.
- The primary imputation method is iterative multivariate imputation in each block.
- The block-specific approach was chosen to avoid forcing missing weather values to be mechanically inferred from price variables, or missing core price values from weather variables.
- KNN estimates are still exported as sensitivity references.

Current imputed cells:

- `2025-09-01` `colombia_cocoa_price_cop_kg`: iterative estimate `23855.548769`
- `2025-12-01` `nasa_surface_solar_radiation_mj_m2_day`: iterative estimate `18.387004`

## Main Caveats

- The aligned sample is still short for strong long-run inference.
- Phillips-Perron results are unavailable in the current output tables because the optional `arch` package is not installed here.
- Monthly weather series are contextual location-level averages, not farm-observed production outcomes.
- Precipitation log returns are mechanically very volatile because small monthly precipitation values can make proportional changes very large.
- STL decomposition with `53` monthly points is descriptive rather than definitive.

## Preliminary Core Findings

- Core level series continue to behave like non-stationary variables:
  - ADF does not reject for the five core level series.
  - KPSS rejects stationarity for Colombian cocoa, world cocoa, EU chocolate, and Brent.
  - `COP/USD` is the closest core level series to stationarity under KPSS.
- Core log returns are much closer to stationarity:
  - ADF rejects for Colombian cocoa, world cocoa, EU chocolate, and `COP/USD`.
  - Brent returns are borderline on ADF (`p = 0.081`) but KPSS does not reject stationarity.
- The highest annualized return volatility in the core block remains:
  - Colombian cocoa: `0.376`
  - world cocoa: `0.367`
  - Brent: `0.258`
- ARCH-LM indicates volatility clustering at `p < 0.05` for:
  - world cocoa
  - EU chocolate
- In the core STL outputs, EU chocolate shows the strongest trend and seasonal structure.

## Preliminary Weather Findings

- Several weather series look more stationary in levels than the core price system:
  - precipitation, max temperature, min temperature, humidity, wind speed, and solar radiation all reject a unit root under ADF at `p < 0.05`
  - mean temperature is borderline in levels on ADF (`p = 0.055`) but KPSS does not reject stationarity
- Weather log returns are stationary across the block under the current ADF and KPSS readout.
- Annualized return volatility is highest for:
  - precipitation: `3.106`
  - wind speed: `0.347`
  - solar radiation: `0.283`
  - relative humidity: `0.250`
- No weather series shows ARCH-LM significance at `p < 0.05`; precipitation is the closest at `p = 0.070`.
- STL decomposition suggests the strongest seasonal weather structure is:
  - solar radiation: seasonal strength `0.691`
  - precipitation: seasonal strength `0.505`
  - wind speed: seasonal strength `0.470`

## Vulnerability Interpretation

- The supply-chain price block appears to combine non-stationary levels with volatile and, in some cases, clustered return dynamics, which is consistent with a vulnerability framing based on unstable market exposure.
- The weather block is more useful here as structured environmental context than as evidence of direct causal transmission.
- Strong seasonality in solar radiation and precipitation can help frame when farmers are exposed to environmental regularities, while volatile cocoa-price returns describe when they are exposed to market shocks.
- The current design therefore supports a vulnerability narrative built from two interacting dimensions:
  - unstable downstream and benchmark price dynamics across the supply chain
  - recurring environmental seasonality plus occasional weather volatility in the producing location

## Follow-on Modeling Stage Now Implemented

- The core supply-chain system is now reported as a separate transmission chapter with aligned-sample regressions, Engle-Granger tests, Granger causality, and compact VAR diagnostics.
- The weather block is now reported as a second chapter that extends the domestic-price equations with selected weather variables and builds exploratory vulnerability indicators.
- This means the statistical-properties stage now functions as the descriptive and diagnostic bridge into two distinct empirical chapters rather than as a standalone endpoint.

## Main Output Files

- `outputs/tables/table_statistical_properties_all_series_overview.csv`
- `outputs/tables/table_statistical_properties_weather_overview.csv`
- `outputs/tables/table_stationarity_tests_imputed_all_series_levels.csv`
- `outputs/tables/table_stationarity_tests_imputed_weather_levels.csv`
- `outputs/tables/table_volatility_summary_imputed_all_series_log_returns.csv`
- `outputs/tables/table_arch_lm_tests_imputed_weather_log_returns.csv`
- `outputs/tables/table_decomposition_strength_imputed_all_series.csv`
- `data/processed/final_series/all_series_common_window_panel_imputed.csv`
