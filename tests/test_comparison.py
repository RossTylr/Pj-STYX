"""S7 NEWS2 A/B — the comparison panel's lead is single-sourced, the comparator fair, reveal gated.

Builder-only (LYR-1). Three guarantees: the annotated lead is exactly the early-warning-vs-NEWS2
gap read from the real fire-points (305 min on the silent case — the headline pin, bound by the
SpO₂ ≤91 single-parameter red, the aggregate never reaching 5); the comparator lane is the complete
``styx.readouts.news2_complete`` passed through unchanged (fair NEWS2 — never re-scored or weakened
inside the figure); and no crossing marker or lead bracket appears before the replay clock has
reached it (rule 6).
"""

from __future__ import annotations

import numpy as np

from styx.explain import COMPARISON_LABELS
from styx.frame import build_context
from styx.readouts import NEWS2_TRIGGER, news2_complete, news2_complete_crossing
from styx.synth import build_cohort
from styx.viz.comparison import comparison_figure


def _setup():
    cohort = build_cohort(seed=42)
    patient = cohort.silent_case()
    return patient, build_context(cohort, patient)


def _figure(patient, ctx, now_idx: int | None = None):
    return comparison_figure(
        patient.t_min, ctx.risk, ctx.threshold, news2_complete(patient), NEWS2_TRIGGER,
        aegis_min=ctx.fire.aegis_min, escalation_min=ctx.fire.threshold_min,
        news2_crossing_min=news2_complete_crossing(patient), now_idx=now_idx)


def test_lead_annotation_single_sourced_from_fire_points() -> None:
    patient, ctx = _setup()
    lead = news2_complete_crossing(patient) - ctx.fire.aegis_min
    assert lead == 305.0  # the headline pin: early warning 705 vs NEWS2 1010 (sim-min)
    fig = _figure(patient, ctx)
    texts = [a.text for a in fig.layout.annotations]
    assert COMPARISON_LABELS["lead"].format(hours=lead / 60, minutes=lead) in texts


def test_news2_lane_is_the_readout_unchanged() -> None:
    patient, ctx = _setup()
    fig = _figure(patient, ctx)
    lane = next(tr for tr in fig.data if tr.name == COMPARISON_LABELS["news2_lane"])
    assert np.array_equal(np.asarray(lane.y), news2_complete(patient))


def test_nothing_revealed_before_the_clock_reaches_it() -> None:
    patient, ctx = _setup()
    pre_i = int(np.searchsorted(patient.t_min, ctx.fire.aegis_min)) - 1
    fig = _figure(patient, ctx, now_idx=pre_i)
    names = {tr.name for tr in fig.data}
    assert COMPARISON_LABELS["escalation"] not in names
    assert COMPARISON_LABELS["news2_fires"] not in names
    lead_prefix = COMPARISON_LABELS["lead"].split("{")[0]
    assert all(lead_prefix not in (a.text or "") for a in fig.layout.annotations)
    lane = next(tr for tr in fig.data if tr.name == COMPARISON_LABELS["styx_lane"])
    assert float(np.asarray(lane.x).max()) == float(patient.t_min[pre_i])
