"""Build the master table, simplified GeoJSON, facilities file, sensitivity CSV."""
import json
import sys

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# Allow running as `python pipeline/04_overlay_exposure.py` from the repo root:
# a script's own folder (pipeline/) lands on sys.path, the repo root does not.
if __package__ in (None, ""):
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline import scoring
from pipeline.paths import CRS_METRIC, CRS_WGS, HEADLINE_RP, PROCESSED, RAW, RETURN_PERIODS, WEIGHTS

GEOJSON_LIMIT_MB = 15
SIMPLIFY_START_M = 10


def load_facilities() -> gpd.GeoDataFrame:
    raw = json.loads((RAW / "osm" / "facilities.json").read_text(encoding="utf-8"))
    rows = []
    for el in raw["elements"]:
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        tags = el.get("tags", {})
        if lat is None or "amenity" not in tags:
            continue
        kind = "school" if tags["amenity"] == "school" else "health"
        rows.append({"kind": kind, "name": tags.get("name", "(unnamed)"),
                     "geometry": Point(lon, lat)})
    return gpd.GeoDataFrame(rows, crs=CRS_WGS).to_crs(CRS_METRIC)


def write_geojson(bgy: gpd.GeoDataFrame) -> None:
    tol = SIMPLIFY_START_M
    while True:
        g = bgy[["pcode", "name", "city", "geometry"]].copy()
        g["geometry"] = g.geometry.simplify(tol, preserve_topology=True)
        g = g.to_crs(CRS_WGS)
        out = PROCESSED / "barangays_wgs84.geojson"
        g.to_file(out, driver="GeoJSON")
        mb = out.stat().st_size / 1e6
        print(f"geojson tol={tol}m -> {mb:.1f}MB")
        if mb < GEOJSON_LIMIT_MB:
            return
        tol *= 2


def main() -> None:
    bgy = gpd.read_parquet(PROCESSED / "barangay_base.parquet")
    fac = load_facilities()
    fac = gpd.sjoin(fac, bgy[["geometry"]], predicate="within").drop(columns="index_right")
    fac.to_parquet(PROCESSED / "facilities.parquet")
    print(f"facilities inside NCR: {len(fac)} "
          f"({(fac['kind'] == 'school').sum()} schools, {(fac['kind'] == 'health').sum()} health)")

    df = bgy[["pcode", "name", "city", "population"]].copy()
    for rp in RETURN_PERIODS:
        hz = gpd.read_parquet(PROCESSED / f"hazard_mh_{rp}yr.parquet")
        df[f"pct_area_mh_{rp}"] = scoring.pct_area_in(bgy, hz).values

    df["est_pop_exposed_25"] = (df["population"] * df[f"pct_area_mh_{HEADLINE_RP}"]).round().astype(int)

    hz25 = gpd.read_parquet(PROCESSED / f"hazard_mh_{HEADLINE_RP}yr.parquet")
    for kind, col in (("school", "schools"), ("health", "health")):
        pts = fac[fac["kind"] == kind]
        df[f"{col}_total"] = scoring.points_in_per_bgy(pts, bgy).values
        exposed = pts[pts.geometry.within(hz25.dissolve().geometry.iloc[0])]
        df[f"{col}_exposed"] = scoring.points_in_per_bgy(exposed, bgy).values
    df["infra_exposed"] = df["schools_exposed"] + df["health_exposed"]

    sc = pd.DataFrame({"est_pop_exposed": df["est_pop_exposed_25"],
                       "pct_area_mh": df[f"pct_area_mh_{HEADLINE_RP}"],
                       "infra_exposed": df["infra_exposed"]})
    df["pop_norm"] = scoring.minmax(sc["est_pop_exposed"]).round(4)
    df["area_norm"] = scoring.minmax(sc["pct_area_mh"]).round(4)
    df["infra_norm"] = scoring.minmax(sc["infra_exposed"]).round(4)
    df["score"] = scoring.exposure_score(sc, WEIGHTS)
    df["rank_ncr"] = df["score"].rank(ascending=False, method="min").astype(int)

    scoring.sensitivity(sc, WEIGHTS).to_csv(PROCESSED / "sensitivity.csv", index=False)
    df.to_parquet(PROCESSED / "barangay_master.parquet", index=False)
    print(f"master rows={len(df)}; top5:\n"
          f"{df.nsmallest(5, 'rank_ncr')[['name', 'city', 'score', 'est_pop_exposed_25']]}")
    write_geojson(bgy)


if __name__ == "__main__":
    main()
