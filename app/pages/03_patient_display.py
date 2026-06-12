"""Patient Display (HERMES) — the patient-safe, descriptive surface for families and carers.

LYR-1: a thin client. Every word comes from ``styx`` — the calm status and lay reason from
``styx.reach.carer`` (relabelling the *same* CALLIOPE attribution the clinician sees, faithfulness
1.000), the timeline from a pure ``styx.viz`` builder, the safe action from ``styx.explain``. This page
computes nothing and makes no predictive claim: it renders one fixed silent-window frame, in the
softest register — no scores, no codenames, no "breach"/"escalation"/"NEWS2".
"""

import streamlit as st

from styx.explain import CARER_ACTION, CARER_FOOTER
from styx.frame import build_context, patient_frame
from styx.reach.carer import lay_explain, lay_status
from styx.synth import Archetype, build_cohort
from styx.timeline import episode_timeline
from styx.viz.carer import carer_timeline_figure

st.set_page_config(page_title="Patient Display", layout="wide")
st.warning(
    "Demo mode: **replay of synthetic data** — no real patient data, not a live deployment.",
    icon="⚠️",
)


@st.cache_resource
def _context(pid: int):
    cohort = build_cohort(seed=42)
    return cohort.patients[pid], build_context(cohort, cohort.patients[pid])


# --- patient picker (shared key with the clinician pages; no replay clock — a fixed, calm frame) ---
cohort = build_cohort(seed=42)
escalators = [p.pid for p in cohort.patients if p.archetype is not Archetype.STABLE]
pid = st.sidebar.selectbox("Patient", escalators, key="patient_pick",
                           format_func=lambda i: f"patient {i}")
patient, ctx = _context(pid)

# One fixed silent-window frame — the page can never surface a future / post-threshold view.
frame = patient_frame(ctx, ctx.default_idx)
lay = lay_explain(frame.rationale)
status = lay_status(frame.rationale)

# --- calm status -------------------------------------------------------------------------------
st.title(f"Patient {pid}")
st.subheader(status.status)

# --- the plain reason (same primary driver as the clinician view) ------------------------------
st.markdown("##### What is standing out")
st.markdown(lay.headline)

# --- a calm view of the stay so far ------------------------------------------------------------
st.plotly_chart(carer_timeline_figure(episode_timeline(ctx)), width="stretch")
st.caption("The shaded bar shows the stay so far; the right-hand edge marks the current position.")

# --- one safe action ---------------------------------------------------------------------------
st.info(CARER_ACTION)

st.caption(CARER_FOOTER)
