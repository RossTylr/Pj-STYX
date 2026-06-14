"""Clinical basis — the reference page: what STYX is grounded in, its scope and its limits.

LYR-1: a thin client. Every word comes from ``styx.clinical_basis``; the scoring table from
``styx.viz.scoring_table``; the footer from ``styx.readouts``. This page only arranges and
renders — it computes nothing and invents no copy (the cascade-stage definitions are unsettled
and render as placeholders by design).
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from styx.clinical_basis import (
    CANNOT_SEE_PROSE,
    CHARTS,
    DERIVED_BADGE,
    GLOSSARY,
    INTENDED_USE,
    NO_ALERT_LINE,
    NURSE_OBS_PROSE,
    OXYGEN_UPLIFT_LINE,
    PAGE_PURPOSE,
    RCP_ACKNOWLEDGEMENT,
    READS_PROSE,
    TABLE_NURSE_COLUMNS,
    TABLE_NURSE_ROWS,
    REFERENCES,
    RELATIONSHIP_LINE,
    SCALE2_CONSTRAINT,
    TABLE_A_NOTE,
    TABLE_B_COLUMNS,
    TABLE_B_ROWS,
    TABLE_C_CAPTION,
    TABLE_C_COLUMNS,
    TABLE_C_ROWS,
    TABLE_D_CAPTION,
    TABLE_D_COLUMNS,
    TABLE_D_ROWS,
    VIRTUAL_WARD_GUARDRAIL,
    VIRTUAL_WARD_PLACEMENT,
    WHY_TRAJECTORY,
    ChartAsset,
)
from styx.readouts import footer_text
from styx.viz.scoring_table import scoring_table_styler

_ASSETS = Path(__file__).resolve().parents[1] / "assets"

# Page config, logo and brand chrome are owned by the router (app/app.py via st.navigation).
st.title("Clinical basis")
st.caption(PAGE_PURPOSE)
st.warning(
    "Demo mode: **replay of synthetic data** — no real patient data, not a live deployment.",
    icon="⚠️",
)


def _official_chart(chart: ChartAsset) -> None:
    # §B copyright rule: the official colour image, unmodified, with the verbatim acknowledgement;
    # if the asset is not bundled, the expander falls back to the RCP source link instead.
    with st.expander(chart.title):
        path = _ASSETS / chart.filename
        if path.exists():
            st.image(str(path), width="stretch")
        else:
            st.info(f"Official chart not bundled with this demo — view it at {chart.source_url}")
        st.caption(RCP_ACKNOWLEDGEMENT)


def _prose_table(columns: tuple[str, ...], rows: tuple[tuple[str, ...], ...]) -> None:
    # st.table wraps long prose cells (st.dataframe truncates); first column as the index.
    st.table(pd.DataFrame(rows, columns=list(columns)).set_index(columns[0]))


# --- §2 Intended use and scope (governance) ----------------------------------------------------
st.divider()
st.markdown("### Intended use and scope")
for line in INTENDED_USE:
    st.markdown(f"- {line}")
st.info(NO_ALERT_LINE)

# --- §3 What STYX reads ------------------------------------------------------------------------
st.divider()
st.markdown("### What STYX reads")
st.markdown(READS_PROSE)
st.table(scoring_table_styler())
st.caption(f"{DERIVED_BADGE} Column headers are the NEWS2 point values.")
st.markdown(f"*{TABLE_A_NOTE}*")
_official_chart(CHARTS[0])

# --- §3b What the nurse obs round adds to the comparator ---------------------------------------
st.divider()
st.markdown("### What the nurse obs round adds")
st.markdown(NURSE_OBS_PROSE)
_prose_table(TABLE_NURSE_COLUMNS, TABLE_NURSE_ROWS)

# --- §4 What STYX cannot see -------------------------------------------------------------------
st.divider()
st.markdown("### What STYX cannot see")
st.markdown(CANNOT_SEE_PROSE)
_prose_table(TABLE_B_COLUMNS, TABLE_B_ROWS)
st.info(SCALE2_CONSTRAINT)
st.markdown(OXYGEN_UPLIFT_LINE)

# --- §5 STYX and NEWS2 (relationship and escalation) -------------------------------------------
st.divider()
st.markdown("### STYX and NEWS2")
st.markdown(RELATIONSHIP_LINE)
_prose_table(TABLE_C_COLUMNS, TABLE_C_ROWS)
st.caption(TABLE_C_CAPTION)
_prose_table(TABLE_D_COLUMNS, TABLE_D_ROWS)
st.caption(TABLE_D_CAPTION)
_official_chart(CHARTS[1])
_official_chart(CHARTS[2])

# --- §6 Why trajectory, not just threshold -----------------------------------------------------
st.divider()
st.markdown("### Why trajectory, not just threshold")
st.markdown(WHY_TRAJECTORY)

# --- §7 Place within the virtual-ward framework ------------------------------------------------
st.divider()
st.markdown("### Place within the virtual-ward framework")
st.markdown(VIRTUAL_WARD_PLACEMENT)
st.info(VIRTUAL_WARD_GUARDRAIL)

# --- §8 Glossary (cascade-stage definitions unsettled — placeholders by design) ------------------
st.divider()
st.markdown("### Glossary")
for entry in GLOSSARY:
    st.markdown(f"**{entry.term}** — {entry.definition}")

# --- §9 References and attribution (both mechanisms, kept distinct) -----------------------------
st.divider()
st.markdown("### References and attribution")
st.markdown("**Chart attribution** — for any NEWS2 chart reproduced on this page:")
st.caption(RCP_ACKNOWLEDGEMENT)
st.markdown("**References**")
for reference in REFERENCES:
    st.markdown(f"- {reference}")

st.caption(footer_text())
