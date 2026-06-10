"""No raw archetype enum in rendered output (S5.6 / 6g) — the analogue of ``test_vocabulary_is_closed``.

Boards and the patient page must show the lay "Pattern: …" wording, never the raw archetype enum.
We drive the real pages via ``AppTest`` and scan everything they render for the snake_case raw
tokens (the form that was previously shown in backticks). Evidence from the rendered app itself.
"""

from streamlit.testing.v1 import AppTest

from styx.explain import ARCHETYPE_PATTERNS
from styx.synth import Archetype

_WARD = "app/pages/02_ward.py"
_PATIENT = "app/pages/01_patient.py"

#: Raw enum forms that must never survive into rendered text — those NOT contained in their own lay
#: label (so "coupled"/"stable", which the fuller phrases legitimately reuse, are not false positives).
_LEAK_TOKENS = [a.value for a in Archetype if a.value not in ARCHETYPE_PATTERNS[a.value]]


def _rendered_text(at) -> str:
    parts: list[str] = []
    for coll in (at.markdown, at.caption, at.title, at.header, at.subheader):
        parts += [el.value for el in coll]
    for m in at.metric:
        parts += [str(m.label), str(m.value)]
    for df in at.get("dataframe"):
        parts.append(df.value.to_string())
    return " ".join(parts)


def test_leak_tokens_are_the_snake_case_enums() -> None:
    # Guard the guard: the set we forbid must at least include the snake_case archetype.
    assert "silent_hypoxia" in _LEAK_TOKENS


def test_patient_page_shows_pattern_not_raw_enum() -> None:
    pt = AppTest.from_file(_PATIENT, default_timeout=90)
    pt.session_state["patient_pick"] = 0
    pt.run()
    assert not pt.exception
    blob = _rendered_text(pt)
    assert "Pattern:" in blob  # the lay reframe is shown
    for tok in _LEAK_TOKENS:
        assert tok not in blob, f"raw archetype enum {tok!r} leaked into the patient page"


def test_ward_page_shows_pattern_not_raw_enum() -> None:
    at = AppTest.from_file(_WARD, default_timeout=90).run()
    assert not at.exception
    blob = _rendered_text(at)
    for tok in _LEAK_TOKENS:
        assert tok not in blob, f"raw archetype enum {tok!r} leaked into the ward board"
