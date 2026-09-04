"""Generate bilingual briefs for every barangay via the Message Batches API.

Usage: python pipeline/06_generate_briefs.py [--limit N] [--yes]
Writes data/raw/briefs_raw.json (unvalidated model output, gitignored path).
"""
import argparse
import json
import os
import sys
import time
from datetime import UTC, datetime

import pandas as pd
from anthropic import Anthropic

# Allow running as `python pipeline/06_generate_briefs.py` from the repo root:
# a script's own folder (pipeline/) lands on sys.path, the repo root does not.
if __package__ in (None, ""):
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.grounding import build_payload
from pipeline.paths import PROCESSED, RAW, ROOT

MODEL = "claude-haiku-4-5"
SYSTEM = """You write short public-safety briefs about flood exposure for Metro Manila barangays, based on Project NOAH hazard-model scenarios. These are model scenarios, NOT historical flood records.

What the user JSON fields mean — you may restate them ONLY with these meanings:
- pct_area_5yr / pct_area_25yr / pct_area_100yr: percent of the barangay's LAND inside the modeled Medium/High flood zone in a 5- / 25- / 100-year flood scenario. An "N-year flood" is a severity with a 1-in-N chance of happening in any given year. It is NOT how often the area floods and NOT a historical observation — never say the area "flooded" or "experienced flooding" in the past N years.
- est_pop_exposed: estimated residents living inside the 25-year flood zone (out of "population").
- schools_exposed / health_exposed: mapped schools / health facilities inside the 25-year zone.
- rank_ncr: flood-exposure rank (1 = most exposed) out of n_bgys_ncr Metro Manila barangays.
- The zone is always called the "Medium/High flood zone" at every return period; there is no separate "medium zone" or "high zone" per scenario.

Rules, non-negotiable:
- Use ONLY the numbers in the user's JSON, written exactly as given (you may add thousands separators). Never compute, estimate, or invent any number.
- Plain, calm, non-alarmist language. No specific local claims (no street names, no named evacuation centers) — only generic preparedness advice (know the barangay evacuation plan, keep documents waterproof, follow PAGASA advisories).
- ~120 words per language.
- The Tagalog must read like a native Metro Manila speaker wrote it directly — natural conversational Tagalog, with Taglish fine for technical terms (flood zone, emergency kit, evacuation plan). Never invent Tagalog words; if unsure of a term, keep the English term. Do not translate the English word-for-word. Grammar slips to avoid: barangay names take "Ang", never "Si"; count with correct linkers ("apat na paaralan", "limang paaralan") and never "lima pang" (that means "five more"); "importanteng dokumento", not "importante documents".
Output STRICTLY a JSON object: {"en": "...", "tl": "..."}. No other text."""


def load_env_key() -> None:
    """Populate ANTHROPIC_API_KEY / ANTHROPIC_WORKSPACE_ID from the gitignored
    repo-root .env, unless already set. The workspace id is required by the API
    when the key is identity-linked (the Console's newer key type)."""
    if not (ROOT / ".env").exists():
        return
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        key, _, val = line.partition("=")
        key = key.strip()
        if key in ("ANTHROPIC_API_KEY", "ANTHROPIC_WORKSPACE_ID") and key not in os.environ:
            os.environ[key] = val.strip().strip("'\"")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, help="only the N highest-exposure barangays")
    ap.add_argument("--yes", action="store_true")
    args = ap.parse_args()

    m = pd.read_parquet(PROCESSED / "barangay_master.parquet")
    rows = m.nsmallest(args.limit, "rank_ncr") if args.limit else m
    payloads = [build_payload(r, n_bgys=len(m)) for r in rows.to_dict("records")]

    est_cost = len(payloads) * 900 / 1e6 * 5  # ~900 tok/req, rough $5/Mtok blended batch
    print(f"{len(payloads)} briefs, rough cost ≤ ${est_cost:.2f}")
    if not args.yes and input("proceed? [y/N] ").lower() != "y":
        sys.exit("aborted")

    load_env_key()
    if not os.environ.get("ANTHROPIC_API_KEY", "").startswith("sk-ant-") or \
            os.environ.get("ANTHROPIC_API_KEY") == "sk-ant-your-key-here":
        sys.exit("no API key: paste yours into .env (see .env.example) or set ANTHROPIC_API_KEY")

    wid = os.environ.get("ANTHROPIC_WORKSPACE_ID")
    client = Anthropic(default_headers={"anthropic-workspace-id": wid} if wid else None)
    reqs = [{"custom_id": p["pcode"],
             "params": {"model": MODEL, "max_tokens": 700, "temperature": 0.3,
                        "system": SYSTEM,
                        "messages": [{"role": "user",
                                      "content": json.dumps(p, ensure_ascii=False)}]}}
            for p in payloads]
    batch = client.messages.batches.create(requests=reqs)
    print(f"batch {batch.id} submitted; polling...")
    while True:
        b = client.messages.batches.retrieve(batch.id)
        print(f"  {b.processing_status} {dict(b.request_counts)}")
        if b.processing_status == "ended":
            break
        time.sleep(60)

    out = {}
    for res in client.messages.batches.results(batch.id):
        if res.result.type != "succeeded":
            print(f"  {res.custom_id}: {res.result.type}")
            continue
        text = res.result.message.content[0].text.strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            parsed = json.loads(text)
            out[res.custom_id] = {"en": parsed["en"], "tl": parsed["tl"],
                                  "source": "claude", "model": MODEL,
                                  "generated_at": datetime.now(UTC).isoformat()}
        except (json.JSONDecodeError, KeyError):
            print(f"  {res.custom_id}: unparseable output")
    (RAW / "briefs_raw.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                         encoding="utf-8")
    print(f"wrote {len(out)}/{len(payloads)} raw briefs")


if __name__ == "__main__":
    main()
