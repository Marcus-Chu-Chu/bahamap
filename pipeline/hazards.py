"""Normalize NOAH flood hazard shapefiles into a uniform schema."""
import geopandas as gpd
from shapely import make_valid

from pipeline.paths import CRS_METRIC, HAZARD_LEVEL_CANDIDATES, MIN_HAZARD_LEVEL


def detect_level_col(gdf: gpd.GeoDataFrame) -> str:
    for cand in HAZARD_LEVEL_CANDIDATES:
        if cand in gdf.columns:
            return cand
    raise ValueError(
        f"No known hazard-level column. Columns present: {list(gdf.columns)}. "
        "Add the real name to HAZARD_LEVEL_CANDIDATES after inspecting the file.")


def normalize(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    col = detect_level_col(gdf)
    out = gdf[[col, "geometry"]].rename(columns={col: "level"})
    out["level"] = out["level"].round().astype(int)
    bad = ~out["level"].isin([1, 2, 3])
    if bad.any():
        raise ValueError(f"Unexpected hazard levels: {sorted(out.loc[bad, 'level'].unique())}")
    out = out.to_crs(CRS_METRIC) if out.crs else out.set_crs(CRS_METRIC)
    invalid = ~out.geometry.is_valid
    if invalid.any():
        out.loc[invalid, "geometry"] = out.loc[invalid, "geometry"].apply(make_valid)
    return out


def dissolve_medhigh(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    mh = gdf[gdf["level"] >= MIN_HAZARD_LEVEL]
    return mh.dissolve()[["geometry"]].reset_index(drop=True)
