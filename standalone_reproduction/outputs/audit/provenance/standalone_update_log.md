# Standalone Update Log

- Added parser-driven table crosswalk from `final_draft/main.tex` to regenerated CSV/TEX files.
- Added original script and output provenance maps for all manuscript tables and figures.
- Replaced token-order table comparison with semantic row/column matching and kept token matching only as a warning fallback.
- Added column/window audit documenting input paths, column availability, transformations, imputation handling, and sample filters.
- Reproduced vulnerability indicators with original additive helper logic (`compute_farmer_exposure_index` and `build_livelihood_risk_score`).
- Reconstructed the ten-row publication weather-extended model table from original regression logic and volatility-source handling.
- Rebuilt the supplementary disaster Granger table directly from `reports/v2/tables/table_disaster_causality.csv`.
- Updated PCA construction to use the original V2 candidate feature list and orientation, reproducing the October 2022 pressure peak.
- Kept the map as `static_map_copied` because offline geospatial base layers and basemap tiles are not bundled as organized analytical inputs.
- Did not modify `final_draft/main.tex`; manuscript-level inconsistencies are documented rather than silently overwritten.
