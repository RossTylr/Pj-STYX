"""Ward board (STYX cohort triage) — the F6 risk-ranked board on the shared replay clock.

LYR-1: a thin client. Every row comes from ``styx.cohort`` (one ``ward_frame`` per scrub); every
explainer line from ``styx.explain``. This page only arranges, toggles disclosure, and renders —
it computes nothing. The clock is the *same* one the patient page scrubs (shared ``scrub_pos``),
so a click drills straight through at the same moment.
"""

import math

import streamlit as st

from styx.clinical_basis import NEWS2_FOOTNOTE
from styx.cohort import build_cohort_context, ward_frame, ward_of
from styx.config import WARD_COUNT
from styx.explain import (
    ETA_BANDS,
    EXPLAINERS,
    OBS_AGE_TEMPLATE,
    WARD_LABEL_PRESETS,
    WARD_PRESET_NAMES,
)
from styx.readouts import eta_ordinal, footer_text, sim_clock
from styx.synth import Archetype, build_cohort
from styx.viz import board

st.set_page_config(page_title="STYX — ward", page_icon="docs/Pj-STYX.jpeg", layout="wide")
st.logo("docs/Pj-STYX.jpeg", size="large")  # (6h) app-wide brand mark above the sidebar nav
st.markdown(  # (6h+) full-width brand mark in the sidebar banner; gone when the sidebar is closed
    "<style>"
    "[data-testid='stSidebarHeader']{height:auto!important;display:block!important;"
    "position:relative!important;padding:.5rem!important;}"
    "[data-testid='stSidebarCollapseButton']{position:absolute!important;"
    "top:.35rem!important;right:.35rem!important;z-index:2!important;}"
    "[data-testid='stSidebarHeader'] [data-testid='stLogoLink']{width:100%!important;"
    "height:auto!important;max-height:none!important;display:block!important;}"
    "[data-testid='stSidebarLogo']{width:100%!important;height:auto!important;"
    "max-height:none!important;}"
    "section[data-testid='stSidebar'][aria-expanded='false'] [data-testid='stSidebarLogo']"
    "{display:none!important;}"
    "</style>",
    unsafe_allow_html=True,
)
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


_patients = {p.pid: p for p in cctx.cohort.patients}


def _news2(r) -> board.News2Now:
    """The patient's NEWS2 standing at the clock (read-only slice of the existing comparator)."""
    return board.news2_now(_patients[r.pid], now_idx)


def _spark(r) -> tuple[str, str]:
    """(trend arrow, inline-SVG sparkline) from the STYX risk history up to the clock — STYX accent,
    never a band signal. Down-sampled to keep the SVG small; band colour is reserved for NEWS2."""
    hist = cctx.risk[r.pid][: now_idx + 1]
    step = max(1, len(hist) // 24)
    pts = [float(v) for v in hist[::step]]
    return board.trend_arrow(pts), board.sparkline_svg(pts)


def _sub_line(r) -> str:
    """The card's sub-line (6): for a flagged bed, the lead-time before NEWS2 would escalate (a band,
    never an exact minute — UQ-1); for a calm bed, the STYX/NEWS2 agreement. Never a codename."""
    if not r.silent_but_rising:
        return "STYX and NEWS2 agree"
    if r.status == "no-forecast":
        return "rising — no NEWS2 escalation projected yet"
    band = ETA_BANDS[eta_ordinal(r.eta_soonest_min)]
    return f"~{band if r.eta_confident else '≥ ' + band} before NEWS2 would escalate"


def _rail_item(r, n2: board.News2Now):
    """Attention-rail entry (pid, band, short reason) for a flagged bed, else None."""
    if n2.band == "high":
        reason = "high NEWS2"
    elif n2.single_red:
        reason = "single red score"
    elif n2.band == "med":
        reason = "medium NEWS2"
    elif r.silent_but_rising:
        reason = "early signal"
    else:
        return None
    return r.pid, n2.band, reason


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


st.markdown(board.BOARD_CSS, unsafe_allow_html=True)  # one scoped style block for the whole board
st.title("Ward board")
st.caption(f"Cohort {OBS_AGE_TEMPLATE.format(clock=sim_clock(cctx.t_min[now_idx]))} · "
           f"{len(rows)} patients")

# --- (6k) routine board: an attention rail, then three full-width bays of bed cards ------------
# The bays read as physical bed positions: every bed visible, ordered by pid (bed number), never
# urgency-ranked. The NEWS2 band is each card's primary signal; the STYX trend rides the sparkline;
# the attention rail above carries the triage summary the unranked grid no longer provides.
_n2 = {r.pid: _news2(r) for r in rows}  # one NEWS2 standing per bed at the clock (reused below)
# Each bay sorts its beds by pid and pads to a uniform capacity (sized to the largest bay).
boxes = {w: sorted((r for r in rows if ward_of(r.pid) == w), key=lambda r: r.pid)
         for w in range(WARD_COUNT)}
bay_rows = max(math.ceil(len(b) / board.BAY_COLS) for b in boxes.values())
bay_capacity = bay_rows * board.BAY_COLS


def _bed(cell, r) -> None:
    """One occupied bed (P0-3): the STYX verdict leads, NEWS2 recedes; real SpO₂ % shown, never a
    bare sub-score (P0-2). Then the drill button (escalators only)."""
    with cell:
        arrow, spark = _spark(r)
        p = _patients[r.pid]
        flagged = r.silent_but_rising
        vitals = [board.vital_reading(p, "SpO2", now_idx, label="SpO₂", unit="%")]
        if flagged:  # the flagged card carries respiratory effort alongside saturation (Bed 6)
            vitals.append(board.vital_reading(p, "RR", now_idx, label="RR", unit=""))
        st.markdown(
            board.card_html(r.pid, ward_labels[ward_of(r.pid)], _n2[r.pid],
                            flagged=flagged, receding=(arrow == "↓"), vitals=vitals,
                            sub_line=_sub_line(r), arrow=arrow, sparkline=spark),
            unsafe_allow_html=True,
        )
        if r.archetype != Archetype.STABLE.value:  # the patient page lists escalators only
            _drill(r)


_header("Attention rail — flagged beds across all bays", "ward_board")
rail = [item for r in rows if (item := _rail_item(r, _n2[r.pid])) is not None]
st.markdown(board.attention_rail_html(rail), unsafe_allow_html=True)

for w in range(WARD_COUNT):
    box = boxes[w]
    bands = [_n2[r.pid] for r in box]
    rollup = board.Rollup(
        occupancy=len(box),
        high=sum(n2.band == "high" for n2 in bands),
        med=sum(n2.band == "med" for n2 in bands),
        max_news2=max((n2.aggregate for n2 in bands), default=0),
    )
    with st.container(border=True):
        st.markdown(board.banner_html(ward_labels[w], rollup), unsafe_allow_html=True)
        beds = list(box) + [None] * (bay_capacity - len(box))  # vacant slots pad the fixed grid
        for start in range(0, bay_capacity, board.BAY_COLS):
            cells = st.columns(board.BAY_COLS)
            for cell, r in zip(cells, beds[start:start + board.BAY_COLS]):
                if r is None:
                    cell.markdown(board.vacant_tile_html(), unsafe_allow_html=True)
                else:
                    _bed(cell, r)

st.caption(footer_text())
try:
    st.page_link("pages/04_clinical_basis.py", label=NEWS2_FOOTNOTE)
except KeyError:
    # Single-file AppTest registry has no sibling pages (same limitation test_ward_boxes notes
    # for st.switch_page) — fall back to the same line as plain text.
    st.caption(NEWS2_FOOTNOTE)
