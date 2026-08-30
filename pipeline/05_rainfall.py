"""Average the four Open-Meteo points into one NCR daily series; write metrics."""
import json
import sys

import pandas as pd

# Allow running as `python pipeline/05_rainfall.py` from the repo root:
# a script's own folder (pipeline/) lands on sys.path, the repo root does not.
if __package__ in (None, ""):
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline import rainfall
from pipeline.paths import PROCESSED, RAIN_EVENTS, RAIN_POINTS, RAW


def main() -> None:
    frames = []
    for i in range(len(RAIN_POINTS)):
        body = json.loads((RAW / "rain" / f"point_{i}.json").read_text(encoding="utf-8"))
        frames.append(pd.DataFrame({"date": body["daily"]["time"],
                                    f"mm_{i}": body["daily"]["precipitation_sum"]}))
    df = frames[0]
    for f in frames[1:]:
        df = df.merge(f, on="date")
    daily = pd.DataFrame({"date": df["date"],
                          "mm": df[[c for c in df if c.startswith("mm_")]].mean(axis=1)})
    daily = daily.dropna()

    annual = rainfall.annual_metrics(daily)
    annual.to_parquet(PROCESSED / "rainfall_annual.parquet")

    daily_idx = daily.set_index("date")["mm"]
    meta = {
        "trends": {c: rainfall.trend(annual, c)
                   for c in ("max_daily_mm", "days_ge_50", "days_ge_100")},
        "events": RAIN_EVENTS,
        "event_daily_mm": {name: round(float(daily_idx.get(date, float("nan"))), 1)
                           for name, date in RAIN_EVENTS.items()},
        "note": ("ERA5 reanalysis (~31km grid) smooths point extremes; values are "
                 "area-averaged and used for trends, not absolute records."),
    }
    (PROCESSED / "rainfall_meta.json").write_text(json.dumps(meta, indent=2),
                                                  encoding="utf-8")
    print(annual.tail(10).to_string(), "\n", json.dumps(meta["trends"], indent=2))


if __name__ == "__main__":
    main()
