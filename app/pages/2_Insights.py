import pandas as pd
import plotly.express as px
import streamlit as st

from data_io import load_master, load_rainfall

st.set_page_config(page_title="BahaMap — Insights", page_icon="🌊", layout="wide")
st.title("Insights")

m = load_master()
h1, h2, h3 = st.columns(3)
h1.metric("Est. residents in 25-yr flood zones", f"{m['est_pop_exposed_25'].sum():,}")
h2.metric("Schools in flood zones",
          f"{m['schools_exposed'].sum():,} / {m['schools_total'].sum():,}")
h3.metric("Barangays ≥50% in flood zone", f"{(m['pct_area_mh_25'] >= 0.5).sum():,}")

st.subheader("Most exposed barangays")
top = m.nsmallest(20, "rank_ncr")[["rank_ncr", "name", "city", "score",
                                  "population", "est_pop_exposed_25",
                                  "pct_area_mh_25", "infra_exposed"]]
st.dataframe(top, hide_index=True, use_container_width=True,
             column_config={"pct_area_mh_25": st.column_config.ProgressColumn(
                 "% area in zone", min_value=0, max_value=1)})

st.subheader("City league table")
city = (m.groupby("city")
          .agg(population=("population", "sum"), exposed=("est_pop_exposed_25", "sum"))
          .assign(pct=lambda d: 100 * d["exposed"] / d["population"])
          .sort_values("pct").reset_index())
st.plotly_chart(px.bar(city, x="pct", y="city", orientation="h",
                       labels={"pct": "% of population exposed (25-yr)", "city": ""}),
                use_container_width=True)

st.subheader("Is extreme rainfall getting more frequent?")
annual, meta = load_rainfall()
fig = px.line(annual, x="year", y="days_ge_50",
              labels={"days_ge_50": "days ≥50mm", "year": ""})
fig.add_scatter(x=annual["year"], y=annual["days_ge_50"].rolling(10).mean(),
                name="10-yr rolling mean")
for name, date in meta["events"].items():
    fig.add_vline(x=int(date[:4]), line_dash="dot", annotation_text=name)
st.plotly_chart(fig, use_container_width=True)
t = meta["trends"]["days_ge_50"]
st.caption(f"Linear trend: {t['slope_per_decade']:+.2f} days/decade (p={t['p_value']}). "
           + meta["note"])
