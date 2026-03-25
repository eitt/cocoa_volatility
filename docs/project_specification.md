# Project Specification

## Title

**Cocoa volatility and supply chain vulnerability of smallholder cocoa farmers to global commodity price volatility: From Colombian farms to European markets**

## Objective

Build a transparent empirical workflow that links Colombian cocoa-related prices, international cocoa benchmarks, European downstream indicators, and trade or supply-chain linkages in a way that supports reproducible econometric analysis and manuscript-ready outputs.

## Analytical Scope

- Colombian domestic cocoa prices, preferably at wholesale or farm-linked market level.
- International cocoa commodity benchmarks from official or intergovernmental sources.
- European downstream indicators such as HICP, CPI, PPI, or import price proxies for cocoa and chocolate.
- Trade links between Colombia and Europe for cocoa beans and processed cocoa goods.
- Exchange rate, inflation, and optional freight or input-cost controls.
- Climate and agronomic extensions used only as contextual or robustness material unless time and space alignment are defensible.

## Preferred Design

The repository follows a functional programming style:

- reusable small functions
- explicit inputs and outputs
- no classes
- no hidden state
- script entry points that orchestrate module functions
- YAML configuration for paths, variables, and source mappings

## Baseline Research Outputs

- analysis-ready merged monthly dataset
- descriptive tables and figures
- stationarity test table
- ARIMA summaries
- co-integration and transmission results
- vulnerability indicators
- bibliography and citation rationale notes

## Modeling Priorities

1. Monthly harmonization across all selected datasets.
2. Construction of nominal, real, logged, and differenced series.
3. Descriptive inspection of trends, seasonality, and volatility.
4. Stationarity testing using ADF, KPSS, and optional Phillips-Perron.
5. ARIMA or ARIMAX for key series.
6. Engle-Granger and Johansen testing for long-run relationships.
7. VAR or VECM dynamics, including Granger causality and impulse responses where justified.
8. Vulnerability interpretation focused on smallholder exposure and benefit transmission.

## Output Standards

Every dataset should record:

- source institution
- raw filename
- download date
- transformed filename
- units
- frequency
- missing-data handling
- transformation steps
- manuscript citation

Every model output should record:

- sample period
- variables used
- lag rule
- diagnostic tests
- interpretation limits
