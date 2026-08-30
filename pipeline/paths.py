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

# Source file/column identities — confirmed 2026-08-24, REVISED 2026-08-30 when
# the census join exposed a vintage mismatch (see docs/data-notes.md): the rich
# variant's pcodes are OLD PSGC (zero overlap with the census's new codes) and
# its NCR names are null, so we join on the LEAN variant instead. Its adm4_psgc
# holds the new 10-digit PSGC as an int (leading zero stripped outside NCR).
BGY_FILE = "PH_Adm4_BgySubMuns.shp.shp"  # lean variant, new-vintage PSGC
BGY_RAW_PSGC_COL = "adm4_psgc"           # int64 new 10-digit PSGC
BGY_PCODE_COL = "pcode_ph"               # constructed: "PH" + zfill(10)
BGY_NAME_COL = "adm4_en"
BGY_LEVEL_COL = "geo_level"              # also holds Manila's 14 "SubMun" aggregates
BGY_LEVEL_KEEP = "Bgy"                   # keep true barangays only
CENSUS_PCODE_COL = "New 10 PCODE"        # PH-prefixed new 10-digit PSGC
CENSUS_POP_COL = "2020 Census Popn"
CENSUS_CITY_COL = "Mun_City"             # city names ride along in the join
HAZARD_LEVEL_CANDIDATES = ["Var"]        # confirmed: values 1.0/2.0/3.0, EPSG:4326

# The 2020 census still codes the 10 EMBO barangays under Makati; the (newer)
# boundary file already uses their post-Supreme-Court-ruling Taguig pcodes.
# Map census pcode -> boundary pcode so the join holds all 336,873 residents.
PCODE_FIXES = {
    "PH1380300003": "PH1381500029",  # Cembo
    "PH1380300004": "PH1381500030",  # Comembo
    "PH1380300007": "PH1381500031",  # East Rembo
    "PH1380300016": "PH1381500032",  # Pembo
    "PH1380300019": "PH1381500033",  # Pitogo
    "PH1380300021": "PH1381500034",  # Post Proper Northside
    "PH1380300022": "PH1381500035",  # Post Proper Southside
    "PH1380300033": "PH1381500036",  # Rizal
    "PH1380300028": "PH1381500037",  # South Cembo
    "PH1380300032": "PH1381500038",  # West Rembo
}
EMBO_CITY = "City of Taguig"  # current administration of the remapped barangays

for _p in (RAW, PROCESSED):
    _p.mkdir(parents=True, exist_ok=True)
