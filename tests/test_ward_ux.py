"""(ward-ux-p0) Ward-card UX invariants — the AppTest oracle for the P0 hardening slice.

Deterministic (seed=42), content/markup only (AppTest sees the element tree, not rendered CSS — the
P0-1a wrapping fix is checked at the visual gate, not here). Enforces:
  * P0-1 every rendered state label ∈ the approved short set; no soft hyphen anywhere.
  * P0-2 each card's SpO₂ token is a percentage (``SpO₂ 91%``); zero bare ``SpO₂ <0-3>`` across the app.
  * P0-3 on a flagged card the STYX-verdict element precedes the demoted NEWS2 line in DOM order.
"""

from __future__ import annotations

import re

from streamlit.testing.v1 import AppTest

from styx.viz import board

_WARD = "app/pages/02_ward.py"
_PATIENT = "app/pages/01_patient.py"

_STATE = re.compile(r'class="[^"]*\bstyx-state\b[^"]*">([^<]+)<')
_SPO2_OK = re.compile(r"SpO.? ?\d{2,3}%")
_SPO2_BARE = re.compile(r"SpO.? ?[0-3]\b")
_SOFT_HYPHEN = "­"


def _markdown(at: AppTest) -> list[str]:
    return [m.value for m in at.markdown]


def _strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html)


def _ward() -> AppTest:
    at = AppTest.from_file(_WARD, default_timeout=90).run()
    assert not at.exception
    return at


# --- P0-1: approved state vocabulary, break-safe ----------------------------------------------

def test_every_state_label_is_approved() -> None:
    blob = " ".join(_markdown(_ward()))
    labels = set(_STATE.findall(blob))
    assert labels, "no styx-state labels rendered — the verdict/badge markers are missing"
    assert labels <= board.APPROVED_STATES, f"off-vocabulary state label(s): {labels - board.APPROVED_STATES}"


def test_no_soft_hyphen_in_rendered_board() -> None:
    assert _SOFT_HYPHEN not in " ".join(_markdown(_ward()))


# --- P0-2: SpO₂ disambiguated to a percentage -------------------------------------------------

def test_spo2_renders_as_a_percentage_on_every_card() -> None:
    cards = [_strip_tags(m) for m in _markdown(_ward()) if "styx-card-v" in m]
    assert cards, "no patient cards rendered"
    for card in cards:
        assert _SPO2_OK.search(card), f"card has no SpO₂ percentage token: {card[:120]!r}"


def test_no_bare_spo2_subscore_across_the_app() -> None:
    # The unsafe `SpO₂ 1` / `SpO₂ 2` (reads as a 1–2% saturation) must not appear on either page.
    for page in (_WARD, _PATIENT):
        at = AppTest.from_file(page, default_timeout=90)
        if page == _PATIENT:
            at.session_state["patient_pick"] = 0
        at.run()
        assert not at.exception
        text = _strip_tags(" ".join(m.value for m in at.markdown))
        hit = _SPO2_BARE.search(text)
        assert hit is None, f"bare SpO₂ sub-score {hit.group()!r} leaked into {page}"


# --- P0-3: flagged card leads with the STYX verdict, NEWS2 demoted -----------------------------

def test_flagged_card_verdict_precedes_news2() -> None:
    # The silent case (pid 0) is flagged at the default frame: its verdict element must come before
    # the muted NEWS2 line, which reads as a below-trigger counterpoint.
    card = next(m for m in _markdown(_ward()) if "Bed 0 ·" in m)
    assert "styx-verdict" in card and "styx-news2-foot" in card
    assert card.index("styx-verdict") < card.index("styx-news2-foot")
    assert "deteriorating — silent" in card  # the STYX verdict is the headline
    assert "below trigger" in card  # NEWS2 demoted to a counterpoint
