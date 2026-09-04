"""Validate raw briefs; regenerate-or-template failures; write final briefs.json."""
import json
import sys
from datetime import UTC, datetime

import pandas as pd

# Allow running as `python pipeline/07_validate_briefs.py` from the repo root:
# a script's own folder (pipeline/) lands on sys.path, the repo root does not.
if __package__ in (None, ""):
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.grounding import build_payload, template_brief, validate
from pipeline.paths import PROCESSED, RAW


def main() -> None:
    raw = json.loads((RAW / "briefs_raw.json").read_text(encoding="utf-8"))
    m = pd.read_parquet(PROCESSED / "barangay_master.parquet")
    final, n_fail = {}, 0
    for row in m.to_dict("records"):
        p = build_payload(row, n_bgys=len(m))
        entry = raw.get(p["pcode"])
        bad = (validate(entry["en"], p) + validate(entry["tl"], p)) if entry else ["missing"]
        if entry and not bad:
            final[p["pcode"]] = entry
        else:
            n_fail += 1
            t = template_brief(p)
            final[p["pcode"]] = {"en": t["en"], "tl": t["tl"], "source": "template",
                                 "model": None,
                                 "generated_at": datetime.now(UTC).isoformat()}
            if entry:
                print(f"FAIL {p['pcode']} {row['name']}: ungrounded numbers {bad}")
    (PROCESSED / "briefs.json").write_text(
        json.dumps(final, ensure_ascii=False, indent=1), encoding="utf-8")
    rate = 1 - n_fail / len(m)
    print(f"grounding pass rate {rate:.1%}; {n_fail} templated; wrote briefs.json ({len(final)})")


if __name__ == "__main__":
    main()
