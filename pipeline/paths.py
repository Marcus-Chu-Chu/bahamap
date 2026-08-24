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

# Lowercase substrings that identify the 17 NCR LGUs in filenames/columns.
NCR_CITY_TOKENS = [
    "manila", "quezon", "caloocan", "las pinas", "makati", "malabon",
    "mandaluyong", "marikina", "muntinlupa", "navotas", "paranaque",
    "pasay", "pasig", "pateros", "san juan", "taguig", "valenzuela",
]

RAIN_POINTS = [  # (lat, lon) — Manila/Port Area, QC, Marikina valley, Muntinlupa
    (14.59, 120.97), (14.65, 121.05), (14.65, 121.10), (14.38, 121.05),
]
RAIN_EVENTS = {"Ondoy": "2009-09-26", "Carina (habagat)": "2024-07-24"}

# Column names in source data. Values below are best guesses from source docs;
# Task 3 (inspection) CONFIRMS or corrects them against the real downloads.
BGY_PCODE_COL = "adm4_psgc"
BGY_NAME_COL = "adm4_en"
BGY_CITY_COL = "adm3_en"
CENSUS_PCODE_COL = "admin4Pcode"
CENSUS_POP_COL = "T_TL"
HAZARD_LEVEL_CANDIDATES = ["Var", "VAR", "var", "HAZ", "hazard", "GRIDCODE"]

for _p in (RAW, PROCESSED):
    _p.mkdir(parents=True, exist_ok=True)
