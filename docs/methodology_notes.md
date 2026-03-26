# Methodology Notes

## Frequency Choice

The baseline frequency is monthly because it balances data availability, comparability, and econometric tractability across domestic, international, EU, macro, and climate series.

## Alignment Rule

- Keep the full monthly panel for source coverage, long-history context, and exploratory plots.
- Constrain comparative descriptive work to the shared core window `2021-08-01` to `2025-12-01`.
- Distinguish between:
  - the shared core calendar window (`53` rows)
  - the balanced common core sample (`52` complete rows)
  - the climate-augmented common sample (`51` complete rows)

## Missing-Data Rule

- Preserve the raw and merged datasets without overwriting missing observations.
- Use the non-imputed balanced sample as the baseline for reported aligned descriptive statistics.
- Export imputed aligned panels only as transparent continuity and sensitivity artifacts.
- The current primary imputed panel uses iterative multivariate imputation; the KNN version is retained as a comparison.
- The imputed aligned core panel is also the input for the dedicated statistical-properties reporting step.
- For the weather block, imputation is done within the weather variables only and then merged with the imputed core panel for the aggregated all-series overview. This avoids forcing missing weather values to be mechanically inferred from price variables, or missing core price values from weather variables.

## Core Transformations

- nominal prices
- real prices
- natural logarithms
- log differences or returns
- rolling volatility indicators
- exchange-rate-adjusted price series
- shared-window alignment
- indexed series rebased to 100 for cross-series visual comparison
- STL decomposition with monthly period `12`

## Figure Conventions

- Use the Okabe-Ito colorblind-safe palette across all line plots and panel figures.
- Use fixed theoretical bounds of `-1` to `1` for correlation heatmaps.
- Render heatmap annotation values in black when coefficients fall between `-0.2` and `0.2`.
- Use short acronyms in dense heatmaps and place the acronym key in a full-width footer.

## Baseline Econometric Sequence

1. Descriptive plots, coverage diagnostics, and aligned summary statistics.
2. ADF and KPSS stationarity tests on the relevant aligned sample.
3. Parallel statistical-properties reporting for the weather block and the full supply-chain-plus-weather panel.
4. Optional Phillips-Perron for robustness.
5. ARIMA or ARIMAX for key univariate series.
6. Baseline core transmission chapter with parsimonious HAC-robust level and return equations on the aligned monthly core system.
7. Pairwise Engle-Granger, directional Granger causality, and compact VAR diagnostics where sample length is still defensible.
8. Separate weather-vulnerability chapter that extends the domestic equations with selected weather stress variables and builds exploratory vulnerability indicators.

## Vulnerability Interpretation

Transmission estimates are interpreted through exposure channels such as:

- sensitivity to global benchmark volatility
- weak bargaining power in domestic chains
- incomplete transmission of favorable downstream price changes
- interaction with climate or production stress

## Climate Extension Rule

The 2025 biomass-density paper and NASA POWER block are treated as:

- contextual theoretical support
- a descriptive environmental companion to the price system
- a robustness extension when the shorter climate-augmented sample is acceptable
- or a discussion bridge between market exposure and production stress

The climate variables are now visible in the merged panel and descriptive figures, but they are not mandatory regressors in the core co-integration specification.
They are now handled as a separate weather-vulnerability chapter so the supply-chain transmission story and the vulnerability context can be reported in two distinct sections.
