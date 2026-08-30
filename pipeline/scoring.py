"""Exposure metrics and the composite exposure score."""
import geopandas as gpd
import pandas as pd


def pct_area_in(bgy: gpd.GeoDataFrame, hazard_mh: gpd.GeoDataFrame) -> pd.Series:
    """Share of each barangay's area intersecting the dissolved hazard geometry."""
    hz = hazard_mh.dissolve().geometry.iloc[0]
    inter = bgy.geometry.intersection(hz).area
    pct = (inter / bgy.geometry.area).clip(0, 1)
    pct.index = bgy["pcode"].values
    return pct


def points_in_per_bgy(points: gpd.GeoDataFrame, bgy: gpd.GeoDataFrame) -> pd.Series:
    j = gpd.sjoin(points, bgy[["pcode", "geometry"]], predicate="within")
    counts = j.groupby("pcode").size()
    return counts.reindex(bgy["pcode"].values, fill_value=0)


def count_points_in(points: gpd.GeoDataFrame, hazard_mh: gpd.GeoDataFrame) -> int:
    hz = hazard_mh.dissolve().geometry.iloc[0]
    return int(points.geometry.within(hz).sum())
