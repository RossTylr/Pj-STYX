"""Patient view (STYX × Theograph) — the integrated single-patient hero, hero-first.

LYR-1: a thin client. Every number comes from ``styx`` (one ``patient_frame`` per scrub); every
figure from a ``styx.viz`` pure builder; every explainer line from ``styx.explain``. This page only
arranges, toggles disclosure, and renders — it computes nothing.
"""

import streamlit as st

from styx.config import THRESHOLDS, VITALS
from styx.explain import (
    ARCHETYPE_PATTERNS,
    DISPLAY_NAMES,
    EXPLAINERS,
    NEWS2_PARTIAL_LABEL,
    OBS_AGE_TEMPLATE,
    SCORE_CAPTION,
)
from styx.cohort import build_cohort_context
from styx.cohort.echo import echo_neighbours
from styx.frame import build_context, patient_frame
from styx.reach.decoupling import decoupling_onset
from styx.reach.history import stratify
from styx.readouts import footer_text, news2_crossing, sim_clock, styx_index
from styx.synth import Archetype, build_cohort
from styx.timeline import episode_timeline
from styx.viz.coherence import coherence_figure
from styx.viz.cone import cone_figure
from styx.viz.hazard import hazard_figure
from styx.viz.theograph import detail_strip_figure, ribbon_figure
from styx.viz.timeline import timeline_figure
from styx.viz.trajectory import clinical_trajectory_figure  # trajectory_figure retained as future model view
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


@st.cache_resource
def _hazard():
    # Cohort-wide history-as-prior stratification — same for every patient, so fit once (no pid arg).
    return stratify(build_cohort_context(build_cohort(seed=42)))


@st.cache_resource
def _echo_endpoints(pid: int) -> list[tuple[float, float]]:
    # Past-deterioration cluster for the clinical hero: the (SpO₂, RR) endpoints of the escalated
    # look-alikes (read-only retrieval; the figure just plots the points).
    cohort = build_cohort(seed=42)
    cctx = build_cohort_context(cohort)
    _, c = _context(pid)
    return [
        (float(cohort.patients[n.pid].vitals["SpO2"][-1]),
         float(cohort.patients[n.pid].vitals["RR"][-1]))
        for n in echo_neighbours(cctx, pid, c.default_idx) if n.outcome == "escalated"
    ]


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
# 2×2 (not 4 across): a sidebar column split four ways is too narrow and wraps the labels.
top, bottom = st.sidebar.columns(2), st.sidebar.columns(2)
if top[0].button("Silent", help="silent window", width="stretch"):
    st.session_state["scrub_pos"] = default_pos
if top[1].button(DISPLAY_NAMES["aegis"], width="stretch") and ctx.ticks["aegis"] is not None:
    st.session_state["scrub_pos"] = ctx.indices.index(ctx.ticks["aegis"])
if bottom[0].button("Breach", width="stretch") and ctx.ticks["breach"] is not None:
    st.session_state["scrub_pos"] = ctx.indices.index(ctx.ticks["breach"])
if bottom[1].button("Step ▶", width="stretch"):
    st.session_state["scrub_pos"] = min(st.session_state["scrub_pos"] + 1, len(ctx.indices) - 1)

# Clock-tick labels: plain display name for codename ticks (e.g. aegis), else the upper-cased key.
_tickname = {idx: DISPLAY_NAMES.get(name, name.upper())
             for name, idx in ctx.ticks.items() if idx is not None}


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
st.caption(f"Pattern: {ARCHETYPE_PATTERNS[patient.archetype.value]}")

lead = ctx.fire.aegis_threshold_lead_min
s1, s2, s3 = st.columns(3)
s1.metric("STYX index", f"{styx_index(frame.risk_now)} / 100", frame.risk_verb, delta_color="off")
s1.caption(SCORE_CAPTION)
s2.metric(DISPLAY_NAMES["sentinel"], f"{frame.sentinel:.0%}", frame.sentinel_label, delta_color="off")
s3.metric(f"{DISPLAY_NAMES['aegis']} lead", f"{lead / 60:.1f} h" if lead else "—",
          "before threshold", delta_color="off")
st.caption(OBS_AGE_TEMPLATE.format(clock=sim_clock(frame.now_min)))

# --- hero: clinical state-space trajectory (SpO₂ × RR) ----------------------------------------
# Scrub-driven (6d.2): the replay clock moves the "now" cursor and reveals the cascade markers in
# fire order; hover carries the per-marker detail. trajectory_figure (constructed/model axes) is
# retained as the future model view — imported, not rendered.
_header(DISPLAY_NAMES["trajectory"], "trajectory")
try:
    _decoupling_min = decoupling_onset(patient).onset_min
except ValueError:
    _decoupling_min = None  # not every escalator carries a decoupling onset
st.plotly_chart(
    clinical_trajectory_figure(
        patient, decoupling_min=_decoupling_min, aegis_min=ctx.fire.aegis_min,
        escalation_min=ctx.fire.threshold_min, news2_min=news2_crossing(patient),
        echo_endpoints=_echo_endpoints(pid), now_idx=now_idx,
    ),
    width="stretch",
)

# --- episode timeline (build-once strip; static, independent of the scrub) --------------------
_header("Episode timeline", "timeline")
st.plotly_chart(timeline_figure(episode_timeline(ctx)), width="stretch")
st.caption(NEWS2_PARTIAL_LABEL)

# --- anticipation: risk waterline, then forecast cone — stacked full width --------------------
_header(DISPLAY_NAMES["waterline"], "waterline")
st.plotly_chart(waterline_figure(patient.t_min, ctx.risk, ctx.threshold, aegis_idx=ctx.aegis_idx),
                width="stretch")

# --- history-as-prior (R1): additive, full width below the waterline — the live signal is untouched
_header(DISPLAY_NAMES["history"], "history")
hz = _hazard()
st.plotly_chart(hazard_figure(hz, focus_density=float(sum(patient.theograph.values()))),
                width="stretch")
st.caption(f"Hazard ratio {hz.hazard_ratio:.2f} per care event "
           f"(95% CI {hz.hr_ci[0]:.2f}–{hz.hr_ci[1]:.2f}); concordance {hz.c_index:.2f}; "
           f"log-rank p {hz.logrank_p:.3f}. Descriptive association, not predictive lift.")

# --- CADUCEUS (R3a.2): the mechanism behind the silent window — additive, descriptive only --------
# Guarded: the selector allows any escalator, but not all carry a decoupling onset.
try:
    d = decoupling_onset(patient)
except ValueError:
    d = None
if d is not None:
    _header(DISPLAY_NAMES["caduceus"], "caduceus")
    st.plotly_chart(
        coherence_figure(patient.t_min, d.coherence, d.onset_min, aegis_min=ctx.fire.aegis_min),
        width="stretch",
    )
    st.caption("Mechanism shown in hindsight — why the deterioration is silent; "
               "the early warning is still where STYX alerts.")

_header(DISPLAY_NAMES["cone"], "cone")
show_ghost = st.checkbox("Hindsight forecast (forecast at early warning)", value=True)
if explain_all:
    g = EXPLAINERS["ghost"]
    st.caption(f"Hindsight forecast — {g.what}")
st.plotly_chart(
    cone_figure(patient.t_min, ctx.risk, frame.cone, THRESHOLDS.risk_escalation,
                now_idx=now_idx, ghost=ctx.ghost if show_ghost else None),
    width="stretch",
)

# --- CALLIOPE: headline always; contributors only when they still sum to the risk -------------
_header(DISPLAY_NAMES["calliope"], "calliope")
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

st.caption(footer_text())
