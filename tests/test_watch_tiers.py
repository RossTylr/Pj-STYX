"""Watchlist urgency tiers (6e) — the alert-fatigue fix on the ward board.

The flat silent-but-rising list is split into three urgency tiers (review now / this hour / watch),
classified purely over existing signals (status, early-warning flag, ordinal ETA band) — no new
score, so the pipeline digest is untouched by construction (the sentinel in test_baseline holds).
Four guarantees here: the criteria map as specified, the default-frame split is not degenerate
(a relabel that lands everyone in one tier fixes nothing), the tiering is deterministic (DET-1),
and the rendered page shows labels + criteria, never raw tier keys.
"""

from streamlit.testing.v1 import AppTest

from styx.cohort import WATCH_TIERS, WardRow, build_cohort_context, ward_frame, watch_tier
from styx.explain import WATCH_TIER_CRITERIA, WATCH_TIER_LABELS
from styx.synth import build_cohort

_WARD = "app/pages/02_ward.py"


def _row(status: str, eta: float | None, silent: bool = True) -> WardRow:
    # watch_tier reads only status / eta_soonest_min / silent_but_rising; the rest is scaffolding.
    return WardRow(0, "silent_hypoxia", status, 0.4, eta, eta, eta is not None, silent, False, False)


def test_tier_criteria_mapping() -> None:
    # The escalated clause is unsatisfiable within the watchlist (risk below the line by
    # membership) but the function must still answer honestly for any row at any clock.
    assert watch_tier(_row("escalated", None, silent=False)) == "review_now"
    assert watch_tier(_row("escalating", 10.0)) == "review_now"  # ETA band < 30 min
    assert watch_tier(_row("escalating", 45.0)) == "this_hour"  # early-warning + 30–60 min
    assert watch_tier(_row("escalating", 90.0)) == "watch"  # ETA beyond the hour
    assert watch_tier(_row("no-forecast", None)) == "watch"  # no projected escalation
    for case in (("escalated", None), ("escalating", 10.0), ("escalating", 45.0),
                 ("escalating", 90.0), ("no-forecast", None)):
        assert watch_tier(_row(*case)) in WATCH_TIERS  # closed over the tier vocabulary


def test_default_frame_distribution_not_degenerate() -> None:
    # The F-02 fix only works if review-now is a manageable set and the bulk sits in watch —
    # all three tiers populated at the silent-window default frame, summing to the watchlist.
    cctx = build_cohort_context(build_cohort(seed=42))
    watch = [r for r in ward_frame(cctx, cctx.default_idx) if r.silent_but_rising]
    assert len(watch) == 21
    counts = {t: sum(1 for r in watch if watch_tier(r) == t) for t in WATCH_TIERS}
    assert sum(counts.values()) == len(watch)
    assert all(counts[t] > 0 for t in WATCH_TIERS), f"degenerate tier split: {counts}"
    assert counts["review_now"] < counts["watch"]  # triage head stays short, bulk stays quiet


def test_tiering_deterministic() -> None:
    # DET-1 — same seed → identical (pid, tier) assignment across independent builds.
    def tiers() -> list[tuple[int, str]]:
        cctx = build_cohort_context(build_cohort(seed=42))
        return [(r.pid, watch_tier(r)) for r in ward_frame(cctx, cctx.default_idx)]

    assert tiers() == tiers()


def test_tier_keys_closed_and_labels_plain() -> None:
    # One label and one criteria caption per tier key; rendered copy never carries a raw key.
    assert set(WATCH_TIER_LABELS) == set(WATCH_TIERS) == set(WATCH_TIER_CRITERIA)
    for text in list(WATCH_TIER_LABELS.values()) + list(WATCH_TIER_CRITERIA.values()):
        assert text.strip(), "empty tier copy"
        assert "_" not in text, f"raw tier key leaked into copy: {text!r}"


def test_ward_page_renders_tiers() -> None:
    # The rendered board shows all three tier labels and their criteria (transparency standard).
    at = AppTest.from_file(_WARD, default_timeout=90).run()
    assert not at.exception
    blob = " ".join([el.value for el in at.markdown] + [el.value for el in at.caption])
    for t in WATCH_TIERS:
        assert WATCH_TIER_LABELS[t] in blob, f"tier label missing from ward page: {t}"
        assert WATCH_TIER_CRITERIA[t] in blob, f"tier criteria missing from ward page: {t}"
