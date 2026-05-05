"""Generate the San Vicente de Chucuri context map used in the manuscript.

This script is pipeline-friendly:
- Reproducible default output path under outputs/figures/
- Local geodata caching to avoid repeated downloads
- Optional basemap toggle for offline or restricted environments
- Metadata export for traceable artifact regeneration
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.file_utils import ensure_directory, load_yaml

PATHS = load_yaml(ROOT / "config" / "paths.yaml")


def _load_geo_dependencies():
    """Import geospatial dependencies lazily with actionable errors."""
    try:
        import contextily as ctx
        import geopandas as gpd
        from shapely.geometry import Point
    except ImportError as error:  # pragma: no cover - depends on local environment
        message = (
            "Missing geospatial dependency. Install with: "
            "python -m pip install geopandas contextily shapely pyogrio"
        )
        raise RuntimeError(message) from error
    return gpd, ctx, Point


def _cache_paths(cache_dir: Path) -> dict[str, Path]:
    return {
        "south_america": cache_dir / "south_america_admin0.parquet",
        "colombia_adm1": cache_dir / "colombia_admin1.parquet",
        "colombia_adm2": cache_dir / "colombia_admin2.parquet",
    }


def download_or_load_admin_data(cache_dir: Path, refresh: bool):
    """
    Load administrative boundaries from local cache when possible.
    Falls back to online fetch and refreshes cache files.
    """
    gpd, _, _ = _load_geo_dependencies()
    ensure_directory(cache_dir)
    cache = _cache_paths(cache_dir)

    if not refresh and all(path.exists() for path in cache.values()):
        south_america = gpd.read_parquet(cache["south_america"])
        adm1 = gpd.read_parquet(cache["colombia_adm1"])
        adm2 = gpd.read_parquet(cache["colombia_adm2"])
        return south_america, adm1, adm2, "cache"

    world_url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
    colombia_adm_url = "https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_COL_shp.zip"

    world = gpd.read_file(world_url)
    south_america = world[world["CONTINENT"] == "South America"].copy()
    adm1 = gpd.read_file(colombia_adm_url, layer="gadm41_COL_1")
    adm2 = gpd.read_file(colombia_adm_url, layer="gadm41_COL_2")

    south_america.to_parquet(cache["south_america"], index=False)
    adm1.to_parquet(cache["colombia_adm1"], index=False)
    adm2.to_parquet(cache["colombia_adm2"], index=False)

    return south_america, adm1, adm2, "download"


def add_north_arrow(ax):
    """Add a simple north arrow to the specified axes."""
    x, y, arrow_length = 0.95, 0.95, 0.08
    ax.annotate(
        "N",
        xy=(x, y),
        xytext=(x, y - arrow_length),
        arrowprops={"facecolor": "black", "width": 5, "headwidth": 15},
        ha="center",
        va="center",
        fontsize=15,
        fontweight="bold",
        xycoords=ax.transAxes,
    )


def add_scale_bar(ax, length_km: int = 20):
    """Add a scale bar. Assumes axes are in EPSG:3857 meters."""
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()

    scale_len_m = length_km * 1000
    padding_x = (x_max - x_min) * 0.05
    padding_y = (y_max - y_min) * 0.05

    start_x = x_max - scale_len_m - padding_x
    end_x = x_max - padding_x
    bar_y = y_min + padding_y

    ax.plot([start_x, end_x], [bar_y, bar_y], color="black", linewidth=3)
    ax.plot([start_x, start_x], [bar_y, bar_y + padding_y / 2], color="black", linewidth=2)
    ax.plot([end_x, end_x], [bar_y, bar_y + padding_y / 2], color="black", linewidth=2)
    ax.text(
        (start_x + end_x) / 2,
        bar_y + padding_y / 1.5,
        f"{length_km} km",
        ha="center",
        va="bottom",
        fontsize=12,
        fontweight="bold",
    )


def _find_target_municipality(adm2, municipality_name: str):
    matches = adm2[adm2["NAME_2"].str.contains(municipality_name, case=False, na=False)].copy()
    if matches.empty:
        raise ValueError(f"Municipality not found in admin layer: {municipality_name}")
    return matches


def plot_colombia_maps(
    south_america,
    adm1,
    adm2,
    site_point,
    municipality_name: str,
    department_name: str,
    output_path: Path,
    include_basemap: bool,
):
    """Generate the multi-panel map and save to output_path."""
    gpd, ctx, _ = _load_geo_dependencies()
    plt.rcParams.update(
        {
            "font.family": "serif",
            "axes.facecolor": "#fbfbf8",
            "figure.facecolor": "white",
        }
    )

    fig = plt.figure(figsize=(14, 11))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.5, 1], height_ratios=[1, 1])

    ax_main = fig.add_subplot(gs[:, 0])
    target_muni = _find_target_municipality(adm2, municipality_name)
    target_dept = adm1[adm1["NAME_1"] == department_name].copy()

    if target_dept.empty:
        raise ValueError(f"Department not found in admin layer: {department_name}")

    target_dept_3857 = target_dept.to_crs(epsg=3857)
    target_muni_3857 = target_muni.to_crs(epsg=3857)

    target_dept_3857.plot(ax=ax_main, color="white", edgecolor="gray", alpha=0.3)
    target_muni_3857.plot(ax=ax_main, color="#8B4513", edgecolor="black", alpha=0.6)

    site_gdf = gpd.GeoDataFrame(geometry=[site_point], crs="EPSG:4326").to_crs(epsg=3857)
    site_gdf.plot(
        ax=ax_main,
        marker="*",
        color="gold",
        markersize=300,
        edgecolor="black",
        zorder=10,
        label="Study Site",
    )

    if include_basemap:
        try:
            ctx.add_basemap(ax_main, source=ctx.providers.Esri.WorldPhysical)
        except Exception:
            # Basemap fetch can fail in restricted environments; geometry still renders.
            pass

    add_north_arrow(ax_main)
    add_scale_bar(ax_main, length_km=20)
    ax_main.set_title(
        "Local Context: San Vicente de Chucuri\n(Yariguies Range Terrain)",
        fontsize=16,
        fontweight="bold",
    )
    ax_main.axis("off")

    ax_inset_sa = fig.add_subplot(gs[0, 1])
    south_america.plot(ax=ax_inset_sa, color="#e0e0e0", edgecolor="white")
    south_america[south_america["NAME"] == "Colombia"].plot(ax=ax_inset_sa, color="#3b5998", alpha=0.5)
    gpd.GeoDataFrame(geometry=[site_point], crs="EPSG:4326").plot(
        ax=ax_inset_sa,
        marker="o",
        color="red",
        markersize=25,
    )
    ax_inset_sa.set_title("Location in South America", fontsize=11)
    ax_inset_sa.axis("off")

    ax_inset_dept = fig.add_subplot(gs[1, 1])
    adm1.plot(ax=ax_inset_dept, color="#f0f0f0", edgecolor="gray", linewidth=0.5)
    target_dept.plot(ax=ax_inset_dept, color="#d4a373", edgecolor="black")
    ax_inset_dept.set_title("Santander within Colombia", fontsize=11)
    ax_inset_dept.axis("off")

    ensure_directory(output_path.parent)
    plt.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate manuscript context map for San Vicente de Chucuri.")
    parser.add_argument(
        "--output",
        type=str,
        default=str(ROOT / PATHS["output_figures"] / "fig0_san_vicente_chucuri_map.png"),
        help="Output PNG path.",
    )
    parser.add_argument(
        "--metadata-output",
        type=str,
        default=str(ROOT / PATHS["output_appendix"] / "fig0_san_vicente_chucuri_map_metadata.json"),
        help="Metadata JSON output path.",
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default=str(ROOT / "data" / "raw" / "geospatial_cache"),
        help="Cache directory for downloaded administrative geodata.",
    )
    parser.add_argument(
        "--municipality-name",
        type=str,
        default="San Vicente de Chucuri",
        help="Municipality name to match in NAME_2.",
    )
    parser.add_argument(
        "--department-name",
        type=str,
        default="Santander",
        help="Department name to match in NAME_1.",
    )
    parser.add_argument("--longitude", type=float, default=-73.4111, help="Study-site longitude (EPSG:4326).")
    parser.add_argument("--latitude", type=float, default=6.8833, help="Study-site latitude (EPSG:4326).")
    parser.add_argument("--refresh-cache", action="store_true", help="Force refresh of cached geodata.")
    parser.add_argument(
        "--skip-basemap",
        action="store_true",
        help="Skip remote basemap tile fetch (useful in restricted/offline runs).",
    )
    return parser


def main() -> None:
    parser = _arg_parser()
    args = parser.parse_args()

    _, _, Point = _load_geo_dependencies()
    output_path = Path(args.output)
    metadata_path = Path(args.metadata_output)
    cache_dir = Path(args.cache_dir)
    site_point = Point(args.longitude, args.latitude)

    south_america, adm1, adm2, source_mode = download_or_load_admin_data(
        cache_dir=cache_dir,
        refresh=args.refresh_cache,
    )
    plot_colombia_maps(
        south_america=south_america,
        adm1=adm1,
        adm2=adm2,
        site_point=site_point,
        municipality_name=args.municipality_name,
        department_name=args.department_name,
        output_path=output_path,
        include_basemap=not args.skip_basemap,
    )

    ensure_directory(metadata_path.parent)
    metadata = {
        "script": str(Path(__file__).relative_to(ROOT)),
        "output_figure": str(output_path),
        "cache_dir": str(cache_dir),
        "geometry_source_mode": source_mode,
        "municipality_name": args.municipality_name,
        "department_name": args.department_name,
        "site_coordinates_epsg4326": {"longitude": args.longitude, "latitude": args.latitude},
        "basemap_included": not args.skip_basemap,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
