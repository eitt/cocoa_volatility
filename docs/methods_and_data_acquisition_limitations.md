# Methods and Data-Acquisition Limitations

## Data-acquisition limitations

- The Colombian domestic cocoa series is the shortest core block in the project and currently starts in `2021-08`.
- AgroNet price formatting is not perfectly stable across weeks; some historical rows use malformed separator patterns that required parser rules and validation checks.
- The EU chocolate block is based on the legacy Eurostat COICOP path through `2025-12`; the January 2026 classification change means continuation requires a documented handoff to the ECOICOP 2 structure.
- The official World Bank monthly cocoa benchmark currently ends at `2026-02-01`, so the international benchmark is not fully synchronized with all March 2026 controls.
- The official EIA monthly Brent history currently ends at `2026-02-01`; the March 2026 monthly Brent value in this project is derived from the official daily EIA history.
- The NASA POWER monthly climate block currently has one missing solar-radiation month at `2025-12-01`.

## Missing-data limitations

- Inside the shared core window (`2021-08-01` to `2025-12-01`), there is one missing month: `2025-09-01` for the Colombian cocoa series.
- Any imputed value is an estimate, not a recovered ground-truth observation.
- Imputation reduces discontinuities in aligned descriptive figures but does not remove uncertainty about the missing observation.
- When the full climate block is required, the common sample drops again because the solar-radiation series is missing `2025-12-01`.
- The current all-series overview uses block-specific iterative imputation: the core supply-chain block and the weather block are imputed separately and then merged.

## Method limitations

- KNN imputation depends on distance relationships in a very small aligned sample and can be sensitive to scaling and local neighbors.
- Iterative multivariate imputation depends on conditional model structure and the correlation pattern in the observed sample.
- With only one missing value in the aligned window, both methods are mainly sensitivity tools rather than strong identification devices.
- Correlation matrices from a short common sample can look strong even when the effective long-run evidence is limited.
- Return correlations are based on an even shorter effective sample because differencing removes the first aligned month and any month adjacent to a missing value.
- Climate-price correlations are descriptive and sample-specific; they should not be treated as structural without a stronger identification strategy and a longer overlap.
- Log returns on precipitation can look extremely volatile because very small monthly precipitation values make proportional changes mechanically large.
- NASA POWER monthly averages are location-level contextual indicators, not farm-measured agronomic outcomes.
- Phillips-Perron results remain unavailable in the current tables because the optional `arch` dependency is not installed in this environment.

## Presentation limitations

- Fixed `-1` to `1` heatmap scales improve comparability across figures but do not indicate statistical significance.
- Acronym-based corrplots improve readability, but interpretation still depends on the accompanying legend and variable definitions.
- Imputed figures are useful for continuity, but the non-imputed aligned sample should remain the primary reference for descriptive reporting.
- STL decomposition with only `53` monthly points is informative for descriptive patterning, but its seasonal and trend strengths should still be treated as preliminary.

## Modeling implications

- The current aligned monthly window is adequate for descriptive work and careful exploratory reduced-form analysis.
- The current window is still short for confident five-variable monthly Johansen, VECM, or larger VAR systems.
- Any model using the imputed panel should be reported as using imputed data, and sensitivity checks should compare the imputed and non-imputed windows.
- Any model using the complete climate block should explicitly report that the usable aligned sample falls to `51` monthly observations.
- The implemented core transmission chapter should therefore be treated as a parsimonious reduced-form benchmark, not as a definitive structural representation of the whole cocoa supply chain.
- The implemented weather-vulnerability chapter should be read as contextual and vulnerability-oriented evidence, not as proof that local weather dominates the market-transmission mechanism.
