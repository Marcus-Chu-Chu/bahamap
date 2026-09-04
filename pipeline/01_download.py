"""Fetch all raw sources. Idempotent: skips files that already exist.

Usage:
  python pipeline/01_download.py            # fetch everything missing
  python pipeline/01_download.py --only osm # one source: boundaries|census|noah|osm|rain
  python pipeline/01_download.py --verify   # check presence only, exit 1 if incomplete
"""
import argparse
import json
import sys
import time

import requests

# Allow running as `python pipeline/01_download.py` from the repo root:
# a script's own folder (pipeline/) lands on sys.path, the repo root does not.
if __package__ in (None, ""):
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.paths import RAIN_POINTS, RAW
from pipeline.sources import is_mm_flood

UA = {"User-Agent": "BahaMap/0.1 (student project; gilmlachu@gmail.com)"}


def _manual(msg: str) -> None:
    print(f"\n[MANUAL STEP NEEDED]\n{msg}\n", file=sys.stderr)


# ---------------- boundaries (altcoder PSGC shapefiles via GitHub tree API) --
def fetch_boundaries() -> bool:
    out = RAW / "boundaries"
    if any(out.glob("**/*.shp")) or any(out.glob("**/*.geojson")):
        return True
    out.mkdir(parents=True, exist_ok=True)
    try:
        tree = requests.get(
            "https://api.github.com/repos/altcoder/philippines-psgc-shapefiles/git/trees/main?recursive=1",
            headers=UA, timeout=60).json()["tree"]
        cands = [t["path"] for t in tree
                 if "adm4" in t["path"].lower() and t["path"].lower().endswith((".zip", ".geojson"))]
        if not cands:
            raise RuntimeError("no Adm4 file found in repo tree")
        pick = sorted(cands, key=len)[0]
        print(f"boundaries: downloading {pick}")
        url = f"https://github.com/altcoder/philippines-psgc-shapefiles/raw/main/{pick}"
        blob = requests.get(url, headers=UA, timeout=600)
        blob.raise_for_status()
        dest = out / pick.split("/")[-1]
        dest.write_bytes(blob.content)
        if dest.suffix == ".zip":
            import zipfile
            zipfile.ZipFile(dest).extractall(out)
        return True
    except Exception as e:  # noqa: BLE001 — any failure routes to manual path
        _manual(
            f"Automated boundary download failed ({e}).\n"
            "1. Open https://github.com/altcoder/philippines-psgc-shapefiles\n"
            "2. Download the *Adm4 / Barangay* level zip (dist folder or release assets)\n"
            f"3. Extract into {out}\\ so a .shp (or .geojson) is somewhere under it.\n"
            "Alternative: HDX 'cod-ab-phl' ADM4 layer.")
        return False


# ---------------- census (HDX CKAN API, dataset cod-ps-phl) ------------------
def fetch_census() -> bool:
    out = RAW / "census"
    if any(out.glob("*.csv")) or any(out.glob("*.xlsx")):
        return True
    out.mkdir(parents=True, exist_ok=True)
    try:
        # Dataset id verified 2026-08-24: PSA 2020 Census total population per
        # barangay with 10-digit "new" PSGC pcodes (cod-ps-phl only reaches adm2).
        pkg = requests.get(
            "https://data.humdata.org/api/3/action/package_show"
            "?id=2020-census-total-population-by-barangay_admin4",
            headers=UA, timeout=60).json()["result"]
        res = [r for r in pkg["resources"]
               if r.get("format", "").lower() in ("csv", "xlsx")]
        if not res:
            raise RuntimeError("no csv/xlsx resource in census dataset")
        r = res[0]
        print(f"census: downloading {r['name']}")
        blob = requests.get(r["url"], headers=UA, timeout=600)
        blob.raise_for_status()
        ext = ".xlsx" if "xlsx" in r.get("format", "").lower() else ".csv"
        (out / f"census_bgy{ext}").write_bytes(blob.content)
        return True
    except Exception as e:  # noqa: BLE001
        _manual(
            f"Automated census download failed ({e}).\n"
            "1. Open https://data.humdata.org/dataset/cod-ps-phl\n"
            "2. Download the admin-level-4 (barangay) population file\n"
            f"3. Save it as {out}\\census_bgy.csv (or .xlsx)")
        return False


# ---------------- NOAH hazard maps (HF dataset mirror) -----------------------
def fetch_noah() -> bool:
    out = RAW / "noah"
    if any(out.glob("**/*.shp")):
        return True
    out.mkdir(parents=True, exist_ok=True)
    try:
        import zipfile

        from huggingface_hub import HfApi, hf_hub_download
        api = HfApi()
        files = api.list_repo_files("bettergovph/project-noah-hazard-maps",
                                    repo_type="dataset")
        picks = [f for f in files if is_mm_flood(f)]
        print(f"noah: matched {len(picks)} files: {picks}")
        if len(picks) < 3:  # expect one Metro Manila zip per return period
            raise RuntimeError(f"expected 3 Metro Manila flood zips, got {picks}")
        for f in picks:
            local = hf_hub_download("bettergovph/project-noah-hazard-maps", f,
                                    repo_type="dataset", local_dir=out)
            zipfile.ZipFile(local).extractall(RAW / "noah" / "extracted")
            print(f"noah: extracted {f}")
        return True
    except Exception as e:  # noqa: BLE001
        _manual(
            f"Automated NOAH download failed ({e}).\n"
            "1. Open https://huggingface.co/datasets/bettergovph/project-noah-hazard-maps\n"
            "   (or per-city layers at https://lipad-fmc.dream.upd.edu.ph)\n"
            "2. Download 5yr/25yr/100yr flood hazard shapefiles for all 17 NCR LGUs\n"
            f"3. Extract under {out}\\ (any folder layout; *.shp must be findable)")
        return False


# ---------------- OSM facilities (Overpass, NCR bounding box) ----------------
def fetch_osm() -> bool:
    dest = RAW / "osm" / "facilities.json"
    if dest.exists():
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    query = """
[out:json][timeout:180];
(
  nwr["amenity"="school"](14.30,120.90,14.80,121.15);
  nwr["amenity"="hospital"](14.30,120.90,14.80,121.15);
  nwr["amenity"="clinic"](14.30,120.90,14.80,121.15);
);
out center;
"""
    try:
        r = requests.post("https://overpass-api.de/api/interpreter",
                          data={"data": query}, headers=UA, timeout=300)
        r.raise_for_status()
        data = r.json()
        if len(data.get("elements", [])) < 500:
            raise RuntimeError(f"suspiciously few elements: {len(data.get('elements', []))}")
        dest.write_text(json.dumps(data), encoding="utf-8")
        print(f"osm: {len(data['elements'])} elements")
        return True
    except Exception as e:  # noqa: BLE001
        _manual(f"Overpass failed ({e}). Retry later or use mirror "
                "https://overpass.kumi.systems/api/interpreter (edit URL above).")
        return False


# ---------------- rainfall (Open-Meteo ERA5 archive) -------------------------
def fetch_rain() -> bool:
    out = RAW / "rain"
    out.mkdir(parents=True, exist_ok=True)
    ok = True
    for i, (lat, lon) in enumerate(RAIN_POINTS):
        dest = out / f"point_{i}.json"
        if dest.exists():
            continue
        url = ("https://archive-api.open-meteo.com/v1/archive"
               f"?latitude={lat}&longitude={lon}"
               "&start_date=1940-01-01&end_date=2025-12-31"
               "&daily=precipitation_sum&timezone=Asia%2FManila")
        try:
            r = requests.get(url, headers=UA, timeout=300)
            r.raise_for_status()
            body = r.json()
            assert "daily" in body and len(body["daily"]["time"]) > 30000
            dest.write_text(json.dumps(body), encoding="utf-8")
            print(f"rain: point {i} ok ({len(body['daily']['time'])} days)")
            time.sleep(2)
        except Exception as e:  # noqa: BLE001
            _manual(f"Open-Meteo failed for point {i} ({e}). Re-run this script.")
            ok = False
    return ok


SOURCES = {"boundaries": fetch_boundaries, "census": fetch_census,
           "noah": fetch_noah, "osm": fetch_osm, "rain": fetch_rain}


def verify() -> dict:
    return {
        "boundaries": any((RAW / "boundaries").glob("**/*.shp"))
                      or any((RAW / "boundaries").glob("**/*.geojson")),
        "census": any((RAW / "census").glob("census_bgy.*")),
        "noah": any((RAW / "noah").glob("**/*.shp")),
        "osm": (RAW / "osm" / "facilities.json").exists(),
        "rain": all((RAW / "rain" / f"point_{i}.json").exists()
                    for i in range(len(RAIN_POINTS))),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=SOURCES)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if args.verify:
        status = verify()
        for k, v in status.items():
            print(f"{'OK  ' if v else 'MISS'} {k}")
        sys.exit(0 if all(status.values()) else 1)
    targets = {args.only: SOURCES[args.only]} if args.only else SOURCES
    results = {name: fn() for name, fn in targets.items()}
    print("\nsummary:", results)
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
