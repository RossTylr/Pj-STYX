"""Patient view (STYX × Theograph) — the integrated single-patient hero, hero-first.

LYR-1: a thin client. Every number comes from ``styx`` (one ``patient_frame`` per scrub); every
figure from a ``styx.viz`` pure builder; every explainer line from ``styx.explain``. This page only
arranges, toggles disclosure, and renders — it computes nothing.
"""

import streamlit as st

from styx.config import THRESHOLDS, VITALS
from styx.explain import EXPLAINERS
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
    return cohort.patients[pid], build_context(cohort, cohort.patients[pid])


# --- sidebar controls -------------------------------------------------------------------------
cohort = build_cohort(seed=42)
escalators = [p.pid for p in cohort.patients if p.archetype is not Archetype.STABLE]
pid = st.sidebar.selectbox("Patient", escalators, key="patient_pick",
                           format_func=lambda i: f"patient {i}")
explain_all = st.sidebar.toggle("Explain this page", value=False,
                                help="Show a plain what / how / why under every panel.")
patient, ctx = _context(pid)

# Replay clock: land on the silent window; reset when the patient changes.
default_pos = ctx.indices.index(ctx.default_idx)
if st.session_state.get("scrub_pid") != pid:
    st.session_state["scrub_pid"] = pid
    st.session_state["scrub_pos"] = default_pos

st.sidebar.markdown("**Replay clock**")
jump = st.sidebar.columns(4)
if jump[0].button("Silent", help="silent window"):
    st.session_state["scrub_pos"] = default_pos
if jump[1].button("AEGIS") and ctx.ticks["aegis"] is not None:
    st.session_state["scrub_pos"] = ctx.indices.index(ctx.ticks["aegis"])
if jump[2].button("Breach") and ctx.ticks["breach"] is not None:
    st.session_state["scrub_pos"] = ctx.indices.index(ctx.ticks["breach"])
if jump[3].button("Step ▶"):
    st.session_state["scrub_pos"] = min(st.session_state["scrub_pos"] + 1, len(ctx.indices) - 1)

_tickname = {idx: name.upper() for name, idx in ctx.ticks.items() if idx is not None}


def _clock_label(i: int) -> str:
    idx = ctx.indices[i]
    m = int(patient.t_min[idx])
    return f"{m} min" + (f" · {_tickname[idx]}" if idx in _tickname else "")


pos = st.sidebar.select_slider("clock", options=range(len(ctx.indices)), key="scrub_pos",
                               format_func=_clock_label, label_visibility="collapsed")
now_idx = ctx.indices[pos]
frame = patient_frame(ctx, now_idx)


def _header(title: str, cid: str) -> None:
    """A panel title with an ⓘ popover (and an inline card when 'Explain this page' is on)."""
    a, b = st.columns([9, 1])
    a.markdown(f"#### {title}")
    e = EXPLAINERS[cid]
    with b, st.popover("ⓘ"):
        st.markdown(f"**What** — {e.what}\n\n**How** — {e.how}\n\n**Why** — {e.why}")
    if explain_all:
        st.info(f"**What** {e.what}\n\n**How** {e.how}\n\n**Why** {e.why}")


# --- title + status row -----------------------------------------------------------------------
st.title(f"Patient {pid}")
st.caption(f"{patient.archetype.value.replace('_', ' ').title()}  ·  `{patient.archetype.value}`")

lead = ctx.fire.aegis_threshold_lead_min
s1, s2, s3 = st.columns(3)
s1.metric("Risk", f"{frame.risk_now:.2f}", frame.risk_verb, delta_color="off")
s2.metric("SENTINEL confidence", f"{frame.sentinel:.0%}", frame.sentinel_label, delta_color="off")
s3.metric("AEGIS lead", f"{lead / 60:.1f} h" if lead else "—", "before threshold", delta_color="off")

# --- hero: state-space trajectory -------------------------------------------------------------
_header("State-space trajectory", "trajectory")
st.plotly_chart(trajectory_figure(patient, ctx.emb, ctx.basins, events=ctx.on_path),
                width="stretch")

# --- anticipation: waterline ‖ cone -----------------------------------------------------------
left, right = st.columns(2)
with left:
    _header("Risk waterline", "waterline")
    st.plotly_chart(waterline_figure(patient.t_min, ctx.risk, ctx.threshold, aegis_idx=ctx.aegis_idx),
                    width="stretch")
with right:
    _header("Forecast cone", "cone")
    show_ghost = st.checkbox("Ghost trail (forecast at AEGIS)", value=True)
    if explain_all:
        g = EXPLAINERS["ghost"]
        st.caption(f"Ghost — {g.what}")
    st.plotly_chart(
        cone_figure(patient.t_min, ctx.risk, frame.cone, THRESHOLDS.risk_escalation,
                    now_idx=now_idx, ghost=ctx.ghost if show_ghost else None),
        width="stretch",
    )

# --- CALLIOPE: headline always; contributors only when they still sum to the risk -------------
_header("CALLIOPE — why this risk", "calliope")
st.markdown(f"**{frame.rationale.headline}**")
if frame.rationale.additive and frame.rationale.top_k[0][1] > 0:
    with st.expander("Show contributions (analyst)"):
        for name, val in frame.rationale.top_k:
            st.write(f"• {name}: {val:+.2f}")
        for line in frame.rationale.context:
            st.write(f"• {line}")
else:  # post-breach: the additive split no longer sums — show only the (σ-clamped) context
    for line in frame.rationale.context:
        st.caption(f"• {line}")

# --- Theograph (collapsed) + raw vitals (collapsed, off) --------------------------------------
with st.expander("Care history (Theograph)"):
    _header("Theograph", "theograph")
    st.plotly_chart(ribbon_figure(ctx.events), width="stretch")
    st.plotly_chart(detail_strip_figure(ctx.events), width="stretch")
with st.expander("Raw vitals (SIG-1)"):
    _header("Raw vitals", "raw_vitals")
    st.line_chart({v: patient.vitals[v] for v in VITALS})
