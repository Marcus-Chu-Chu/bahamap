"""Canonical paths, CRS codes, and project constants. Single source of truth."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

CRS_METRIC = "EPSG:32651"  # UTM 51N — all area math
CRS_WGS = "EPSG:4326"      # all display geometry

RETURN_PERIODS = (5, 25, 100)
HEADLINE_RP = 25
MIN_HAZARD_LEVEL = 2  # 1=Low 2=Medium 3=High; "exposed" = Medium+High
WEIGHTS = {"pop": 0.5, "area": 0.3, "infra": 0.2}

POP_NCR_2020 = 13_484_462  # PSA 2020 census NCR total; join gate = ±1%

# NCR = PSGC region code 13; boundary/census pcodes are "PH" + new 10-digit PSGC.
NCR_PCODE_PREFIXES = ("PH13",)

RAIN_POINTS = [  # (lat, lon) — Manila/Port Area, QC, Marikina valley, Muntinlupa
    (14.59, 120.97), (14.65, 121.05), (14.65, 121.10), (14.38, 121.05),
]
RAIN_EVENTS = {"Ondoy": "2009-09-26", "Carina (habagat)": "2024-07-24"}

# Source file/column identities — CONFIRMED against real downloads 2026-08-24
# (see docs/data-notes.md). The rich boundaries variant carries pop_2020 for
# cross-checking but NO city-name column; city names come via the census join.
BGY_FILE = "BgySubMuns.shp.shp"       # rich variant; sibling PH_Adm4_* is lean
BGY_PCODE_COL = "adm4_pcode"          # e.g. "PH1380100001"
BGY_NAME_COL = "name"                 # clean barangay name
BGY_XCHECK_POP_COL = "pop_2020"       # independent population cross-check
CENSUS_PCODE_COL = "New 10 PCODE"     # PH-prefixed, matches adm4_pcode format
CENSUS_POP_COL = "2020 Census Popn"
CENSUS_CITY_COL = "Mun_City"          # city names ride along in the join
HAZARD_LEVEL_CANDIDATES = ["Var"]     # confirmed: values 1.0/2.0/3.0, EPSG:4326

for _p in (RAW, PROCESSED):
    _p.mkdir(parents=True, exist_ok=True)
