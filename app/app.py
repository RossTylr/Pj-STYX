"""STYX Streamlit entry (LYR-1: thin client — imports styx, holds zero logic)."""

import streamlit as st

import styx
from styx.config import RESCORE_CADENCE_MIN, VITALS

st.set_page_config(page_title="STYX", layout="wide")
st.title("STYX — virtual-ward trajectory monitor")
st.caption(f"v{styx.__version__}")

# Hard Rule 7: the demo is replay-of-synthetic; say so plainly. No real patient data.
st.warning(
    "Demo mode: **replay of synthetic data** — no real patient data, not a live "
    "or streaming deployment.",
    icon="⚠️",
)

st.write(f"Vital set (SIG-1): {', '.join(VITALS)}")
st.write(f"Re-score cadence: every {RESCORE_CADENCE_MIN} min (sim-time)")
st.info("Open the **Ward** board in the sidebar for cohort triage (rank by time-to-escalation, the "
        "silent-but-rising watchlist, ECHO look-alikes), then click a patient to drill into the "
        "integrated single-patient **Patient** view at the same moment.")
