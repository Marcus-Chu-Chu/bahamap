"""Print the real schemas of every raw source so constants can be confirmed.

Look at raw data BEFORE writing code against it. Run after 01_download completes.
"""
import json
import sys

# Allow running as `python pipeline/inspect_raw.py` from the repo root.
if __package__ in (None, ""):
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import geopandas as gpd
import pandas as pd

from pipeline.paths import RAW


def main() -> None:
    # Boundaries: two variants shipped in one zip — show both.
    for shp in sorted((RAW / "boundaries").glob("*.shp")):
        gdf = gpd.read_file(shp, rows=3)
        print(f"\n== boundaries: {shp.name}  rows(sample)=3  CRS={gdf.crs}")
        print(f"columns: {list(gdf.columns)}")
        print(gdf.drop(columns="geometry").head(3).to_string())

    # Census: PSA xlsx files often carry title rows — show raw, no header guess.
    c = sorted((RAW / "census").glob("census_bgy.*"))[0]
    raw = pd.read_excel(c, header=None, nrows=8) if c.suffix == ".xlsx" \
        else pd.read_csv(c, header=None, nrows=8)
    print(f"\n== census: {c.name} (first 8 rows, no header assumption)")
    print(raw.to_string())

    # NOAH: the three extracted Metro Manila shapefiles.
    for shp in sorted((RAW / "noah" / "extracted").glob("**/*.shp")):
        h = gpd.read_file(shp, rows=3)
        print(f"\n== noah: {shp.name}  CRS={h.crs}")
        print(f"columns: {list(h.columns)}")
        print(h.drop(columns="geometry").head(3).to_string())

    # OSM: element counts by amenity type.
    osm = json.loads((RAW / "osm" / "facilities.json").read_text(encoding="utf-8"))
    kinds: dict = {}
    for el in osm["elements"]:
        k = el.get("tags", {}).get("amenity", "?")
        kinds[k] = kinds.get(k, 0) + 1
    print(f"\n== osm: {len(osm['elements'])} elements by amenity: {kinds}")


if __name__ == "__main__":
    main()
