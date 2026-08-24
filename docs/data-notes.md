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
school/hospital/clinic, `out center`; thousands of elements. Spillover beyond
NCR is expected and gets clipped to boundaries in pipeline step 04.

**Rainfall** — Open-Meteo ERA5 archive, 4 NCR points, daily precipitation
1940-01-01..2025-12-31 (31,412 days/point). Transient rate-limit on first
back-to-back fetch; idempotent re-run completed it.
