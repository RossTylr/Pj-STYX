"""R1a claim-integrity gate — the descriptive hazard stratification (no predictive-lift claim).

Verify → else fallback → else cut: this asserts the *primary* path (strata separate, HR > 1, a
reported c-index, pid 39 the honest residual). If it ever regresses, the notebook carries the
"history-only AUC 0.765 + pid 39" fallback — the claim degrades, it does not overclaim.
"""

import numpy as np

from styx.cohort import build_cohort_context
from styx.reach.history import stratify, survival_table
from styx.synth import build_cohort


def _ctx(seed: int = 42):
    return build_cohort_context(build_cohort(seed=seed))


def test_determinism_seed42() -> None:
    a, b = stratify(_ctx()), stratify(_ctx())
    assert (a.hazard_ratio, a.hr_ci, a.c_index, a.logrank_p) == (
        b.hazard_ratio, b.hr_ci, b.c_index, b.logrank_p
    )  # DET-1 — lifelines Cox/KM/log-rank carry no RNG
    assert np.array_equal(a.high.survival, b.high.survival)
    assert np.array_equal(a.low.survival, b.low.survival)
    assert a.residual_pids == b.residual_pids


def test_duration_reads_the_waterline() -> None:
    """Single-source: a known escalated patient's duration is the first risk≥threshold crossing —
    read off the existing waterline, not a recomputed time-to-event."""
    cctx = _ctx()
    df = survival_table(cctx)
    row = df[df["pid"] == 39].iloc[0]
    risk = cctx.risk[39]
    expected = float(cctx.t_min[int(np.flatnonzero(risk >= cctx.threshold)[0])])
    assert row["event"] == 1 and row["duration_min"] == expected


def test_descriptive_claim_holds() -> None:
    s = stratify(_ctx())
    assert s.n_events == 21  # the seed=42 escalation split (21 of 50) — the survival event count
    assert s.hazard_ratio > 1.0 and s.hr_ci[0] > 1.0  # denser history → higher hazard, CI clears 1
    assert s.logrank_p < 0.05  # the high- vs low-density strata separate
    assert s.c_index > 0.6  # discrimination reported — descriptive, never a lift claim


def test_pid39_is_the_honest_residual() -> None:
    # bottom-quartile care history yet escalated — caught by the live signal, not by history
    assert 39 in stratify(_ctx()).residual_pids
