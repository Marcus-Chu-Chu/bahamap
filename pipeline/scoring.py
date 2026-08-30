"""Exposure metrics and the composite exposure score."""
import geopandas as gpd
import pandas as pd
from scipy.stats import spearmanr


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


def minmax(s: pd.Series) -> pd.Series:
    rng = s.max() - s.min()
    if rng == 0:
        return pd.Series(0.0, index=s.index)
    return (s - s.min()) / rng


def exposure_score(df: pd.DataFrame, weights: dict) -> pd.Series:
    score = (weights["pop"] * minmax(df["est_pop_exposed"])
             + weights["area"] * minmax(df["pct_area_mh"])
             + weights["infra"] * minmax(df["infra_exposed"]))
    return (100 * minmax(score)).round(1)


def sensitivity(df: pd.DataFrame, weights: dict, delta: float = 0.10) -> pd.DataFrame:
    base = exposure_score(df, weights).rank()
    rows = []
    for key in weights:
        for sign in (+1, -1):
            w = dict(weights)
            w[key] = max(0.0, w[key] + sign * delta)
            others = [k for k in w if k != key]
            rest = 1.0 - w[key]
            tot = sum(weights[k] for k in others)
            for k in others:
                w[k] = rest * weights[k] / tot
            corr = spearmanr(base, exposure_score(df, w).rank()).statistic
            rows.append({"shift": f"{key}{'+' if sign > 0 else '-'}{int(delta*100)}pp",
                         "spearman_rank_corr": round(float(corr), 4)})
    return pd.DataFrame(rows)
