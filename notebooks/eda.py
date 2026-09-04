# %% [markdown]
# # BahaMap EDA — produces memo charts and headline numbers
# %%
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repo root importable

import pandas as pd
import plotly.express as px

from pipeline.paths import HEADLINE_RP, PROCESSED  # noqa: E402

OUT = Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)
m = pd.read_parquet(PROCESSED / "barangay_master.parquet")

# %% headline numbers (copy these into docs/findings-memo.md)
half_flooded = m[m[f"pct_area_mh_{HEADLINE_RP}"] >= 0.5]
print(f"HEADLINE: {half_flooded['population'].sum():,} residents live in "
      f"{len(half_flooded)} barangays that are >=50% inside the {HEADLINE_RP}-yr Medium/High zone")
print(f"HEADLINE: total est. exposed population (25yr): {m['est_pop_exposed_25'].sum():,}")
print(f"HEADLINE: exposed schools: {m['schools_exposed'].sum():,} of {m['schools_total'].sum():,}; "
      f"exposed health facilities: {m['health_exposed'].sum():,} of {m['health_total'].sum():,}")
city = m.groupby("city").agg(pop=("population", "sum"),
                             exposed=("est_pop_exposed_25", "sum"))
city["pct"] = (100 * city["exposed"] / city["pop"]).round(1)
print("\nCity exposure table:\n", city.sort_values("pct", ascending=False).to_string())

# %% concentration + sensitivity extras for the memo
srt = m.sort_values("est_pop_exposed_25", ascending=False).reset_index(drop=True)
top_k = 100
share = srt.loc[:top_k - 1, "est_pop_exposed_25"].sum() / max(1, srt["est_pop_exposed_25"].sum())
print(f"HEADLINE: top {top_k} barangays ({top_k / len(m):.1%} of count) hold "
      f"{share:.1%} of all exposed residents")
sens = pd.read_csv(PROCESSED / "sensitivity.csv")
print(f"HEADLINE: min rank corr under ±10pp weight shifts: {sens['spearman_rank_corr'].min()}")

# %% charts
fig = px.bar(city.sort_values("pct").reset_index(), x="pct", y="city", orientation="h",
             title=f"Share of population in {HEADLINE_RP}-yr Medium/High flood zones, by city",
             labels={"pct": "% of population exposed", "city": ""})
fig.write_image(OUT / "city_exposure.png", width=900, height=650, scale=2)

ann = pd.read_parquet(PROCESSED / "rainfall_annual.parquet").reset_index()
meta = json.loads((PROCESSED / "rainfall_meta.json").read_text(encoding="utf-8"))
fig2 = px.line(ann, x="year", y="days_ge_50",
               title="Days ≥50mm rainfall per year (NCR area average, ERA5)")
fig2.add_scatter(x=ann["year"], y=ann["days_ge_50"].rolling(10).mean(),
                 name="10-yr rolling mean")
for name, date in meta["events"].items():
    fig2.add_vline(x=int(date[:4]), line_dash="dot", annotation_text=name)
fig2.write_image(OUT / "rainfall_trend.png", width=900, height=500, scale=2)
print("charts written to notebooks/out/")
