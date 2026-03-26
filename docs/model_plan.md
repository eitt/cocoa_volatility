# Model Plan

## Current Core Monthly System

- Colombian cocoa price proxy
- world cocoa benchmark price
- EU chocolate indicator
- `COP/USD` exchange rate
- Brent oil price

## Current Context and Extension Series

- Yahoo Finance cocoa futures history for higher-frequency diagnostics
- auxiliary Eurostat cocoa, confectionery, sweets, and France chocolate indicators
- NASA POWER precipitation, temperature, humidity, wind, and solar-radiation variables

## Current Descriptive Asset Set

- summary statistics
- same-length common-window summary statistics
- series coverage and pairwise overlap tables
- level and log-return correlation matrices
- imputation audit table
- imputed statistical-properties tables
- all-series overview table combining supply-chain and weather series
- stationarity tests
- ARIMA model diagnostics
- climate summary and climate-core correlation tables

## Current Figure Set

- price trend comparison
- same-length core panels
- indexed series comparison
- data-availability figures
- correlation heatmaps
- climate panels and climate-core correlation heatmap
- one STL decomposition figure for each core series
- one STL decomposition figure for each weather series
- monthly volatility comparison
- rolling return volatility
- core transmission actual-versus-fitted figures
- core return impulse-response figure
- weather-vulnerability actual-versus-fitted figures
- weather-vulnerability index figure

## Completed Modeling Steps

1. Ran aligned-sample stationarity and volatility diagnostics on the imputed core panel.
2. Ran a parallel weather statistical-properties stage and built an all-series overview.
3. Estimated a parsimonious core transmission chapter with HAC-robust level and return equations.
4. Ran pairwise Engle-Granger, directional Granger causality, and a compact return VAR on the core system.
5. Estimated a weather-vulnerability chapter with selected weather covariates, model-comparison tables, and exploratory vulnerability indicators.
6. Documented outputs by sample type, including balanced and imputed aligned variants.

## Next Modeling Priorities

1. Run robustness versions using auxiliary EU indicators and the futures series.
2. Compare balanced non-imputed and imputed core transmission estimates side by side in the manuscript tables.
3. Test alternative weather selections or lag structures only if they improve the vulnerability interpretation rather than simply enlarging the model.
4. Extend the Colombian domestic series backward if a defensible official source becomes available.
5. Consider real-price specifications or exchange-rate-adjusted variants as robustness checks.

## Robustness Tracks

- alternative domestic price definitions
- alternative EU indicator definitions
- nominal versus real specifications
- subsample checks
- imputed versus non-imputed aligned samples
- climate-control extension for selected departments
