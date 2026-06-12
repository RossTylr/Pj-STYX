"""(6k) Cards by ward — the pid-derived ward split, the two-label-set preset config, and the
rendered 3-box deck (AppTest arm).

Presentation-only by construction: ``ward_of`` reads nothing but the pid, so the pipeline
digest (tests/test_baseline.py) cannot move. The drill-through buttons are asserted by key
presence, never clicked — ``st.switch_page`` is unsupported under single-file ``AppTest``
(the canonical clock-carry proof lives in tests/test_milestone.py, seeding the patient page).
"""

from streamlit.testing.v1 import AppTest

from styx.config import WARD_COUNT
from styx.cohort import ward_of
from styx.explain import WARD_LABEL_PRESETS, WARD_PRESET_NAMES
from styx.synth import Archetype, build_cohort

_WARD = "app/pages/02_ward.py"


def test_ward_of_partitions_cohort() -> None:
    # Every pid lands in a valid ward, every ward is non-empty, and the hero (the silent case,
    # pid 0) renders in box 0 — the demo's first column.
    cohort = build_cohort(seed=42)
    wards = [ward_of(p.pid) for p in cohort.patients]
    assert set(wards) == set(range(WARD_COUNT))
    assert ward_of(cohort.silent_case().pid) == 0


def test_preset_maps_closed() -> None:
    # The two preset maps share one closed key set; NHS is first (the selector default by dict
    # order); each preset carries exactly one plain label per ward index.
    assert set(WARD_LABEL_PRESETS) == set(WARD_PRESET_NAMES)
    assert next(iter(WARD_PRESET_NAMES)) == "nhs_hah"
    for preset, labels in WARD_LABEL_PRESETS.items():
        assert len(labels) == WARD_COUNT, f"{preset}: one label per ward index"
        for label in labels:
            assert label.strip() and "_" not in label, f"raw label in {preset}: {label!r}"


def _markdown_blob(at: AppTest) -> str:
    return " ".join(md.value for md in at.markdown)


def test_ward_page_renders_three_boxes() -> None:
    # Default run: the NHS preset labels head the three boxes; no table, no chart — the deck
    # IS the board.
    at = AppTest.from_file(_WARD, default_timeout=90).run()
    assert not at.exception
    assert len(at.get("dataframe")) == 0 and len(at.get("plotly_chart")) == 0
    blob = _markdown_blob(at)
    assert all(label in blob for label in WARD_LABEL_PRESETS["nhs_hah"])
    assert not any(label in blob for label in WARD_LABEL_PRESETS["role3"])


def test_preset_flip_relabels_the_boxes() -> None:
    # Flipping the setting preset relabels the boxes over the same cohort — nothing else moves.
    at = AppTest.from_file(_WARD, default_timeout=90)
    at.session_state["ward_preset"] = "role3"
    at.run()
    assert not at.exception
    blob = _markdown_blob(at)
    assert all(label in blob for label in WARD_LABEL_PRESETS["role3"])
    assert not any(label in blob for label in WARD_LABEL_PRESETS["nhs_hah"])


def test_drill_buttons_cover_escalators_only() -> None:
    # One drill-through per non-stable card (the patient page's selector lists escalators only;
    # a stable pid in ``patient_pick`` would be silently reset to the default escalator).
    at = AppTest.from_file(_WARD, default_timeout=90).run()
    keys = {b.key for b in at.button if b.key and b.key.startswith("open_")}
    cohort = build_cohort(seed=42)
    escalators = {f"open_{p.pid}" for p in cohort.patients if p.archetype is not Archetype.STABLE}
    assert keys == escalators
    assert "open_0" in keys  # the hero card drills through


def test_drill_click_sets_target_without_touching_the_clock_widget() -> None:
    # Regression: ``_drill`` must never assign ``scrub_pos`` — writing a widget key after the
    # slider is instantiated raises StreamlitAPIException on a real click. The click here must
    # get all the way to ``st.switch_page`` (unsupported under single-file AppTest — that one
    # expected failure is tolerated) with the target pid set and the clock value untouched.
    at = AppTest.from_file(_WARD, default_timeout=90).run()
    pos = at.session_state["scrub_pos"]
    next(b for b in at.button if b.key == "open_0").click()
    at.run()
    assert [e for e in at.exception if "Could not find page" not in e.message] == []
    assert at.session_state["patient_pick"] == 0
    assert at.session_state["scrub_pid"] == 0
    assert at.session_state["scrub_pos"] == pos  # carried by the shared key, never reassigned
