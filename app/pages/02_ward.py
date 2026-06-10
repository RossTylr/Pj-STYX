"""Ward board (STYX cohort triage) — F6 risk-ranked board + F10 ECHO, on the shared replay clock.

LYR-1: a thin client. Every row comes from ``styx.cohort`` (one ``ward_frame`` per scrub); the ECHO
figure from a ``styx.viz`` pure builder; every explainer line from ``styx.explain``. This page only
arranges, toggles disclosure, and renders — it computes nothing. The clock is the *same* one the
patient page scrubs (shared ``scrub_pos``), so a click drills straight through at the same moment.
"""

import streamlit as st

from styx.cohort import build_cohort_context, ward_frame
from styx.cohort.echo import echo_neighbours
from styx.explain import ARCHETYPE_PATTERNS, DISPLAY_NAMES, ETA_BANDS, EXPLAINERS, OBS_AGE_TEMPLATE
from styx.readouts import eta_ordinal, footer_text, sim_clock, styx_index
from styx.synth import build_cohort
from styx.viz import palette as pal
from styx.viz.echo import echo_figure

st.set_page_config(page_title="STYX — ward", layout="wide")
st.warning(
    "Demo mode: **replay of synthetic data** — no real patient data, not a live deployment.",
    icon="⚠️",
)

TOP_N = 5  # focus mode keeps the watchlist + this many of the soonest-to-escalate


@st.cache_resource
def _cctx():
    return build_cohort_context(build_cohort(seed=42))


cctx = _cctx()

# --- shared replay clock (same key the patient page scrubs) ------------------------------------
default_pos = cctx.indices.index(cctx.default_idx)
if "scrub_pos" not in st.session_state:
    st.session_state["scrub_pos"] = default_pos

st.sidebar.markdown("**Replay clock**")
if st.sidebar.button("Silent window", help="the cohort's silent-window frame"):
    st.session_state["scrub_pos"] = default_pos
focus_mode = st.sidebar.toggle("Focus mode", value=False,
                               help="Collapse to the watchlist + the soonest-to-escalate.")
explain_all = st.sidebar.toggle("Explain this page", value=False,
                                help="Show a plain what / how / why under every panel.")


def _clock_label(i: int) -> str:
    return f"{int(cctx.t_min[cctx.indices[i]])} min"


pos = st.sidebar.select_slider("clock", options=range(len(cctx.indices)), key="scrub_pos",
                               format_func=_clock_label, label_visibility="collapsed")
now_idx = cctx.indices[pos]
rows = ward_frame(cctx, now_idx)


def _header(title: str, cid: str) -> None:
    """A panel title with an ⓘ popover (and an inline card when 'Explain this page' is on)."""
    a, b = st.columns([9, 1])
    a.markdown(f"#### {title}")
    e = EXPLAINERS[cid]
    with b, st.popover("ⓘ"):
        st.markdown(f"**What** — {e.what}\n\n**How** — {e.how}\n\n**Why** — {e.why}")
    if explain_all:
        st.info(f"**What** {e.what}\n\n**How** {e.how}\n\n**Why** {e.why}")


def _eta_label(r) -> str:
    """The ordinal time-to-escalation band (6i) — never a hard minute (UQ-1). A low-confidence
    ETA (only the cone's upper edge crosses) is shown open-ended with a leading ``≥``, not a
    parenthetical."""
    if r.status == "escalated":
        return "threshold crossed"
    if r.status == "no-forecast":
        return "—"
    band = ETA_BANDS[eta_ordinal(r.eta_soonest_min)]
    return band if r.eta_confident else f"≥ {band}"


# Watch-flags: one source for the (WardRow attr → wording) mapping, rendered two ways below.
_FLAGS: tuple[tuple[str, str], ...] = (
    ("silent_but_rising", "silent-but-rising"),
    ("quietest", "quietest"),
    ("new_low_history", "new low-history"),
)


def _active_flags(r) -> list[tuple[str, str]]:
    return [(key, label) for key, label in _FLAGS if getattr(r, key)]


def _flag_badges(r) -> str:
    """Text pill badges (6l): the flag *words* carry the meaning, the badge colour (from the shared
    palette) is a redundant cue only — no emoji, no state by hue alone."""
    return " ".join(
        f":{pal.WARD_FLAG_BADGE[key]}-background[{label}]" for key, label in _active_flags(r)
    )


def _flag_text(r) -> str:
    """Plain-text flags for the dataframe (which renders cells as text, not markdown)."""
    return " · ".join(label for _, label in _active_flags(r))


def _drill(r) -> None:
    """Click-through → the patient page at the SAME clock t. Setting scrub_pid to the target first
    means the patient page's reset branch (``scrub_pid != pid``) does not fire — t is carried."""
    if st.button(f"Open patient {r.pid} →", key=f"open_{r.pid}"):
        st.session_state["patient_pick"] = r.pid  # drive the patient page's selectbox
        st.session_state["scrub_pid"] = r.pid  # match → its reset branch is skipped
        st.session_state["scrub_pos"] = pos
        st.switch_page("pages/01_patient.py")


st.title("Ward board")
st.caption(f"Cohort {OBS_AGE_TEMPLATE.format(clock=sim_clock(cctx.t_min[now_idx]))} · "
           f"{len(rows)} patients")

# --- watchlist: the silent-but-rising patients a threshold board would show green --------------
watch = [r for r in rows if r.silent_but_rising]
_header(f"Watchlist — silent but rising ({len(watch)})", "watchlist")
if not watch:
    st.caption("No silent risers at this frame.")
for r in watch[: (TOP_N if focus_mode else len(watch))]:
    c1, c2, c3, c4 = st.columns([2, 3, 4, 3])
    c1.markdown(f"**patient {r.pid}**")
    c2.markdown(f"Pattern: {ARCHETYPE_PATTERNS[r.archetype]}")
    c3.markdown(f"STYX {styx_index(r.risk_now)} · ETA {_eta_label(r)}  \n{_flag_badges(r)}")
    with c4:
        _drill(r)

# --- the full triage board (ranked by soonest-to-escalate) ------------------------------------
at_risk = [r for r in rows if r.status in ("escalated", "escalating")]
board = (at_risk[:TOP_N] if focus_mode else rows)
_header("Triage board — ranked by time-to-escalation", "ward_board")
st.caption("Focus mode hides the stable bulk." if focus_mode
           else "Ranked: over-the-line → escalating (soonest ETA) → no forecast.")
st.dataframe(
    {
        "patient": [r.pid for r in board],
        "pattern": [ARCHETYPE_PATTERNS[r.archetype] for r in board],
        "status": [r.status for r in board],
        "STYX": [styx_index(r.risk_now) for r in board],
        "time-to-escalation": [_eta_label(r) for r in board],
        "flags": [_flag_text(r) for r in board],
    },
    width="stretch", hide_index=True,
)

# --- ECHO: similar past trajectories for a chosen patient (grounding, not a forecast) ----------
_header(DISPLAY_NAMES["echo"], "echo")
focus_pid = st.selectbox("Focus patient", [r.pid for r in at_risk] or [r.pid for r in rows],
                         format_func=lambda i: f"patient {i}")
neighbours = echo_neighbours(cctx, focus_pid, now_idx)
st.caption("Nearest synthetic trajectories by shape · "
           + " · ".join(f"patient {n.pid} ({n.outcome})" for n in neighbours))
st.plotly_chart(echo_figure(cctx, focus_pid, neighbours, now_idx), width="stretch")

st.caption(footer_text())
