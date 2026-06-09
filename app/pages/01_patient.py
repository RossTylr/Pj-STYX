"""Patient view (STYX × Theograph) — the integrated single-patient hero.

LYR-1: a thin client. Every number comes from ``styx`` (one ``patient_frame`` per scrub); every
figure from a ``styx.viz`` pure builder. This page only lays them out and renders.
"""

import streamlit as st

from styx.config import THRESHOLDS, VITALS
from styx.frame import build_context, patient_frame
from styx.synth import Archetype, build_cohort
from styx.viz.cone import cone_figure
from styx.viz.theograph import detail_strip_figure, ribbon_figure
from styx.viz.trajectory import trajectory_figure
from styx.viz.waterline import waterline_figure

st.set_page_config(page_title="STYX — patient", layout="wide")
st.warning(
    "Demo mode: **replay of synthetic data** — no real patient data, not a live deployment.",
    icon="⚠️",
)


@st.cache_resource
def _context(pid: int):
    cohort = build_cohort(seed=42)
    patient = cohort.patients[pid]
    return patient, build_context(cohort, patient)


# --- controls (sidebar) -----------------------------------------------------------------------
cohort = build_cohort(seed=42)
escalators = [p.pid for p in cohort.patients if p.archetype is not Archetype.STABLE]
pid = st.sidebar.selectbox("Patient", escalators, index=0, format_func=lambda i: f"patient {i}")
patient, ctx = _context(pid)
labels = [f"{int(ctx.patient.t_min[i])} min" for i in ctx.indices]
pos = st.sidebar.select_slider("Replay clock (scrub)", options=range(len(ctx.indices)),
                               value=len(ctx.indices) - 1, format_func=lambda i: labels[i])
show_ghost = st.sidebar.checkbox("Ghost trail (forecast at AEGIS)", value=True)
now_idx = ctx.indices[pos]
frame = patient_frame(ctx, now_idx)

# --- CALLIOPE + SENTINEL ----------------------------------------------------------------------
st.title(f"Patient {pid} — {patient.archetype.value}")
head, conf = st.columns([4, 1])
head.subheader(frame.rationale.headline)
conf.metric("SENTINEL confidence", f"{frame.sentinel:.0%}", frame.sentinel_label)
if frame.rationale.expand:
    with st.expander("CALLIOPE — top contributors"):
        for line in frame.rationale.expand:
            st.write(f"• {line}")

# --- state map + risk -------------------------------------------------------------------------
left, right = st.columns(2)
left.plotly_chart(trajectory_figure(patient, ctx.emb, ctx.basins, events=ctx.on_path),
                  width="stretch")
right.plotly_chart(
    waterline_figure(patient.t_min, ctx.risk, ctx.threshold, aegis_idx=ctx.aegis_idx),
    width="stretch",
)
right.plotly_chart(
    cone_figure(patient.t_min, ctx.risk, frame.cone, THRESHOLDS.risk_escalation,
                now_idx=now_idx, ghost=ctx.ghost if show_ghost else None),
    width="stretch",
)

# --- dual-scale Theograph ---------------------------------------------------------------------
st.plotly_chart(ribbon_figure(ctx.events), width="stretch")
st.plotly_chart(detail_strip_figure(ctx.events), width="stretch")

# --- raw vitals (collapsible) -----------------------------------------------------------------
with st.expander("Raw vitals (SIG-1)"):
    st.line_chart({v: patient.vitals[v] for v in VITALS})
