"""Gate G1 — synthetic fidelity (the root gate; no fallback). After Slice S1.

Mirrors the CLAUDE.md testing pattern. One assertion per G1 sub-condition: determinism, a
dissociable silent window, a genuine RR–SpO2 decoupling leading any breach by ≥90 min, and a
≥12-patient cohort whose outcome is learnable from history.
"""

from styx.config import DECOUPLING_LEAD_MIN, OUTCOME_AUC_BAND
from styx.synth import (
    build_cohort,
    cohort_outcome_auc,
    decoupling_lead_min,
    has_silent_window,
    replay_windows,
)


def test_determinism_seed42() -> None:
    # DET-1 — same seed → bit-identical streams, events, and labels.
    assert build_cohort(seed=42).equals(build_cohort(seed=42))


def test_cohort_is_at_least_twelve() -> None:
    assert len(build_cohort(seed=42).patients) >= 12


def test_dissociable_silent_window() -> None:
    # Vitals in range, multivariate trend adverse — a trend detector fires where a threshold won't.
    assert has_silent_window(build_cohort(seed=42).silent_case())


def test_decoupling_leads_breach_by_90min() -> None:
    # RR–SpO2 coherence collapse precedes any single-signal breach by the G1 lead target.
    assert decoupling_lead_min(build_cohort(seed=42).silent_case()) >= DECOUPLING_LEAD_MIN


def test_outcome_learnability_in_band() -> None:
    # Learnable yet not perfect: frailty raises the *odds* of escalation, stochastically.
    lo, hi = OUTCOME_AUC_BAND
    auc = cohort_outcome_auc(build_cohort(seed=42))
    where = "below" if auc < lo else "above"
    assert lo <= auc <= hi, f"history→outcome AUC {auc:.3f} {where} band [{lo}, {hi}]"


def test_replay_exposes_rescore_cadence() -> None:
    # A2 serving scaffold — windowed re-score over replay; cadence is an explicit parameter.
    cohort = build_cohort(seed=42)
    windows = list(replay_windows(cohort.silent_case(), cohort.rescore_cadence_min))
    assert windows and all(isinstance(t, int) and isinstance(s, slice) for t, s in windows)
