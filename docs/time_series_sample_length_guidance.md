# Time-Series Sample-Length Guidance

## Current aligned sample

- Shared calendar window across the five core monthly series: `2021-08-01` to `2025-12-01` (`53` calendar months).
- Balanced common sample with no missing values across the five core series: `52` monthly observations.
- Remaining missing month inside the shared calendar window: `2025-09-01`, missing only for the Colombian domestic cocoa series.
- Climate-augmented common sample with all currently merged weather variables: `51` monthly observations because the climate block also loses `2025-12-01` for surface solar radiation.
- Imputed aligned core panel: `53` level observations for descriptive continuity, but still not a substitute for a longer observed span.

## Practical interpretation

- The aligned `53`-month window is appropriate for descriptive plots, aligned summary statistics, and return calculations.
- The balanced `52`-observation sample is acceptable for preliminary descriptive correlations and cautious exploratory bivariate modeling.
- The current balanced monthly sample is short for strong claims from multivariate cointegration, Johansen systems, or a five-variable VAR/VECM.
- The `51`-observation climate-augmented sample is even more restrictive, so climate variables should be treated as contextual or robustness inputs unless the specification remains very parsimonious.

## Literature-based guidance

- Hakkio and Rush argue that for cointegration, increasing frequency from annual to quarterly or monthly does not solve a short-span problem by itself; cointegration is a long-run concept and needs a long span of data.
- Schwert shows that unit-root tests have important finite-sample distortions and can be sensitive to misspecification, which is a warning sign when the sample is short.
- Beaulieu and Miron derive monthly seasonal-unit-root mechanics and finite-sample critical values for monthly data, highlighting that monthly seasonality is not a trivial extension of lower-frequency testing.
- Del Barrio Castro and Osborn show that finite-sample seasonal-unit-root procedures can still have a high probability of incorrectly concluding seasonal integration in practice.

## Working recommendation for this project

- Treat `52` monthly observations as a preliminary research window, not a strong final window for the full multivariate long-run system.
- For monthly downstream transmission work with seasonality and long-run relationships, a safer target is roughly `96-120` monthly observations.
- This `96-120` range is an inference from the literature above plus the practical need to observe many annual cycles and to estimate long-run dynamics with more than a bivariate system.
- If the domestic series cannot be extended materially, the safer econometric path is to keep the current sample for descriptive analysis and cautious reduced-form models, then avoid over-parameterized monthly VAR/VECM specifications.
- The imputed aligned core panel is useful for continuous visualization and sensitivity checks, but it does not materially relax the sample-length problem for long-run inference.

## Sources

- Hakkio, C., and Rush, M. (1991). *Cointegration: how short is the long run?* Journal of International Money and Finance. https://doi.org/10.1016/0261-5606(91)90008-8
- Schwert, G. W. (1989). *Tests for Unit Roots: A Monte Carlo Investigation.* Journal of Business & Economic Statistics. https://doi.org/10.1080/07350015.1989.10509723
- Beaulieu, J. J., and Miron, J. A. (1993). *Seasonal unit roots in aggregate U.S. data.* Journal of Econometrics. https://doi.org/10.1016/0304-4076(93)90018-Z
- del Barrio Castro, T., and Osborn, D. R. (2008). *Testing for seasonal unit roots in periodic integrated autoregressive processes.* Econometric Theory. https://doi.org/10.1017/S0266466608080420
