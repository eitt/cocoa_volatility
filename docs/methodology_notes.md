# Methodology Notes

## Frequency Choice

The baseline frequency is monthly because it balances data availability, comparability, and econometric tractability across domestic, international, EU, trade, and macro series.

## Core Transformations

- nominal prices
- real prices
- natural logarithms
- log differences or returns
- rolling volatility indicators
- exchange-rate-adjusted price series

## Baseline Econometric Sequence

1. Descriptive plots and summary statistics
2. ADF and KPSS stationarity tests
3. Optional Phillips-Perron for robustness
4. ARIMA or ARIMAX for key univariate series
5. Engle-Granger and Johansen co-integration tests
6. VAR or VECM depending on integration results
7. Granger causality, impulse-response functions, and variance decomposition where appropriate

## Vulnerability Interpretation

Transmission estimates are interpreted through exposure channels such as:

- sensitivity to global benchmark volatility
- weak bargaining power in domestic chains
- incomplete transmission of favorable downstream price changes
- interaction with climate or production stress

## Climate Extension Rule

The 2025 biomass-density paper is treated as:

- contextual theoretical support
- a robustness extension
- or a discussion bridge

It is not a mandatory regressor in the main co-integration specification.
