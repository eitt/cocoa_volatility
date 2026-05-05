# Reproduction Audit

## A. Executive Summary

- Date/time of run: 2026-05-04T19:24:32
- Python version: 3.12.3
- Main input datasets used: data\processed\analysis_ready\merged_cocoa_price_panel.csv, data\processed\final_series\core_common_window_panel_imputed.csv, data\processed\final_series\all_series_common_window_panel_imputed.csv, reports\v2\intermediate\03_classified_events.csv, reports\v2\intermediate\04_monthly_event_panel.csv
- Number of figures expected: 12
- Number of figures generated: 12
- Number of tables expected: 13
- Number of tables generated: 13
- Figure comparison counts: {"copied_static": 1, "regenerated_minor_difference": 11}
- Table comparison counts: {"recomputed_major_difference": 3, "recomputed_match": 3, "recomputed_minor_difference": 5, "static_from_draft": 2}

## B. Input Data Inventory

| Dataset path                                                           | File type   |   Rows |   Columns | Date range         | Key columns detected                                                                                                                                                                                                                                                                                            | Assumptions made                                                     |
|:-----------------------------------------------------------------------|:------------|-------:|----------:|:-------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------------------------------------------------------------------|
| data\processed\analysis_ready\merged_cocoa_price_panel.csv             | .csv        |    795 |        18 | 1960-01 to 2026-03 | colombia_cocoa_price_cop_kg, world_cocoa_price_usd_mt, eu_hicp_chocolate_index, cop_usd_exchange_rate, brent_oil_usd_bbl, nasa_precipitation_mm_day, nasa_temperature_c, nasa_temperature_max_c, nasa_temperature_min_c, nasa_relative_humidity_pct, nasa_wind_speed_ms, nasa_surface_solar_radiation_mj_m2_day | Selected as organized reproduction input; not a figure/table output. |
| data\processed\final_series\core_common_window_panel_imputed.csv       | .csv        |     53 |        11 | 2021-08 to 2025-12 | colombia_cocoa_price_cop_kg, world_cocoa_price_usd_mt, eu_hicp_chocolate_index, cop_usd_exchange_rate, brent_oil_usd_bbl                                                                                                                                                                                        | Selected as organized reproduction input; not a figure/table output. |
| data\processed\final_series\all_series_common_window_panel_imputed.csv | .csv        |     53 |        25 | 2021-08 to 2025-12 | colombia_cocoa_price_cop_kg, world_cocoa_price_usd_mt, eu_hicp_chocolate_index, cop_usd_exchange_rate, brent_oil_usd_bbl, nasa_precipitation_mm_day, nasa_temperature_c, nasa_temperature_max_c, nasa_temperature_min_c, nasa_relative_humidity_pct, nasa_wind_speed_ms, nasa_surface_solar_radiation_mj_m2_day | Selected as organized reproduction input; not a figure/table output. |
| reports\v2\intermediate\03_classified_events.csv                       | .csv        |    594 |        78 | 2021-08 to 2024-07 | hazard_domain_en                                                                                                                                                                                                                                                                                                | Selected as organized reproduction input; not a figure/table output. |
| reports\v2\intermediate\04_monthly_event_panel.csv                     | .csv        |     36 |        23 | 2021-08 to 2024-07 | total_events, hydrometeorological_events                                                                                                                                                                                                                                                                        | Selected as organized reproduction input; not a figure/table output. |

## C. Figure Reproduction Table

| Expected figure filename                             | Generated?   | Source type           | Comparison status            | Notes                                                                                                                                                                       |
|:-----------------------------------------------------|:-------------|:----------------------|:-----------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| fig0_san_vicente_chucuri_map.png                     | Yes          | copied static         | copied_static                | Static map copied because local geospatial base layers are not bundled for offline regeneration.                                                                            |
| figure_v1_long_run_coverage.png                      | Yes          | regenerated from data | regenerated_minor_difference | generated_pixels=2971x1405; reference_pixels=3435x1560; generated_file_size=210482; reference_file_size=88770; rms_difference=; pixel_dimension_delta=0.13508005822416302   |
| figure_indexed_core_series_common_window_imputed.png | Yes          | regenerated from data | regenerated_minor_difference | generated_pixels=2967x1468; reference_pixels=2959x1466; generated_file_size=297080; reference_file_size=313693; rms_difference=; pixel_dimension_delta=0.002696326255476913 |
| figure_weather_vulnerability_index.png               | Yes          | regenerated from data | regenerated_minor_difference | generated_pixels=2967x1468; reference_pixels=2957x1466; generated_file_size=422208; reference_file_size=372316; rms_difference=; pixel_dimension_delta=0.003370407819346141 |
| figure_monthly_event_totals.png                      | Yes          | regenerated from data | regenerated_minor_difference | generated_pixels=2967x1408; reference_pixels=2500x1337; generated_file_size=185781; reference_file_size=149597; rms_difference=; pixel_dimension_delta=0.15739804516346478  |
| figure_hazard_domain_mix.png                         | Yes          | regenerated from data | regenerated_minor_difference | generated_pixels=2967x1408; reference_pixels=2500x1429; generated_file_size=131673; reference_file_size=220027; rms_difference=; pixel_dimension_delta=0.15739804516346478  |
| figure_contextual_overlay_alignment.png              | Yes          | regenerated from data | regenerated_minor_difference | generated_pixels=2970x2365; reference_pixels=3270x2661; generated_file_size=360623; reference_file_size=447193; rms_difference=; pixel_dimension_delta=0.11123637730176625  |
| figure_pca_loadings.png                              | Yes          | regenerated from data | regenerated_minor_difference | generated_pixels=2372x1614; reference_pixels=3124x1499; generated_file_size=241644; reference_file_size=226597; rms_difference=; pixel_dimension_delta=0.2407170294494238   |
| pca_indicator_change_points.png                      | Yes          | regenerated from data | regenerated_minor_difference | generated_pixels=2964x1468; reference_pixels=2537x1338; generated_file_size=287896; reference_file_size=169008; rms_difference=; pixel_dimension_delta=0.1440620782726046   |
| figure_climate_series_panels_common_window.png       | Yes          | regenerated from data | regenerated_minor_difference | generated_pixels=3570x5845; reference_pixels=3560x5777; generated_file_size=933751; reference_file_size=934277; rms_difference=; pixel_dimension_delta=0.011633875106928999 |
| figure_v3_actual_vs_fitted.png                       | Yes          | regenerated from data | regenerated_minor_difference | generated_pixels=2967x1408; reference_pixels=2536x1328; generated_file_size=210567; reference_file_size=173533; rms_difference=; pixel_dimension_delta=0.14526457701381867  |
| figure_top_municipalities.png                        | Yes          | regenerated from data | regenerated_minor_difference | generated_pixels=2370x1464; reference_pixels=2556x1498; generated_file_size=118799; reference_file_size=101708; rms_difference=; pixel_dimension_delta=0.07276995305164319  |

## D. Table Reproduction Table

| Table label                  | Generated?   | Source type     | Comparison status           | Notes                                                                                        |
|:-----------------------------|:-------------|:----------------|:----------------------------|:---------------------------------------------------------------------------------------------|
| tab_data_card                | Yes          | static metadata | static_from_draft           | Metadata-style table encoded from manuscript and data inventory, not a statistical estimate. |
| tab_sample_design            | Yes          | static metadata | static_from_draft           | Metadata-style table encoded from manuscript and data inventory, not a statistical estimate. |
| tab_descriptive_stats        | Yes          | recomputed      | recomputed_minor_difference | Matched 20 of 55 draft numeric tokens within tolerance.                                      |
| tab_stats_overview           | Yes          | recomputed      | recomputed_minor_difference | Matched 21 of 44 draft numeric tokens within tolerance.                                      |
| tab_transmission_results     | Yes          | recomputed      | recomputed_minor_difference | Matched 15 of 25 draft numeric tokens within tolerance.                                      |
| tab_structural_breaks        | Yes          | recomputed      | recomputed_match            | Matched 11 of 12 draft numeric tokens within tolerance.                                      |
| tab_vulnerability_indicators | Yes          | recomputed      | recomputed_major_difference | Matched 2 of 10 draft numeric tokens within tolerance.                                       |
| tab_weather_extended_models  | Yes          | recomputed      | recomputed_major_difference | Matched 13 of 46 draft numeric tokens within tolerance.                                      |
| tab_hazard_screening         | Yes          | recomputed      | recomputed_minor_difference | Matched 27 of 43 draft numeric tokens within tolerance.                                      |
| tab_hazard_models            | Yes          | recomputed      | recomputed_minor_difference | Matched 15 of 27 draft numeric tokens within tolerance.                                      |
| tab_mean_shifts              | Yes          | recomputed      | recomputed_match            | Matched 8 of 9 draft numeric tokens within tolerance.                                        |
| tab_supp_granger             | Yes          | recomputed      | recomputed_match            | Matched 33 of 34 draft numeric tokens within tolerance.                                      |
| tab_supp_disaster_granger    | Yes          | recomputed      | recomputed_major_difference | Matched 3 of 22 draft numeric tokens within tolerance.                                       |

## E. Statistical Validation Notes

- Main Colombian-return benchmark coefficient: 0.796 (p=<0.001).
- Weather-extended models are reproduced as contextual additions; weather table reports 3 model rows and does not replace the benchmark channel.
- Structural-break diagnostic decision: Retained by BIC; best candidate row is diagnostic if present.
- Hydrometeorological counts are retained as the preferred direct hazard marker with 31 nonzero months.
- Peak contextual-pressure month from reproduced PCA scores: 2022-10.

## F. Warnings and Limitations

- The map figure was copied as a static artifact because offline geospatial base layers are not bundled in the reproduction inputs.
- Metadata tables were encoded as manuscript/data-inventory tables rather than recomputed statistical estimates.
- At least one table has a major difference or is missing; inspect `outputs/audit/table_comparison.csv`.

## Table Crosswalk

- Crosswalk file: `outputs\audit\table_crosswalk.md`
- Matched manuscript tables with both CSV and TEX: 13
- Missing table files: 0
- Extra generated table file groups: 0
- Extra generated table files: 0
- Ambiguous matches: 0
- No ambiguous table matches were detected.

## Provenance Audit

- Provenance folder: `outputs\audit\provenance`
- Tables audited: 13
- Figures audited: 12
- Column/window blocks audited: 8
- Non-exact numeric value comparisons: 1513
- Items requiring author/code review or decision: 9
- See `figure_provenance_map.md`, `table_provenance_map.md`, `latex_vs_generated_values.md`, `column_and_window_audit.md`, `discrepancy_diagnosis.md`, and `standalone_update_log.md`.
