"""Merge per-city NOAH shapefiles into one dissolved Medium+High layer per return period."""
import re
import sys

import geopandas as gpd
import pandas as pd

# Allow running as `python pipeline/02_normalize_hazards.py` from the repo root:
# a script's own folder (pipeline/) lands on sys.path, the repo root does not.
if __package__ in (None, ""):
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline import hazards
from pipeline.paths import PROCESSED, RAW, RETURN_PERIODS


def find_shp_for_rp(rp: int) -> list:
    """Match e.g. *fh5yr*, *_5yr_*, *5year* in any casing; must not match other rps."""
    pat = re.compile(rf"(?<!\d){rp}\s*_?(yr|year)", re.IGNORECASE)
    return [p for p in (RAW / "noah").glob("**/*.shp") if pat.search(p.name.replace("_", ""))
            or pat.search(p.name)]


def main() -> None:
    prev_geom = None  # dissolved M+H of the previous (shorter) return period
    for rp in RETURN_PERIODS:  # ascending order matters for the nesting union
        shps = find_shp_for_rp(rp)
        print(f"{rp}yr: {len(shps)} shapefile(s): {[s.name for s in shps]}")
        if not shps:  # HF mirror ships ONE merged MetroManila_Flood_{rp}year.shp
            raise SystemExit(f"No shapefile matched {rp}yr — "
                             "check data/raw/noah/extracted layout and find_shp_for_rp().")
        parts = []
        for shp in shps:
            g = gpd.read_file(shp)
            parts.append(hazards.normalize(g))
        merged = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), crs=parts[0].crs)
        mh = hazards.dissolve_medhigh(merged)
        if prev_geom is not None:
            # NOAH's merged per-RP layers are not perfectly nested (the 100-yr
            # run locally downgrades some 25-yr Medium/High cells — see
            # docs/data-notes.md). Enforce the physical constraint that a rarer
            # flood covers at least what a more frequent one does.
            mh = gpd.GeoDataFrame(geometry=[mh.geometry.iloc[0].union(prev_geom)],
                                  crs=mh.crs)
        prev_geom = mh.geometry.iloc[0]
        out = PROCESSED / f"hazard_mh_{rp}yr.parquet"
        mh.to_parquet(out)
        print(f"  wrote {out.name}  area_km2={mh.geometry.iloc[0].area / 1e6:,.1f}")


if __name__ == "__main__":
    main()
