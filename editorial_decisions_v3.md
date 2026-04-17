# Editorial Decisions for Version 3

## Purpose

`paper/paper_v3_integrated.tex` was rebuilt as a journal-style article rather than a working-paper-style draft. The final structure treats benchmark transmission, environmental stress, and territorial resilience as one manuscript logic instead of two partially separate texts.

## Which Prior Version Was Closest to Submission Quality

- `paper/cocoa_volatility_manuscript.tex` was the closest starting point for article structure, prose style, and core econometric exposition.
- `reports/v2/disaster_crisis_report_v2.tex` contributed the disaster registry, hazard figures, and the resilience/disaster framing that was missing from the first version's main narrative.
- The original `paper/paper_v3_integrated.tex` was used only as a partial bridge. It contained useful integration attempts, but it still had inconsistencies in reported statistics, incomplete figure/table coverage, and a weaker methodological justification than the final revision.

## What Was Retained From V1

- The main transmission architecture linking Colombian cocoa prices, the world cocoa benchmark, the EU chocolate index, the COP/USD exchange rate, and Brent oil.
- The aligned-window logic distinguishing long historical coverage from the short comparable monthly estimation window.
- The descriptive, stationarity, and transmission tables that anchor the benchmark pass-through story.
- The weather-context logic, but rewritten more carefully so weather is treated as contextual environmental stress rather than as an unsupported replacement for the market mechanism.
- The exploratory vulnerability indicators, retained as contextual interpretation rather than headline causal findings.

## What Was Retained From V2

- The long-run coverage figure and the disaster-event descriptive figures.
- The official Santander disaster registry as the territorial hazard dataset.
- The original disaster-extension insight that isolated earthquake counts are too sparse for direct time-series use.
- The PCA-based multi-hazard indicator, but repositioned as a robustness overlay rather than the default main result.
- The event-window logic around the October 2022 peak disruption episode.
- The lower-level diagnostic figures and tables, moved to the supplementary section instead of discarded.

## Figure and Table Treatment

### V1 Figures

- `figure_indexed_core_series_common_window_imputed.png`: retained in the main text.
- `figure_correlation_heatmap_levels_common_window_imputed.png`: retained in the supplementary section.
- `figure_core_return_impulse_response.png`: retained in the supplementary section.
- `figure_climate_core_correlation_common_sample.png`: retained in the supplementary section.
- `figure_climate_series_panels_common_window.png`: retained in the supplementary section.
- `figure_weather_vulnerability_index.png`: retained in the main text because it carries the full-window environmental stress context.

### V1 Tables

- Data card: retained in updated form in the main text.
- Sample design: retained in updated form in the main text.
- Descriptive statistics: retained in the main text.
- Statistical properties / stationarity overview: retained in the main text.
- Core transmission results: retained in updated form in the main text.
- Granger-causality table: moved to the supplementary section.
- Weather-extended domestic models: moved to the supplementary section.
- Vulnerability indicator definitions: moved to the supplementary section.

### V2 Figures

- `figure_v1_long_run_coverage.png`: retained in the main text because it clarifies the historical-versus-aligned sample distinction.
- `figure_monthly_event_totals.png` and `figure_hazard_domain_mix.png`: retained in the main text as the disaster descriptive backbone.
- `figure_v3_actual_vs_fitted.png`: retained in the supplementary section.
- `figure_v3_integrated_heatmap.png`: retained in the supplementary section.
- `figure_v3_descriptive_stack.png`: retained in the supplementary section.
- `figure_top_municipalities.png`: retained in the supplementary section.
- `figure_pca_loadings.png`: retained in the supplementary section.
- `pca_indicator_change_points.png`: retained in the main text because it directly supports the event-window interpretation.

### V2 Tables

- Dataset overview and aligned-sample description: merged into the main-text data card and sample design tables.
- Earthquake feasibility table: merged into the main-text hazard screening table.
- Disaster causality table: retained in the supplementary section.
- Return and volatility disaster-overlay tables: merged into the new main-text hazard overlay comparison table.
- Structural comparison table: retained in updated form in the main text as the October 2022 event-window table.
- PCA loadings table and municipality/event summaries: not foregrounded in the main text, but their associated evidence is preserved through the supplementary figures and the supporting hazard-selection outputs.

## Methodological Redesign Implemented

- Kept the core HAC-robust levels and return models from V1.
- Clarified the aligned sample architecture:
  - full merged monthly panel,
  - core aligned levels window,
  - core aligned return window,
  - weather-augmented sample,
  - nested disaster levels window,
  - nested disaster return window.
- Reframed the weather block as contextual environmental stress rather than a competing core model.
- Added explicit volatility and event-window equations so the paper no longer relies on partially implied methods.
- Added a reproducible hazard-screening step through `scripts/13_compare_hazard_overlays.py`.
- Exported two new manuscript-facing tables:
  - `paper/tables/table_hazard_signal_screening.csv`
  - `paper/tables/table_hazard_overlay_model_comparison.csv`

## Direct Disaster Time-Series Feasibility

- A direct disaster time series was **partially feasible**.
- Isolated earthquake counts were **not feasible** for direct integration:
  - 35 aligned return months,
  - only 4 non-zero months,
  - zero share of 0.886.
- A broader direct environmental-disaster series **was feasible**:
  - hydrometeorological event counts were non-zero in 30 of 35 aligned return months,
  - they peak in October 2022,
  - they outperform geophysical counts and total event counts in both nested-window return and volatility overlay fit.
- For that reason, the final manuscript uses `hydrometeorological_events` as the primary direct hazard series in the nested-window overlay.

## Synthetic Indicator Construction

- A synthetic multi-hazard indicator was still constructed and tested.
- The final manuscript retains the PCA disaster-pressure series as a robustness overlay rather than the default main result.
- The retained PCA indicator uses 21 eligible monthly disaster features and explains 33.1% of the standardized variance.
- Both the direct hydrometeorological series and the PCA indicator identify October 2022 as the main peak stress episode, which supports the event-window design.

## How Reviewer Concerns Were Addressed

1. Hazards now appear throughout the article, not only in the abstract.
2. The gap statement was rewritten to explain why the question matters for smallholders, cooperatives, traders, and territorial governance.
3. Formal hypotheses were removed from the introduction and replaced with integrated empirical expectations in the conceptual framing.
4. The ecological-economics link was strengthened by treating the cocoa chain as a socio-ecological exposure system.
5. The rationale for log differences was rewritten around shock transmission and instability, not only generic market econometrics.
6. The weak short-run exchange-rate result is now discussed as a cautious institutional interpretation, not a hard claim.
7. Novelty language was moderated. The paper now presents its contribution as empirical integration and methodological bridging.
8. The contribution paragraph now explicitly links supply-chain transmission with resilience and territorial stress.
9. The conclusion now includes transferability, future extensions, and practical resilience arrangements such as coordination, diversification, early-warning systems, and risk-sharing instruments.

## Internal Review Pass

The final manuscript was revised after a dedicated internal review pass that checked:

- whether the resilience/disaster framing remained visible outside the abstract,
- whether the direct-versus-synthetic hazard logic was honest and transparent,
- whether the time-series claims stayed within the limits of the short sample,
- whether V1 and V2 figures/tables had been preserved, merged, or explicitly relocated,
- whether inconsistent reported values from the earlier V3 attempt were corrected.

One specific correction from that review was the treatment of the PCA overlay: the earlier V3 draft contained inconsistent explained-variance reporting. The final manuscript aligns the text with the saved pipeline summary and treats the PCA series as a robustness layer instead of overpromoting it.

## Remaining Empirical Limitations

- The core return sample still contains only 52 monthly observations.
- The nested disaster return sample still contains only 35 months.
- The Colombian domestic price is a national reference series rather than a farm-gate micro panel.
- The weather block is location-based and contextual, not household-specific.
- The disaster registry supports monthly aggregation and event-window analysis, but not a strong fully dynamic hazard model.
- The paper therefore remains strongest as a transparent resilience-oriented transmission study, not as a definitive causal model of disaster impacts.

## Build Status

- `paper/paper_v3_integrated.tex` compiles successfully to `paper/paper_v3_integrated.pdf`.
- Bibliography was refreshed with `bibtex`.
- Remaining LaTeX warnings are layout-level table wrapping warnings, not build-breaking errors.
