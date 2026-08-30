"""NCR filtering and the pcode census join with QA reporting."""
import geopandas as gpd
import pandas as pd

from pipeline.paths import NCR_PCODE_PREFIXES


def _clean(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip()


def filter_ncr(gdf: gpd.GeoDataFrame, pcode_col: str) -> gpd.GeoDataFrame:
    pc = _clean(gdf[pcode_col])
    return gdf[pc.str.startswith(NCR_PCODE_PREFIXES)].copy()


def join_population(bgy: gpd.GeoDataFrame, census: pd.DataFrame,
                    bgy_pcode: str, census_pcode: str, pop_col: str,
                    carry_cols: tuple = ()):
    b = bgy.copy()
    b["_pc"] = _clean(b[bgy_pcode])
    c = census.copy()
    c["_pc"] = _clean(c[census_pcode])
    c["_pop"] = pd.to_numeric(c[pop_col], errors="coerce")
    agg = {"_pop": "sum", **{col: "first" for col in carry_cols}}
    c = c.groupby("_pc", as_index=False).agg(agg)
    joined = b.merge(c, on="_pc", how="left")
    matched = joined["_pop"].notna()
    qa = {
        "n_bgy": len(joined),
        "n_matched": int(matched.sum()),
        "match_rate": round(float(matched.mean()), 4),
        "orphan_bgys": joined.loc[~matched, "_pc"].tolist(),
        "pop_total": int(joined["_pop"].fillna(0).sum()),
    }
    joined["population"] = joined["_pop"].fillna(0).astype(int)
    return joined.drop(columns=["_pc", "_pop"]), qa


def reconcile(pop_total: int, expected: int, tol: float = 0.01) -> bool:
    return abs(pop_total - expected) <= tol * expected
