# Citation Justification

This note explains why each bibliography entry in `references/cocoa_volatility.bib` is included in the repository.

The operational sources that now appear directly in the manuscript draft have been promoted into the bibliography so the paper can cite the same official source family that the pipeline actually uses.

## Data and Institutional Sources

### `agronet_cacao`

Used as the main citation for the Colombian domestic cocoa series because the implemented monthly domestic panel is derived directly from this official AgroNet weekly reference page.

### `dane_sipsa`

Used to justify the broader Colombian domestic market block as supplementary wholesale context. The implemented domestic cacao series now comes from AgroNet's official weekly cacao reference page, while SIPSA remains useful for adjacent market-proxy checks.

### `icco_qbcs`

Used for international cocoa benchmark prices and supporting trade context. ICCO is a specialized intergovernmental source dedicated to cocoa-market statistics.

### `worldbank_pinksheet`

Used as the core public benchmark source for monthly commodity prices, including cocoa. It anchors the official international price block in the merged monthly panel.

### `yahoo_finance_ccf`

Used for the daily and monthly cocoa futures series retained for volatility diagnostics, robustness analysis, and higher-frequency market context. It is cited as a secondary market-data source rather than as the manuscript's main benchmark price series.

### `eurostat_hicp`

Used to justify the European downstream price block. Eurostat HICP metadata provides the official framework for monthly consumer price indices that can be narrowed to cocoa or chocolate-related classes and supports the main EU27 chocolate series plus auxiliary downstream robustness indicators.

### `banrep_trm`

Used to document the official macro-control source for the `COP/USD` exchange-rate series included in the aligned monthly panel and the transmission models.

### `eia_brent`

Used to document the official source family for the Brent oil series used as a macro control in the merged panel and transmission models.

### `un_comtrade`

Used for trade-flow measurement between Colombia and European partners. It is the standard international source for HS-based import and export statistics.

### `nasa_power_api`

Used for the climate robustness extension. NASA POWER provides documented daily and monthly meteorological time series suitable for location-based monthly climate panels using representative coordinates.

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

### `hakkio_rush_1991`

Used to justify the manuscript's caution about short common windows in cointegration analysis. It supports the claim that a short span can undermine long-run inference even when a system contains a reasonable number of observations.

### `acosta_ihle_voncramon_2019`

Used in the introduction and methods to position the paper's contribution relative to the price-transmission literature. It is particularly useful for motivating the combination of market context, data architecture, and econometric strategy rather than treating transmission as a purely mechanical time-series exercise.

### `vanbuuren_groothuisoudshoorn_2011`

Used to justify the iterative multivariate imputation approach and to frame the manuscript's discussion of chained conditional models for block-specific missing-data treatment.

### `troyanskaya_etal_2001`

Used to justify the KNN imputation sensitivity benchmark. In this project it is not the primary imputation method, but it provides the methodological rationale for retaining a neighborhood-based comparison estimate for the missing observations.

## Climate and Agronomic Extension

### `talero_sarmiento_etal_2025`

Included because the project instructions explicitly point to this paper for the climate and agronomic extension. It now serves as contextual framing for the merged NASA POWER block and should inform robustness discussion rather than mechanically forcing the climate variables into the core co-integration model.
