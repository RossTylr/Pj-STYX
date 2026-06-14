"""Nurse-entered obs + the complete (6-of-7) NEWS2 comparator — fidelity, fairness, routing.

Five guarantees: the nurse obs are step-held at the 4-hourly round and deterministic at seed=42;
they are preserved through the silent window (BP band 0, ACVPU Alert), so the completed score adds
nothing to the partial here; the escalation trigger is the protocol-correct *earliest* of (any
single-param red, aggregate ≥ 5) — and on this scenario the single-param SpO₂ red is load-bearing,
the aggregate never reaching 5; and the obs are comparator-only — the baseline pipeline digest is
bit-identical, the field never leaking into a model path.
"""

from __future__ import annotations

import numpy as np

from styx.config import NURSE_OBS_CADENCE_MIN
from styx.readouts import (
    NEWS2_TRIGGER,
    _news2_complete_subscores,
    news2_complete,
    news2_complete_crossing,
    news2_crossing,
    news2_partial,
)
from styx.synth import build_cohort
from tests.test_baseline import pipeline_digest

#: Re-recorded after Slice A (per-escalator severity + onset jitter) intentionally changed the
#: vital streams + risk scores. nurse_obs are NOT in the digest, so this still proves they stay
#: comparator-only. theograph counts are unchanged (diversity uses an independent generator).
_RECORDED_DIGEST = "c9380e9cf7c134a82f2a45dd15c9769129540eee3c7d5db5aa54dc587860b1d9"


def _silent():
    return build_cohort(seed=42).silent_case()


def test_nurse_obs_deterministic_and_step_held() -> None:
    a = build_cohort(seed=42).silent_case().nurse_obs
    b = build_cohort(seed=42).silent_case().nurse_obs
    assert np.array_equal(a["systolic_bp"], b["systolic_bp"])  # DET-1
    assert np.array_equal(a["acvpu"], b["acvpu"])
    p = _silent()
    dt = int(p.t_min[1] - p.t_min[0])
    step = NURSE_OBS_CADENCE_MIN // dt
    bp = p.nurse_obs["systolic_bp"]
    # step-held: the value is constant within each round window, changing only at round boundaries.
    for start in range(0, len(bp), step):
        block = bp[start:start + step]
        assert np.all(block == block[0])


def test_nurse_obs_preserved_through_the_stay() -> None:
    obs = _silent().nurse_obs
    assert np.all(obs["acvpu"] == 0)  # Alert throughout (any other level would score a red 3)
    assert np.all(obs["systolic_bp"] >= 111)  # NEWS2 BP band 0 — the nurse contribution stays 0


def test_complete_adds_nothing_to_partial_here() -> None:
    p = _silent()
    part, comp = news2_partial(p), news2_complete(p)
    assert np.all(comp >= part)  # the complete score can only add to the partial
    assert np.array_equal(comp, part)  # BP/ACVPU preserved → they add exactly 0 in this scenario


def test_single_param_red_is_load_bearing() -> None:
    # The honest trigger is the *earliest* of (any subscore = 3) OR (aggregate ≥ 5). On the silent
    # case the aggregate *peaks at 3 and never reaches 5* — so an aggregate-only trigger would never
    # fire and the comparison would be vacuous; the SpO₂ ≤91 single-parameter red is the entire
    # signal. Pinned so a future synth tweak that moved the aggregate would surface here, not silently.
    p = _silent()
    sub = _news2_complete_subscores(p)
    agg = sub.sum(axis=0)
    assert agg.max() == 3 and agg.max() < NEWS2_TRIGGER  # aggregate-only would NEVER fire
    fire = news2_complete_crossing(p)
    assert fire is not None
    i = int(np.searchsorted(p.t_min, fire))
    assert agg[i] < NEWS2_TRIGGER  # the crossing sample is NOT aggregate-driven …
    assert sub[:, i].max() == 3   # … it is fired by a single-parameter red


def test_complete_crossing_not_earlier_than_partial() -> None:
    # Preserved nurse obs add 0 to the aggregate, so they must not manufacture an earlier crossing.
    p = _silent()
    assert news2_complete_crossing(p) == news2_crossing(p) == 1010.0


def test_hero_and_ab_read_one_fire_time() -> None:
    # Single-source guarantee: the 6d state-space hero and the A/B comparison consume the SAME
    # ``news2_complete_crossing`` fire-time (the patient page binds it once). A future change that
    # passed a different value to one of the two views would break here, not drift silently.
    from styx.explain import COMPARISON_LABELS
    from styx.frame import build_context
    from styx.reach.decoupling import decoupling_onset
    from styx.viz.comparison import comparison_figure
    from styx.viz.trajectory import clinical_trajectory_figure

    cohort = build_cohort(seed=42)
    p = cohort.silent_case()
    ctx = build_context(cohort, p)
    fire = news2_complete_crossing(p)

    ab = comparison_figure(
        p.t_min, ctx.risk, ctx.threshold, news2_complete(p), NEWS2_TRIGGER,
        aegis_min=ctx.fire.aegis_min, escalation_min=ctx.fire.threshold_min, news2_crossing_min=fire)
    marker = next(tr for tr in ab.data if tr.name == COMPARISON_LABELS["news2_fires"])
    assert float(np.asarray(marker.x)[0]) == fire  # the A/B places the NEWS2 fire at the source

    try:
        dec = decoupling_onset(p).onset_min
    except ValueError:
        dec = None
    hero = clinical_trajectory_figure(
        p, decoupling_min=dec, aegis_min=ctx.fire.aegis_min,
        escalation_min=ctx.fire.threshold_min, news2_min=fire, echo_endpoints=None, now_idx=None)
    annotations = " ".join(a.text or "" for a in hero.layout.annotations)
    assert f"NEWS2 {fire:.0f}" in annotations  # the 6d hero names the same single fire-time


def test_obs_are_comparator_only_digest_unchanged() -> None:
    # Cardinal routing proof: nurse obs feed only the comparator, never a model path — so the
    # streams⊕events⊕scores sentinel is bit-identical to the recorded baseline.
    assert pipeline_digest(build_cohort(seed=42)) == _RECORDED_DIGEST
