"""Ward board (STYX cohort triage) — the F6 risk-ranked board on the shared replay clock.

LYR-1: a thin client. Every row comes from ``styx.cohort`` (one ``ward_frame`` per scrub); every
explainer line from ``styx.explain``. This page only arranges, toggles disclosure, and renders —
it computes nothing. The clock is the *same* one the patient page scrubs (shared ``scrub_pos``),
so a click drills straight through at the same moment.
"""

import streamlit as st

from styx.cohort import WATCH_TIERS, build_cohort_context, ward_frame, ward_of, watch_tier
from styx.config import WARD_COUNT
from styx.explain import (
    ARCHETYPE_PATTERNS,
    ETA_BANDS,
    EXPLAINERS,
    OBS_AGE_TEMPLATE,
    WARD_LABEL_PRESETS,
    WARD_PRESET_NAMES,
    WATCH_TIER_CRITERIA,
    WATCH_TIER_LABELS,
)
from styx.readouts import eta_ordinal, footer_text, sim_clock, styx_index
from styx.synth import Archetype, build_cohort
from styx.viz import palette as pal

st.set_page_config(page_title="STYX — ward", layout="wide")
st.warning(
    "Demo mode: **replay of synthetic data** — no real patient data, not a live deployment.",
    icon="⚠️",
)

@st.cache_resource
def _cctx():
    return build_cohort_context(build_cohort(seed=42))


cctx = _cctx()

# --- shared replay clock (same key the patient page scrubs) ------------------------------------
# Re-assigning the key each run promotes it from widget-owned to session-owned, so the clock
# survives a page switch (Streamlit drops a widget-owned key whose widget did not render).
default_pos = cctx.indices.index(cctx.default_idx)
st.session_state["scrub_pos"] = st.session_state.get("scrub_pos", default_pos)

st.sidebar.markdown("**Replay clock**")
if st.sidebar.button("Silent window", help="the cohort's silent-window frame"):
    st.session_state["scrub_pos"] = default_pos
explain_all = st.sidebar.toggle("Explain this page", value=False,
                                help="Show a plain what / how / why under every panel.")
# (6k) Setting preset — relabels the three ward boxes only; nothing is re-scored. Dict order
# makes the first preset (NHS hospital-at-home) the default without fighting session state.
preset = st.sidebar.selectbox("Ward labels", list(WARD_PRESET_NAMES), key="ward_preset",
                              format_func=WARD_PRESET_NAMES.__getitem__,
                              help="Deployment setting — changes the box labels, never the data.")
ward_labels = WARD_LABEL_PRESETS[preset]


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


def _drill(r) -> None:
    """Click-through → the patient page at the SAME clock t. Setting scrub_pid to the target first
    means the patient page's reset branch (``scrub_pid != pid``) does not fire — t is carried.
    ``scrub_pos`` is never assigned here: the session-owned promotion at the top of each page
    carries the clock across the switch, and writing a widget key after the widget is
    instantiated raises (StreamlitAPIException)."""
    if st.button(f"Open patient {r.pid} →", key=f"open_{r.pid}"):
        st.session_state["patient_pick"] = r.pid  # drive the patient page's selectbox
        st.session_state["scrub_pid"] = r.pid  # match → its reset branch is skipped
        st.switch_page("pages/01_patient.py")


st.title("Ward board")
st.caption(f"Cohort {OBS_AGE_TEMPLATE.format(clock=sim_clock(cctx.t_min[now_idx]))} · "
           f"{len(rows)} patients")

# --- (6k) cards by ward: three boxes, most urgent first within each — the deck IS the board ----
# (6e) urgency-within: rows keep the ward_frame order (already soonest-first), so the per-tier
# partition inside each box preserves the existing sort — tier groups it, the rank orders it.
_header("Wards — most urgent first", "ward_board")
st.caption(" · ".join(f"{WATCH_TIER_LABELS[t]} — {WATCH_TIER_CRITERIA[t]}" for t in WATCH_TIERS))
hero_pid = cctx.cohort.silent_case().pid  # the demo's silent case — its card carries a border


def _card(r, tier: str) -> None:
    """One patient card: tier badge, pattern, score/ETA/flags (+ drill-through for escalators)."""
    with st.container(border=(r.pid == hero_pid)):
        st.markdown(f"**patient {r.pid}** "
                    f":{pal.WATCH_TIER_BADGE[tier]}-background[{WATCH_TIER_LABELS[tier]}]")
        st.caption(f"Pattern: {ARCHETYPE_PATTERNS[r.archetype]}")
        st.markdown(f"STYX {styx_index(r.risk_now)} · ETA {_eta_label(r)}  \n{_flag_badges(r)}")
        if r.archetype != Archetype.STABLE.value:  # the patient page lists escalators only
            _drill(r)


for w, col in enumerate(st.columns(WARD_COUNT)):
    box = [r for r in rows if ward_of(r.pid) == w]
    tiers = {t: [r for r in box if watch_tier(r) == t] for t in WATCH_TIERS}
    with col, st.container(border=True):
        st.markdown(f"#### {ward_labels[w]}")
        st.caption(f"{len(box)} patients · {len(tiers['review_now'])} review now")
        for t in ("review_now", "this_hour"):
            for r in tiers[t]:
                _card(r, t)
        with st.expander(f"+ {len(tiers['watch'])} watching"):
            for r in tiers["watch"]:
                _card(r, "watch")

st.caption(footer_text())
