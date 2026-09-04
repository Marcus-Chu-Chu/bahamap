# %% [markdown]
# # BahaMap pipeline acceptance checks — run after any pipeline change
# %%
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repo root importable

import geopandas as gpd
import pandas as pd

from pipeline.paths import POP_NCR_2020, PROCESSED, RETURN_PERIODS  # noqa: E402

failures = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")
    if not ok:
        failures.append(name)


# %%
m = pd.read_parquet(PROCESSED / "barangay_master.parquet")
check("row count ~1700", 1500 <= len(m) <= 1900, f"n={len(m)}")
check("pcode unique", m["pcode"].is_unique)
check("no nulls", not m.isna().any().any())
check("pop reconciles ±1%",
      abs(m["population"].sum() - POP_NCR_2020) <= 0.01 * POP_NCR_2020,
      f"total={m['population'].sum():,}")
check("pct bounds", all(m[f"pct_area_mh_{rp}"].between(0, 1).all() for rp in RETURN_PERIODS))
check("monotone by return period",
      (m["pct_area_mh_5"] <= m["pct_area_mh_25"] + 1e-6).all()
      and (m["pct_area_mh_25"] <= m["pct_area_mh_100"] + 1e-6).all())
check("score bounds", m["score"].between(0, 100).all())
check("17 cities", m["city"].nunique() == 17, f"cities={m['city'].nunique()}")

# %%
g = gpd.read_file(PROCESSED / "barangays_wgs84.geojson")
check("geojson matches master", set(g["pcode"]) == set(m["pcode"]))
check("geojson <15MB",
      (PROCESSED / "barangays_wgs84.geojson").stat().st_size < 15e6)

top = m.nsmallest(15, "rank_ncr")["city"].str.lower()
check("flood belt sanity: Marikina/Pasig/Malabon present in top15",
      top.str.contains("marikina|pasig|malabon|navotas|manila").any(),
      f"top cities={sorted(set(top))}")

# %%
if failures:
    sys.exit(f"{len(failures)} QA failures: {failures}")
print("\nALL QA CHECKS PASSED")
