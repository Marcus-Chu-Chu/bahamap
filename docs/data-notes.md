# Data provenance notes

Running record of what each raw source actually is, confirmed against downloaded
files. Update whenever a source surprises us. (Task 3 adds full schema details.)

## Findings from acquisition (2026-08-24)

**Boundaries** — `altcoder/philippines-psgc-shapefiles`, file `PH_Adm4_BgySubMuns.shp.zip`
(382MB) containing TWO shapefile variants: `BgySubMuns.shp.shp` (rich attributes:
`psgc_code`, `name`, `adm4_pcode` "PH##########", `adm3_pcode`, `pop_2015`,
`pop_2020`, `urb_rur`, `shape_sqkm`, …) and `PH_Adm4_BgySubMuns.shp.shp` (lean).
The rich variant's `pop_2020` gives us an independent cross-check against the
census join. CRS per .prj: geographic (see Task 3 confirmation).

**Census** — HDX dataset id `2020-census-total-population-by-barangay_admin4`
("Philippines: Total Population by Barangay"), single resource
`2020 Census Total Popn Brgy_Adm4_New Pcode.xlsx`. Note: the spec's original
assumption (`cod-ps-phl`) was wrong — that dataset only reaches admin level 2
with 2022–2025 projections, no barangay data.

**NOAH hazard maps** — HF mirror `bettergovph/project-noah-hazard-maps` is
organized `Flood/{5yr,25yr,100yr}/<Province>.zip`, ONE merged shapefile per
province per return period (e.g. `MetroManila_Flood_25year.shp`) — NOT per-city.
Metro Manila == NCR covers all 17 LGUs. Gotchas found: inconsistent naming
within the dataset (`Metro Manila.zip` for 100yr vs `MetroManila.zip` for
5/25yr), and `Quezon.zip` means Quezon PROVINCE (Quezon City is inside the
Metro Manila files) — two province zips were downloaded by an early matcher and
deleted 2026-08-24 to keep them out of `**/*.shp` globs. Extracted shapefiles
live under `data/raw/noah/extracted/`.

**OSM facilities** — Overpass bbox (14.30,120.90)–(14.80,121.15), amenities
school/hospital/clinic, `out center`; 3,738 elements (2,669 school / 328
hospital / 741 clinic). Hospital count feels thin for 13.5M people → OSM
coverage is partial; methodology labels these "OSM-mapped facilities" and lists
under-coverage as a limitation. Spillover beyond NCR is expected and gets
clipped to boundaries in pipeline step 04.

## Schema confirmations (Task 3, 2026-08-24)

| Constant | Value | Evidence |
|---|---|---|
| `BGY_FILE` | `BgySubMuns.shp.shp` | rich variant; has `pop_2020` (cross-check), lacks city names |
| `BGY_PCODE_COL` | `adm4_pcode` | format `PH##########` (PH + new 10-digit PSGC) |
| `BGY_NAME_COL` | `name` | clean barangay name (`adm4_en` carries "(Pob.)" suffixes) |
| `CENSUS_PCODE_COL` | `New 10 PCODE` | PH-prefixed — same format as `adm4_pcode`, direct join key |
| `CENSUS_POP_COL` | `2020 Census Popn` | 41,984 rows nationwide |
| `CENSUS_CITY_COL` | `Mun_City` | city names come via the census join (boundaries lack them) |
| `NCR_PCODE_PREFIXES` | `("PH13",)` | NCR = PSGC region 13 |
| NOAH hazard column | `Var` ∈ {1.0, 2.0, 3.0} | all three shapefiles; CRS `EPSG:4326` |

**Rainfall** — Open-Meteo ERA5 archive, 4 NCR points, daily precipitation
1940-01-01..2025-12-31 (31,412 days/point). Transient rate-limit on first
back-to-back fetch; idempotent re-run completed it.

## Census join reconciliation (Task 5, 2026-08-30)

The Task-3 schema confirmation read the head of the boundary file — region 01
rows. NCR rows broke three of its conclusions, caught by the join gate (0/1,712
match on first run):

- **The rich variant is OLD-PSGC vintage.** Its `adm4_pcode`/`psgc_code`
  (e.g. `PH1303901001`) have **zero** overlap with the census's new 10-digit
  codes, and its `name`/`adm4_en` are null for every NCR row. The table below is
  superseded: we now join on the **lean variant** `PH_Adm4_BgySubMuns.shp.shp`,
  whose `adm4_psgc` is the new 10-digit PSGC stored as int64 (leading zero
  stripped outside NCR — restored via `"PH" + zfill(10)`), names in `adm4_en`,
  CRS already EPSG:32651.
- **14 `geo_level="SubMun"` rows dropped** (Manila's sub-municipal aggregates,
  pcodes ending `000`; their component barangays are present individually),
  plus 2 junk rows carrying old codes and null attributes.
- **The 10 EMBO barangays (336,873 residents) straddle vintages**: the 2020
  census codes them under Makati (`PH13803000xx`) while the boundary file uses
  their post-Supreme-Court-transfer Taguig pcodes (`PH13815000xx`). Without a
  fix they fall out of the join — 2.5% of NCR, more than the ±1% gate allows.
  `PCODE_FIXES` in `paths.py` remaps census→boundary code per barangay
  (name-verified one-to-one); their `city` is set to "City of Taguig" (current
  administration; the census sheet still says Makati).
- **Final:** 1,710 barangays, 100.0% match, population total **13,484,462 —
  exactly** the PSA NCR figure. 17 cities (16 + Pateros).

## Return-period nesting fix (Task 7 QA, 2026-08-30)

The QA monotonicity gate caught 653 barangays whose 25-yr Medium/High area share
exceeded their 100-yr share (deltas up to 94pp, 85% of them in the City of
Manila). Diagnosis on the raw layers: the merged 100-yr product (the
oddly-named `Metro Manila.zip`, see acquisition notes) has MORE total and
Medium/High area metro-wide than the 25-yr layer, but locally classifies some
25-yr Medium/High cells as Low — it is a different model run, not perfectly
nested with the 5/25-yr layers. 5-yr vs 25-yr is perfectly nested (0
violations).

Fix in `02_normalize_hazards.py`: each return period's dissolved Medium/High
geometry is unioned with all shorter return periods' (25 := 25∪5,
100 := 100∪25∪5), enforcing the physical definition that a rarer flood covers
at least what a more frequent one does. The 5-yr layer is untouched; the 25-yr
layer is unchanged by construction (already nested); only the 100-yr layer
grows. Documented as a methodology note in the app.
