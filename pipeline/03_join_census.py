"""Produce barangay_base.parquet: NCR barangays with population, metric CRS."""
import sys

import geopandas as gpd
import pandas as pd

# Allow running as `python pipeline/03_join_census.py` from the repo root:
# a script's own folder (pipeline/) lands on sys.path, the repo root does not.
if __package__ in (None, ""):
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline import joins
from pipeline.paths import (
    BGY_FILE,
    BGY_LEVEL_COL,
    BGY_LEVEL_KEEP,
    BGY_NAME_COL,
    BGY_PCODE_COL,
    BGY_RAW_PSGC_COL,
    CENSUS_CITY_COL,
    CENSUS_PCODE_COL,
    CENSUS_POP_COL,
    CRS_METRIC,
    EMBO_CITY,
    PCODE_FIXES,
    POP_NCR_2020,
    PROCESSED,
    RAW,
)


def main() -> None:
    src = RAW / "boundaries" / BGY_FILE
    bgy = gpd.read_file(src)
    bgy[BGY_PCODE_COL] = "PH" + bgy[BGY_RAW_PSGC_COL].astype(str).str.zfill(10)
    bgy = bgy[bgy[BGY_LEVEL_COL] == BGY_LEVEL_KEEP]  # drop SubMun aggregates
    bgy = joins.filter_ncr(bgy, BGY_PCODE_COL).to_crs(CRS_METRIC)
    print(f"NCR barangays: {len(bgy)} (expect roughly 1700)")

    csrc = sorted((RAW / "census").glob("census_bgy.*"))[0]
    census = (pd.read_csv(csrc, dtype=str) if csrc.suffix == ".csv"
              else pd.read_excel(csrc, dtype=str))
    # Census still uses pre-transfer pcodes for the EMBO barangays; remap to the
    # boundary file's vintage before joining.
    census[CENSUS_PCODE_COL] = (census[CENSUS_PCODE_COL].astype(str).str.strip()
                                .replace(PCODE_FIXES))
    joined, qa = joins.join_population(bgy, census, BGY_PCODE_COL,
                                       CENSUS_PCODE_COL, CENSUS_POP_COL,
                                       carry_cols=(CENSUS_CITY_COL,))
    print(f"QA: matched {qa['n_matched']}/{qa['n_bgy']} ({qa['match_rate']:.1%}); "
          f"pop_total={qa['pop_total']:,}")
    if qa["orphan_bgys"]:
        print(f"orphans ({len(qa['orphan_bgys'])}): {qa['orphan_bgys'][:20]}")
    if not joins.reconcile(qa["pop_total"], POP_NCR_2020):
        sys.exit(f"FAIL: population {qa['pop_total']:,} not within 1% of {POP_NCR_2020:,}. "
                 "Fix orphans/columns before proceeding.")

    out = joined.rename(columns={BGY_PCODE_COL: "pcode", BGY_NAME_COL: "name",
                                 CENSUS_CITY_COL: "city"})
    out = out[["pcode", "name", "city", "population", "geometry"]]
    out["pcode"] = out["pcode"].astype(str).str.strip()
    # The remapped EMBO barangays are administered by Taguig today, whatever the
    # 2020 census sheet says.
    out.loc[out["pcode"].isin(PCODE_FIXES.values()), "city"] = EMBO_CITY
    out.to_parquet(PROCESSED / "barangay_base.parquet")
    print(f"wrote barangay_base.parquet  rows={len(out)}  cities={out['city'].nunique()}")


if __name__ == "__main__":
    main()
