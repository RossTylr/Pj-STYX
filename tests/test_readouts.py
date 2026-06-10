"""Pure display-helper unit tests (S5.6) — the index/clock/ETA-band/partial-NEWS2 primitives.

All deterministic (DET-1). The partial-NEWS2 comparator gets a Hard-Rule-6 honesty test: its
escalation trigger must land *after* AEGIS and the absolute breach on the silent case — the A/B
claim ("the UK standard is blind through the window STYX flags") only ships if the data backs it.
"""

import numpy as np

from styx.anticipation import fire_times
from styx.explain import ETA_BANDS
from styx.frame import build_context
from styx.readouts import (
    NEWS2_TRIGGER,
    _hr_score,
    _news2_subscores,
    _rr_score,
    _spo2_scale1_score,
    _temp_score,
    eta_ordinal,
    news2_crossing,
    news2_partial,
    sim_clock,
    styx_index,
)
from styx.synth import build_cohort


def test_styx_index_anchors_and_clamps() -> None:
    assert styx_index(0.0) == 0
    assert styx_index(0.28) == 28
    assert styx_index(1.0) == 100
    assert styx_index(1.5) == 100  # clamp high
    assert styx_index(-0.2) == 0  # clamp low


def test_sim_clock_hhmm() -> None:
    assert sim_clock(0) == "00:00"
    assert sim_clock(540) == "09:00"
    assert sim_clock(750) == "12:30"
    assert sim_clock(1439) == "23:59"


def test_eta_ordinal_bands() -> None:
    assert eta_ordinal(None) == "unclear"
    assert eta_ordinal(10) == "lt30"
    assert eta_ordinal(29.9) == "lt30"
    assert eta_ordinal(30) == "30_60"
    assert eta_ordinal(59) == "30_60"
    assert eta_ordinal(60) == "1_2h"
    assert eta_ordinal(120) == "1_2h"
    assert eta_ordinal(121) == "gt2h"
    for m in (None, 10, 45, 90, 200):  # every result is a known band key
        assert eta_ordinal(m) in ETA_BANDS


def test_news2_scale1_subscore_boundaries() -> None:
    # NEWS2 Scale 1 thresholds, per parameter (the comparator is only honest if these are exact).
    assert list(_spo2_scale1_score(np.array([97.0, 96, 95, 94, 93, 92, 91, 88]))) == [0, 0, 1, 1, 2, 2, 3, 3]
    assert list(_rr_score(np.array([8.0, 9, 12, 20, 21, 24, 25]))) == [3, 1, 0, 0, 2, 2, 3]
    assert list(_hr_score(np.array([40.0, 41, 50, 51, 90, 91, 110, 111, 130, 131]))) == [3, 1, 1, 0, 0, 1, 1, 2, 2, 3]
    assert list(_temp_score(np.array([35.0, 35.1, 36, 36.1, 38, 38.1, 39, 39.1]))) == [3, 1, 1, 0, 0, 1, 1, 2]


def test_news2_partial_determinism() -> None:
    a = build_cohort(seed=42).silent_case()
    b = build_cohort(seed=42).silent_case()
    assert np.array_equal(news2_partial(a), news2_partial(b))  # DET-1


def test_news2_comparator_is_blind_through_the_window() -> None:
    # Hard Rule 6: the partial NEWS2 must not reach its escalation trigger until *after* the breach,
    # and its crossing must land after AEGIS — only then is the "AEGIS beats NEWS2" headline honest.
    cohort = build_cohort(seed=42)
    p = cohort.silent_case()
    ctx = build_context(cohort, p)
    ft = fire_times(cohort, p, ctx.cadence_min, threshold=ctx.threshold)
    cross = news2_crossing(p)

    assert cross is not None
    assert ft.aegis_min is not None and ft.threshold_min is not None
    assert ft.aegis_min < cross  # AEGIS fires first
    assert ft.threshold_min < cross  # NEWS2 escalates only after the absolute breach

    # And it never reaches its trigger anywhere in the pre-breach window (blind through it).
    sub = _news2_subscores(p)
    triggered = (sub.sum(axis=0) >= NEWS2_TRIGGER) | (sub.max(axis=0) >= 3)
    pre_breach = p.t_min < ft.threshold_min
    assert not triggered[pre_breach].any()
