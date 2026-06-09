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
st.info("Open **Patient** in the sidebar for the integrated single-patient view (S4). "
        "The **Ward** board lands in S5.")
