"""Brief payload construction, numeric grounding validation, template fallback."""
import re

RP_LABELS = {5.0, 25.0, 100.0}


def build_payload(row: dict, n_bgys: int) -> dict:
    return {
        "pcode": row["pcode"], "name": row["name"], "city": row["city"],
        "population": int(row["population"]),
        "rank_ncr": int(row["rank_ncr"]), "n_bgys_ncr": int(n_bgys),
        "pct_area_5yr": round(100 * row["pct_area_mh_5"]),
        "pct_area_25yr": round(100 * row["pct_area_mh_25"]),
        "pct_area_100yr": round(100 * row["pct_area_mh_100"]),
        "est_pop_exposed": int(row["est_pop_exposed_25"]),
        "schools_exposed": int(row["schools_exposed"]),
        "health_exposed": int(row["health_exposed"]),
    }


def extract_numbers(text: str) -> list[float]:
    out = []
    for tok in re.findall(r"\d[\d,]*\.?\d*", text):
        val = float(tok.replace(",", ""))
        if val < 10 or val in RP_LABELS:
            continue
        if 1900 <= val <= 2100 and val == int(val) and "." not in tok and "," not in tok:
            continue  # year
        out.append(val)
    return out


def validate(text: str, payload: dict) -> list[float]:
    allowed = {float(v) for v in payload.values() if isinstance(v, (int, float))}
    for v in payload.values():  # e.g. Manila's "Barangay 693" — its own name
        if isinstance(v, str):
            allowed.update(extract_numbers(v))
    return [n for n in extract_numbers(text)
            if not any(abs(n - a) <= 0.5 for a in allowed)]


def template_brief(p: dict) -> dict:
    en = (f"{p['name']}, {p['city']} ranks #{p['rank_ncr']} of {p['n_bgys_ncr']} "
          f"Metro Manila barangays for flood exposure. About {p['pct_area_25yr']}% of "
          f"its land lies in the 25-year Medium/High flood zone, where an estimated "
          f"{p['est_pop_exposed']} of its {p['population']} residents live. "
          f"Know your barangay's evacuation plan, keep documents in waterproof "
          f"storage, and monitor official PAGASA advisories during heavy rain.")
    tl = (f"Ang {p['name']}, {p['city']} ay pang-{p['rank_ncr']} sa {p['n_bgys_ncr']} "
          f"na barangay ng Metro Manila sa panganib ng pagbaha. Humigit-kumulang "
          f"{p['pct_area_25yr']}% ng lupain nito ay nasa Medium/High flood zone "
          f"(25-taong ulan), kung saan nakatira ang tinatayang {p['est_pop_exposed']} "
          f"sa {p['population']} residente. Alamin ang evacuation plan ng inyong "
          f"barangay, itago ang mahahalagang dokumento sa waterproof na lalagyan, at "
          f"subaybayan ang opisyal na abiso ng PAGASA tuwing malakas ang ulan.")
    return {"en": en, "tl": tl}
