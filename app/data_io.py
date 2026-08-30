"""Cached read-only loaders. The app never computes geospatial operations."""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"


@st.cache_data
def load_master() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / "barangay_master.parquet")


@st.cache_data
def load_geojson() -> dict:
    return json.loads((PROCESSED / "barangays_wgs84.geojson").read_text(encoding="utf-8"))


@st.cache_data
def load_briefs() -> dict:
    p = PROCESSED / "briefs.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


@st.cache_data
def load_rainfall():
    annual = pd.read_parquet(PROCESSED / "rainfall_annual.parquet").reset_index()
    meta = json.loads((PROCESSED / "rainfall_meta.json").read_text(encoding="utf-8"))
    return annual, meta
