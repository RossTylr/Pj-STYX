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

from styx.cohort import build_cohort_context, ward_frame, ward_of
from styx.explain import WARD_LABEL_PRESETS
from styx.synth import build_cohort
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


# === P1 (ward-ux-p1) =========================================================================

_SUB = re.compile(r'class="styx-sub">([^<]+)<')
_BANNED = re.compile(r"no .*projected|nothing|not .*yet", re.I)


def _model():
    """The seed=42 board at the default frame + per-bed NEWS2 — the oracle's source of truth."""
    cctx = build_cohort_context(build_cohort(seed=42))
    rows = ward_frame(cctx, cctx.default_idx)
    pats = {p.pid: p for p in cctx.cohort.patients}
    n2 = {r.pid: board.news2_now(pats[r.pid], cctx.default_idx) for r in rows}
    return cctx, rows, n2


def _flagged_cards(md: list[str]) -> list[str]:
    return [m for m in md if "styx-card-v" in m and "deteriorating — silent" in m]


# --- §A bay-header propagation ----------------------------------------------------------------

def test_no_bay_reads_steady_with_a_flagged_bed() -> None:
    _, rows, n2 = _model()
    md = _markdown(_ward())
    banners = [m for m in md if 'class="styx-banner ' in m]
    assert len(banners) == 3
    for w, label in enumerate(WARD_LABEL_PRESETS["nhs_hah"]):
        # the disjoint definition the bay banner + §E overview share: flagged AND NEWS2 still low
        flagged = sum(r.silent_but_rising and n2[r.pid].band == "low"
                      for r in rows if ward_of(r.pid) == w)
        banner = next(b for b in banners if label in b)
        assert f"{flagged} early signal" in _strip_tags(banner)  # count == flagged beds in the bay
        if flagged:  # hard invariant: a bay with a flagged bed can never read STEADY
            assert "STEADY" not in banner


# --- §C verdict-copy contract -----------------------------------------------------------------

def test_flagged_subtext_obeys_the_copy_contract() -> None:
    flagged = _flagged_cards(_markdown(_ward()))
    assert flagged
    subs = [_SUB.search(m).group(1) for m in flagged if _SUB.search(m)]
    assert len(subs) == len(flagged), "every flagged card must carry a subtext"
    for s in subs:
        assert s == "rising — flagged ahead of NEWS2" or re.fullmatch(r"~.+ ahead of NEWS2", s), s
        assert not _BANNED.search(s), f"banned negation in subtext: {s!r}"


# --- §D demoted NEWS2 footer ------------------------------------------------------------------

def test_every_flagged_card_keeps_the_news2_footer() -> None:
    for card in _flagged_cards(_markdown(_ward())):
        assert "styx-news2-foot" in card and "below trigger" in card  # NEWS2 < trigger on all flagged


# --- §E overview strip + ranked worklist ------------------------------------------------------

def test_overview_and_worklist_replace_the_flat_rail() -> None:
    _, rows, n2 = _model()
    critical = sum(n2[r.pid].band != "low" for r in rows)
    flagged = [r for r in rows if r.silent_but_rising and n2[r.pid].band == "low"]
    stable = len(rows) - critical - len(flagged)
    md = _markdown(_ward())
    assert not any("styx-rail" in m for m in md), "the flat 21-pill rail must be gone"
    ov = _strip_tags(next(m for m in md if "styx-ov-cohort" in m and "<style>" not in m))
    assert "50 patients" in ov and f"{len(flagged)}" in ov and f"{stable}" in ov
    assert critical + len(flagged) + stable == 50  # partition covers the cohort

    ranked = sorted(flagged, key=lambda r: board.review_rank(
        critical=False, eta_soonest_min=r.eta_soonest_min, risk_now=r.risk_now, pid=r.pid))
    expected = [r.pid for r in ranked[:6]]
    wl = next(m for m in md if "styx-wl-row" in m and "<style>" not in m)
    got = [int(x) for x in re.findall(r"Bed (\d+)", _strip_tags(wl))]
    assert got == expected, f"worklist mis-ordered: {got} != {expected}"
    assert len(got) <= 6  # capped at N
    assert f"+ {len(flagged) - len(expected)} more in watch" in _strip_tags(wl)


# --- §B3 twins: per-bed fidelity, differentiated by lead-time ---------------------------------

def test_flagged_cards_render_own_records_and_twins_differ() -> None:
    cctx, rows, _ = _model()
    pats = {p.pid: p for p in cctx.cohort.patients}
    idx = cctx.default_idx
    flagged = _flagged_cards(_markdown(_ward()))
    for r in rows:
        if not r.silent_but_rising:
            continue
        card = _strip_tags(next(m for m in flagged if f"Bed {r.pid} ·" in m))
        assert f"{round(float(pats[r.pid].vitals['SpO2'][idx]))}%" in card  # own record, not cross-wired
    vitals = [_SPO2_OK.search(_strip_tags(m)).group(0) for m in flagged]
    assert len(set(vitals)) > 1, "flagged beds must not all render one templated value"
    # The Bed 0 / Bed 6 twins: integer SpO₂ rounds both genuine-94% records to the same vitals line
    # (sub-integer precision deliberately avoided as clinically non-standard — user decision); the
    # differentiation is lead-time, exactly as ward_overview_target.html shows. Pin that mechanism
    # explicitly rather than comparing whole cards (which would pass on copy alone).
    b0 = _strip_tags(next(m for m in flagged if "Bed 0 ·" in m))
    b6 = _strip_tags(next(m for m in flagged if "Bed 6 ·" in m))
    assert _SPO2_OK.search(b0).group(0) == _SPO2_OK.search(b6).group(0)  # same rounded saturation
    assert _SUB.search(next(m for m in flagged if "Bed 0 ·" in m)).group(1) \
        != _SUB.search(next(m for m in flagged if "Bed 6 ·" in m)).group(1)  # differ by lead-time
