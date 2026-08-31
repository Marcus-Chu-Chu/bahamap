import plotly.express as px
import streamlit as st

from data_io import load_briefs, load_geojson, load_master

st.set_page_config(page_title="BahaMap", page_icon="🌊", layout="wide")
st.title("BahaMap: Metro Manila Flood Exposure Atlas")
st.caption("Who lives in harm's way when the floods come? "
           "Educational project, not official hazard guidance. See Methodology.")

m = load_master()
gj = load_geojson()
briefs = load_briefs()

METRICS = {
    "Exposure score (0-100)": "score",
    "% of area in 25-yr flood zone": "pct_area_mh_25",
    "Est. residents exposed (25-yr)": "est_pop_exposed_25",
    "% of area in 5-yr flood zone": "pct_area_mh_5",
    "% of area in 100-yr flood zone": "pct_area_mh_100",
}

left, right = st.columns([3, 2], gap="large")
with left:
    c1, c2 = st.columns(2)
    metric = c1.selectbox("Color by", list(METRICS))
    cities = c2.multiselect("Filter cities", sorted(m["city"].unique()))
    view = m[m["city"].isin(cities)] if cities else m
    fig = px.choropleth_map(
        view, geojson=gj, locations="pcode", featureidkey="properties.pcode",
        color=METRICS[metric], color_continuous_scale="YlOrRd",
        hover_name="name", hover_data={"city": True, "score": True, "pcode": False},
        custom_data=["pcode"], center={"lat": 14.60, "lon": 121.02},
        zoom=10.2, height=640, opacity=0.75)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    event = st.plotly_chart(fig, on_select="rerun", selection_mode="points",
                            use_container_width=True)

sel = None
if event and event.selection and event.selection.points:
    sel = event.selection.points[0]["customdata"][0]

with right:
    options = view.sort_values("name")
    labels = options["name"] + ", " + options["city"]
    idx = int(options.reset_index().index[options["pcode"] == sel][0]) if sel in set(options["pcode"]) else 0
    pick = st.selectbox("Barangay (or click the map)", labels, index=idx)
    row = options.iloc[list(labels).index(pick)]

    st.subheader(f"{row['name']}, {row['city']}")
    a, b, c, d = st.columns(4)
    a.metric("Exposure rank", f"#{row['rank_ncr']}", help="of all NCR barangays")
    b.metric("Score", f"{row['score']:.0f}/100")
    c.metric("Population (2020)", f"{row['population']:,}")
    d.metric("Est. exposed (25-yr)", f"{row['est_pop_exposed_25']:,}")

    st.progress(min(1.0, row["pct_area_mh_25"]),
                text=f"{row['pct_area_mh_25']:.0%} of area in 25-yr Medium/High zone "
                     f"(5-yr: {row['pct_area_mh_5']:.0%} · 100-yr: {row['pct_area_mh_100']:.0%})")
    st.write(f"**Facilities in flood zone:** {row['schools_exposed']} of "
             f"{row['schools_total']} schools · {row['health_exposed']} of "
             f"{row['health_total']} health facilities *(OSM-mapped)*")
    st.write(f"Score components: population {row['pop_norm']:.2f} · "
             f"area {row['area_norm']:.2f} · infrastructure {row['infra_norm']:.2f} "
             f"(weights 0.5/0.3/0.2)")

    brief = briefs.get(row["pcode"])
    if brief:
        en, tl = st.tabs(["English brief", "Tagalog"])
        en.write(brief["en"])
        tl.write(brief["tl"])
    else:
        st.info("AI risk brief coming soon.")
