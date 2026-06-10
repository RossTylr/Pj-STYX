"""STYX Streamlit entry (LYR-1: thin client — imports styx, holds zero logic)."""

import streamlit as st

from styx.explain import SCOPE_LINE
from styx.readouts import footer_text

st.set_page_config(page_title="STYX", layout="wide")
st.title("STYX — virtual-ward trajectory monitor")

# Hard Rule 7: the demo is replay-of-synthetic; say so plainly. No real patient data.
st.warning(
    "Demo mode: **replay of synthetic data** — no real patient data, not a live "
    "or streaming deployment.",
    icon="⚠️",
)

# (6b) Scope / blind-spot: what STYX sees, and what "no alert" must and must not be read as.
st.info(SCOPE_LINE)

st.info("Open the **Ward** board in the sidebar for cohort triage (rank by time-to-escalation, the "
        "silent-but-rising watchlist, ECHO look-alikes), then click a patient to drill into the "
        "integrated single-patient **Patient** view at the same moment.")

st.caption(footer_text())
