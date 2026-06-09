"""Ward board (stub) — the cohort triage view lands in Slice S5 (F6 + F10).

Placeholder so the two-screen nav scaffold exists now; no logic (LYR-1).
"""

import streamlit as st

st.set_page_config(page_title="STYX — ward", layout="wide")
st.warning(
    "Demo mode: **replay of synthetic data** — no real patient data, not a live deployment.",
    icon="⚠️",
)
st.title("Ward board")
st.info("Cohort triage (F6 risk-ranked board + F10 ward-level lead) lands in Slice S5.")
