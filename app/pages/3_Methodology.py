import pandas as pd
import streamlit as st
from data_io import PROCESSED

st.set_page_config(page_title="BahaMap · Methodology", page_icon="🌊")
st.title("Methodology & Data")

st.markdown("""
### Question
Who in Metro Manila lives in harm's way when the floods come?

### Data
| Layer | Source | Notes |
|---|---|---|
| Flood hazard (5/25/100-yr, 10m) | UP Project NOAH / DOST via LiPAD & BetterGov mirror | Medium+High zones used |
| Barangay boundaries | PSA PSGC (altcoder/philippines-psgc-shapefiles) | 1,710 NCR barangays |
| Population | PSA 2020 Census via OCHA/HDX | joined on PSGC pcode; reconciles to 13,484,462 |
| Schools & health facilities | © OpenStreetMap contributors (ODbL) | coverage is partial; treat as "mapped facilities" |
| Rainfall 1940-2025 | Open-Meteo ERA5 archive (CC-BY-4.0) | area average of 4 NCR points |

### Exposure score
For each barangay, on the 25-year return period: share of land area inside
Medium/High zones; estimated residents in those zones (population × area share;
assumes uniform density); OSM facilities inside zones. Each component is min-max
normalized across NCR and blended **0.5 population / 0.3 area / 0.2 infrastructure**,
scaled 0-100. The weights are an editorial choice, shown with a sensitivity check below.

Return periods are treated as nested scenarios: each period's Medium/High zone
is unioned with all shorter periods' zones, because a rarer flood covers at
least what a more frequent one does. (The source layers are separate model runs
and are not perfectly nested on their own; the 100-yr layer locally classifies
some 25-yr Medium/High cells as Low.)

### Limitations
Hazard maps model riverine/rain flooding at their production vintage; drainage and
mitigation works change reality. Uniform density is wrong where barangays mix uses.
OSM is incomplete. ERA5 smooths extreme point rainfall. The 2020 census predates
the Makati→Taguig transfer of the 10 EMBO barangays; they are shown under Taguig
with their census-vintage populations. **This is an educational
project, not official hazard guidance.** For real decisions, consult
[UP NOAH](https://noah.up.edu.ph) and [PAGASA](https://bagong.pagasa.dost.gov.ph).

### AI briefs
Claude writes each barangay's brief (English + Tagalog) from that barangay's
computed numbers only. A validator then checks every number in the text against
the input payload; if a number is missing, the brief is regenerated or replaced
by a deterministic template. Model: claude-haiku-4-5, batch API.
""")

st.subheader("Weight sensitivity")
st.dataframe(pd.read_csv(PROCESSED / "sensitivity.csv"), hide_index=True)
st.caption("Spearman rank correlation between the baseline ranking and the ranking "
           "after shifting one weight ±10 percentage points (others rescaled).")
