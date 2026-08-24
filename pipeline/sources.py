"""Pure selection rules for external data sources (importable, unit-tested).

The NOAH HF mirror organizes files as Hazard/ReturnPeriod/Province.zip with
inconsistent province spellings ("MetroManila.zip", "Metro Manila.zip"), and
"Quezon.zip" there means Quezon PROVINCE — not Quezon City, which lives inside
the Metro Manila files. NCR == Metro Manila, so we take only those.
"""


def is_mm_flood(path: str) -> bool:
    p = path.lower().replace("_", "").replace("-", "").replace(" ", "")
    return "flood" in p and "metromanila" in p
