# Standalone Update Log

- Added parser-driven table crosswalk from `final_draft/main.tex` to regenerated CSV/TEX files.
- Added original script and output provenance maps for all manuscript tables and figures.
- Added numeric-token comparison among final LaTeX, original generated outputs, and standalone outputs.
- Added column/window audit documenting input paths, column availability, transformations, imputation handling, and sample filters.
- Updated PCA construction to use the original V2 candidate feature list and orientation, reproducing the October 2022 pressure peak.
- Kept the map as `static_map_copied` because offline geospatial base layers and basemap tiles are not bundled as organized analytical inputs.
- Did not modify `final_draft/main.tex`; manuscript-level inconsistencies are documented rather than silently overwritten.
