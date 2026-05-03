# Study-Context Map Figure Pipeline

This repository now includes a dedicated script to generate the manuscript map figure:

- `scripts/14_generate_study_context_map.py`

It produces:

- figure: `outputs/figures/fig0_san_vicente_chucuri_map.png`
- metadata: `outputs/appendix/fig0_san_vicente_chucuri_map_metadata.json`

## Why this is pipeline-safe

The script is organized for reproducible figure updates:

1. Uses fixed default output paths under `outputs/`.
2. Caches administrative geodata under `data/raw/geospatial_cache`.
3. Supports a refresh flag (`--refresh-cache`) when source boundaries must be updated.
4. Supports `--skip-basemap` for offline or restricted environments.
5. Writes machine-readable metadata for traceability.

## Commands

Generate with defaults:

```powershell
python scripts/14_generate_study_context_map.py
```

Force geodata refresh:

```powershell
python scripts/14_generate_study_context_map.py --refresh-cache
```

Offline/restricted run (no tile basemap):

```powershell
python scripts/14_generate_study_context_map.py --skip-basemap
```

## Dependencies

The script requires geospatial extras that are intentionally optional for the rest of the repo:

```powershell
python -m pip install geopandas contextily shapely pyogrio
```

## Integration with manuscript assets

`scripts/12_prepare_latex_bundle.py` already copies all files from `outputs/figures` into `paper/figures`.
After regenerating the map, run the LaTeX bundle step to propagate the updated figure into the manuscript folder.
