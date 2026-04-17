# Editorial Decisions for Version 3

## Purpose

This revision updates `paper/paper_v3_integrated.tex` so the disaster layer is framed in a methodologically defensible way. The paper now reads with a clearer hierarchy:

- core contribution: benchmark transmission into Colombian cocoa prices, with secondary downstream evidence;
- resilience extension: weather and disaster information as territorial exposure and contextual amplification;
- interpretation: vulnerability depends on both market pass-through and the local conditions under which it is experienced.

The key editorial correction is that disaster variables are no longer written as if they were directly comparable econometric series to the world cocoa benchmark, exchange rate, oil price, or the main domestic price block.

## What Changed in This Revision Pass

- Rewrote the abstract so the paper states upfront that the disaster layer is a nested territorial exposure extension, not a co-equal transmission system.
- Rewrote the introduction to explain why disaster data are used as contextual overlays, episode markers, and robustness tools rather than as benchmark-like monthly series.
- Strengthened the conceptual framing with literature on composite territorial-risk indicators and contextual resilience measurement.
- Rewrote the methods section so the disaster block is justified as:
  - shorter than the core market window,
  - sparse and irregular,
  - partly zero-inflated,
  - partly synthetic,
  - and spatially mismatched relative to the climate point series and the producer-linked price system.
- Rewrote the results text so the hazard tables are interpreted as contextual overlay screens, not as a contest among co-equal price drivers.
- Rewrote the discussion and conclusion to make the limitations explicit and to emphasize contextual amplification instead of short-run price leadership.

## Disaster Framing Revision

The disaster layer is now explicitly positioned as a territorial resilience extension. In the revised manuscript it appears in five roles only:

- a descriptive exposure layer through the event totals and hazard-mix figures;
- a contextual stress proxy through the PCA-based territorial-pressure index;
- a parsimonious robustness extension through one-at-a-time hazard-overlay regressions;
- an episode-level marker through hydrometeorological counts in the nested window;
- an exploratory event-window comparison around the October 2022 peak pressure month.

The manuscript now states clearly across the introduction, methods, results, discussion, and conclusion that the disaster layer is not fully comparable to the market series because:

- the temporal window is shorter and only partially overlaps the main transmission sample;
- the registry counts are sparse, irregular, and in some cases strongly zero-inflated;
- the PCA measure is a synthetic territorial-pressure construct built from heterogeneous features;
- the disaster registry, climate reference point, and producer-linked price system operate at different spatial scales.

## Fallacies Corrected or Softened

### 1. Comparability fallacy

Corrected in the methods, results, discussion, and conclusion. The PCA measure is now described as a synthetic territorial-pressure indicator, not as a canonical economic time series. Hydrometeorological counts are described as contextual episode markers rather than as benchmark peers.

### 2. Overinterpretation fallacy

Corrected in the results and discussion. Weak coefficients and weak disaster-led diagnostics are no longer treated as evidence of disaster leadership. The text now says the disaster layer enriches interpretation even when it does not dominate short-run price formation.

### 3. Sample-window fallacy

Corrected in the introduction, data section, methods, and discussion. The shorter 35-observation disaster return window is now treated as a substantive reason for parsimony rather than as a minor technical footnote.

### 4. Shock-selection endogeneity

Softened and disclosed in the methods, results, and discussion. October 2022 is now described as an exploratory, data-driven peak month selected from the same nested hazard data used for screening, not as a strictly exogenous treatment date.

### 5. Spatial-scale mismatch

Added explicitly to the data and discussion sections. The manuscript now notes that the disaster registry is departmental, the climate data are point-based, and the price series are broader producer-linked references. This supports contextual interpretation but limits precise local causal attribution.

### 6. Reporting automation fallacy

Corrected editorially. Pipeline-stamped phrasing that overstated the role of the disaster variables was removed. Captions and narrative were manually revised so they no longer imply stronger evidence than the models actually provide.

## Literature Integrated for the Revised Framing

No additional external download was required in this pass because the project already contained a usable local resilience/disaster review and an expanded bibliography. The revised manuscript now leans more directly on existing references already present in `paper/references/cocoa_volatility.bib`, especially:

- `Parsons2021` and `Garschagen2021` for composite territorial-risk and resilience indicators;
- `Djalante2011` and `Birkmann2023` for resilience as context-sensitive absorption and governance under hazard conditions;
- `hakkio_rush_1991` and `lutkepohl_2005` for short-sample caution in multivariate time-series work;
- `acosta_ihle_voncramon_2019` for parsimonious price-transmission design logic when structure and timing differ across blocks.

These citations were integrated to justify the revised methodological stance rather than to claim that the exact same design is standard in cocoa.

## Figure Decisions

The revision kept the V1 visual identity by using the project palette defined in the shared plotting helpers.

### Figures retained in the main text

- `figure_v1_long_run_coverage.png`
- `figure_indexed_core_series_common_window_imputed.png`
- `figure_weather_vulnerability_index.png`
- `figure_monthly_event_totals.png`
- `figure_hazard_domain_mix.png`
- `pca_indicator_change_points.png`

### Figure moved into the main text in updated form

- The earlier V2-style descriptive stack was replaced by a cleaned figure generated in this pass:
  - `paper/figures/figure_contextual_overlay_alignment.png`
  - generated via `scripts/13_compare_hazard_overlays.py`
  - purpose: show the nested-window alignment of world returns, Colombian returns, hydrometeorological counts, and composite territorial pressure without the pipeline-style V2 labeling.

### Figures kept in the supplementary section

- `figure_correlation_heatmap_levels_common_window_imputed.png`
- `figure_climate_core_correlation_common_sample.png`
- `figure_climate_series_panels_common_window.png`
- `figure_core_return_impulse_response.png`
- `figure_v3_actual_vs_fitted.png`
- `figure_v3_integrated_heatmap.png`
- `figure_top_municipalities.png`
- `figure_pca_loadings.png`

### Figures removed as separate displays because their evidence is preserved elsewhere

- `figure_v3_descriptive_stack.png`

Its evidence is now carried by the new cleaned main-text alignment figure, so the underlying V2 content was preserved without leaving a redundant pipeline-style display in the manuscript.

## What Was Retained From V1 and V2

### Retained from V1

- the benchmark-transmission backbone;
- the aligned-window logic;
- the core descriptive, stationarity, and transmission tables;
- the full-window weather-context block;
- the project figure palette and visual identity.

### Retained from V2

- the Santander disaster registry;
- the hazard descriptives;
- the earthquake infeasibility result;
- the PCA-based multi-hazard pressure construct;
- the October 2022 episode logic;
- the supporting diagnostic figures and tables that remain useful as supplementary evidence.

## Empirical Redesign Implemented

- Kept the core HAC-robust level and return models as the main empirical system.
- Kept the weather block as contextual environmental stress rather than as a competing transmission model.
- Kept the disaster block only in nested-window form.
- Reframed hazard screening as selection of contextual overlays rather than selection of a rival benchmark series.
- Kept the hydrometeorological count as the most defensible direct monthly episode marker.
- Kept the PCA indicator only as a robustness and territorial-pressure construct.
- Kept the event-window comparison, but relabeled it as exploratory and data-driven.
- Updated `scripts/13_compare_hazard_overlays.py` to generate:
  - `paper/tables/table_hazard_signal_screening.csv`
  - `paper/tables/table_hazard_overlay_model_comparison.csv`
  - `paper/figures/figure_contextual_overlay_alignment.png`

## Remaining Empirical Limits

- The core return sample still contains only 52 monthly observations.
- The nested disaster return sample still contains only 35 observations.
- The producer-linked cocoa price is still a broad reference series rather than a farm-gate panel.
- The climate data remain point-based.
- The disaster registry remains departmental and irregular.
- The event window remains exploratory because the peak month is data-driven.

The paper is therefore strongest as a resilience-oriented transmission study with a contextual territorial exposure layer, not as a definitive causal model of disaster-led cocoa pricing.

## Build and Verification Status

- `scripts/13_compare_hazard_overlays.py` runs successfully.
- `python -m py_compile scripts/13_compare_hazard_overlays.py` passes.
- The manuscript source has been updated to reference the new main-text contextual alignment figure and the revised methodological framing.
