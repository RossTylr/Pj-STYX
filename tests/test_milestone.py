"""Milestone gate — the 10-feature MVP runs end-to-end on the pre-baked scenario.

Drives the whole path: ward board at the silent-window frame → patient-0 surfaces on the watchlist
→ drill into the patient page at the *same* clock t → all ten features {F5,F1,F2,F4,F7,F3,F8,F6,F9,
F10} render → scrub forward and patient-0 climbs the board while AEGIS→forecast→threshold fire in
order. Logic claims are asserted compute-side (``ward_frame`` / ``fire_times``); the Streamlit pages
are driven via ``AppTest`` only for render-without-exception and feature *presence*. F10's evidence
is the retrieval itself (``echo_neighbours``) — its figure left the ward page at 6k but the builder
is retained and scanned (tests/test_no_codename.py), same pattern as ``trajectory_figure``.
"""

from streamlit.testing.v1 import AppTest

from styx.anticipation import fire_times
from styx.cohort import build_cohort_context, ward_frame
from styx.cohort.echo import echo_neighbours
from styx.explain import DISPLAY_NAMES, WARD_LABEL_PRESETS
from styx.synth import build_cohort

_WARD = "app/pages/02_ward.py"
_PATIENT = "app/pages/01_patient.py"
_FWD_IDX = 183  # a forward frame just past patient-0's threshold crossing (sim-min 915)


def _cctx():
    return build_cohort_context(build_cohort(seed=42))


def test_ward_renders_and_patient0_is_on_the_watchlist() -> None:
    cctx = _cctx()
    rows = ward_frame(cctx, cctx.default_idx)
    p0 = next(r for r in rows if r.pid == 0)
    assert p0.silent_but_rising  # the silent-window catch — AEGIS fired, still pre-threshold
    assert p0.status == "escalating" and p0.eta_soonest_min is not None  # banded ETA, no hard minute
    at = AppTest.from_file(_WARD, default_timeout=90).run()
    assert not at.exception
    # 6k: the board is the ward-grouped card deck — no table, no chart on this page.
    assert len(at.get("dataframe")) == 0 and len(at.get("plotly_chart")) == 0
    blob = " ".join(md.value for md in at.markdown)
    assert all(label in blob for label in WARD_LABEL_PRESETS["nhs_hah"])  # F6 — the three boxes
    assert "patient 0" in blob  # the hero card renders


def test_drill_carries_the_clock_into_the_patient_page() -> None:
    cctx = _cctx()
    pos = cctx.indices.index(cctx.default_idx)
    pt = AppTest.from_file(_PATIENT, default_timeout=90)
    pt.session_state["patient_pick"] = 0
    pt.session_state["scrub_pid"] = 0
    pt.session_state["scrub_pos"] = pos
    pt.run()
    assert not pt.exception
    assert pt.session_state["scrub_pos"] == pos  # the reset branch did NOT fire — same t carried


def test_all_ten_features_present() -> None:
    # F5 — the synthetic cohort underpinning everything.
    assert len(build_cohort(seed=42).patients) == 50

    pt = AppTest.from_file(_PATIENT, default_timeout=90)
    pt.session_state["patient_pick"] = 0
    pt.run()
    assert not pt.exception
    # F1 trajectory + F2 cone + F4 waterline + F3 theograph (ribbon + detail strip) = ≥5 charts.
    assert len(pt.get("plotly_chart")) >= 5
    assert any(DISPLAY_NAMES["aegis"] in m.label for m in pt.metric)  # F7 (early-warning lead)
    assert any(DISPLAY_NAMES["calliope"] in md.value for md in pt.markdown)  # F8 (why this score)
    assert any("Hindsight forecast" in cb.label for cb in pt.checkbox)  # F9 (6j: ghost → hindsight)

    at = AppTest.from_file(_WARD, default_timeout=90).run()
    # F6 — the board is the 6k card deck: the three ward boxes render, no table, no chart.
    blob = " ".join(md.value for md in at.markdown)
    assert all(label in blob for label in WARD_LABEL_PRESETS["nhs_hah"])
    assert len(at.get("dataframe")) == 0 and len(at.get("plotly_chart")) == 0
    # F10 retrieval sanity: ECHO returns k look-alikes for patient 0, none of them itself.
    ns = echo_neighbours(_cctx(), 0, 150)
    assert len(ns) == 3 and all(n.pid != 0 for n in ns)


def test_scrub_forward_climbs_the_board_in_anticipation_order() -> None:
    # Compute-side rank semantics — unchanged by 6k: ward_frame order still drives card order
    # within each ward box (the tier partition preserves it).
    cctx = _cctx()
    rank_default = [r.pid for r in ward_frame(cctx, cctx.default_idx)].index(0)
    fwd = ward_frame(cctx, _FWD_IDX)
    rank_fwd = [r.pid for r in fwd].index(0)
    assert rank_fwd < rank_default  # patient 0 rises up the board as it deteriorates
    assert next(r for r in fwd if r.pid == 0).status == "escalated"  # now over the line

    ft = fire_times(cctx.cohort, cctx.cohort.silent_case())
    assert ft.ordered  # AEGIS → forecast → threshold, the dissociation headline (G3) at the milestone
    assert ft.aegis_min < ft.forecast_min < ft.threshold_min
