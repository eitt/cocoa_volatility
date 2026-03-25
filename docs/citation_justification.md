# Citation Justification

This note explains why each bibliography entry in `references/cocoa_volatility.bib` is included in the repository.

## Data and Institutional Sources

### `dane_sipsa`

Used to justify the Colombian domestic price block. SIPSA is the most natural official starting point for wholesale agricultural prices that can proxy farm-linked cocoa market conditions in Colombia.

### `icco_qbcs`

Used for international cocoa benchmark prices and supporting trade context. ICCO is a specialized intergovernmental source dedicated to cocoa-market statistics.

### `worldbank_pinksheet`

Used as a public benchmark source for monthly commodity prices, including cocoa. It is especially useful when a standardized cross-commodity benchmark is needed.

### `eurostat_hicp`

Used to justify the European downstream price block. Eurostat HICP metadata provides the official framework for monthly consumer price indices that can be narrowed to cocoa or chocolate-related classes.

### `un_comtrade`

Used for trade-flow measurement between Colombia and European partners. It is the standard international source for HS-based import and export statistics.

### `nasa_power_api`

Used for the climate robustness extension. NASA POWER provides documented daily and monthly meteorological time series suitable for department-level proxies using representative coordinates.

## Econometric Foundations

### `box_jenkins_reinsel_ljung_2015`

Provides the baseline ARIMA reference for univariate time-series modeling and forecasting decisions.

### `dickey_fuller_1979`

Supports the Augmented Dickey-Fuller family of stationarity testing used at the beginning of the empirical workflow.

### `phillips_perron_1988`

Supports Phillips-Perron stationarity testing as a robustness complement when the error process may violate simpler assumptions.

### `kwiatkowski_etal_1992`

Supports KPSS testing so the workflow does not rely on a single null-hypothesis structure for stationarity assessment.

### `engle_granger_1987`

Provides the two-step co-integration framework for testing long-run relationships between Colombian, international, and EU price series.

### `johansen_1991`

Provides the multivariate co-integration framework needed when the model includes more than two jointly endogenous price series.

### `granger_1969`

Supports the causality tests used to explore directional predictive linkages across market series.

### `lutkepohl_2005`

Provides a standard reference for VAR and VECM estimation, impulse-response interpretation, and forecast error variance decomposition.

## Climate and Agronomic Extension

### `talero_sarmiento_etal_2025`

Included because the project instructions explicitly point to this paper for the climate and agronomic extension. It should inform contextual framing, variable selection, or a robustness appendix rather than the core co-integration model unless alignment is demonstrated.
