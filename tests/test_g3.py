"""Gate G3 — anticipation dissociation. On the silent case the three signals fire in order —
AEGIS → forecast → F4 absolute threshold — with an AEGIS→threshold lead the cadence preserves.
Evidence comes from styx.anticipation (LYR-1: imported, never reimplemented)."""

from styx.anticipation import fire_times
from styx.config import AEGIS_LEAD_FLOOR_MIN, RESCORE_CADENCE_MIN
from styx.synth import build_cohort


def test_determinism_seed42() -> None:
    a, b = build_cohort(seed=42), build_cohort(seed=42)
    fa = fire_times(a, a.silent_case())
    fb = fire_times(b, b.silent_case())
    assert (fa.aegis_min, fa.forecast_min, fa.threshold_min) == (
        fb.aegis_min, fb.forecast_min, fb.threshold_min
    )  # DET-1 — same seed → identical fire times


def test_signals_fire_in_order() -> None:
    cohort = build_cohort(seed=42)
    ft = fire_times(cohort, cohort.silent_case())
    assert ft.ordered, (
        f"signals collapsed: AEGIS={ft.aegis_min} forecast={ft.forecast_min} thr={ft.threshold_min}"
    )  # AEGIS → forecast → threshold, dissociated


def test_aegis_threshold_lead_clears_floor() -> None:
    cohort = build_cohort(seed=42)
    lead = fire_times(cohort, cohort.silent_case()).aegis_threshold_lead_min
    assert lead is not None and lead >= AEGIS_LEAD_FLOOR_MIN, (
        f"at-cadence AEGIS→threshold lead {lead} below floor {AEGIS_LEAD_FLOOR_MIN}"
    )  # the headline number — regression guard


def test_cadence_preserves_lead() -> None:
    cohort = build_cohort(seed=42)
    p = cohort.silent_case()
    at_cadence = fire_times(cohort, p, RESCORE_CADENCE_MIN).aegis_threshold_lead_min
    raw = fire_times(cohort, p, cohort.dt_min).aegis_threshold_lead_min  # per-sample re-score
    assert at_cadence is not None and raw is not None
    assert abs(at_cadence - raw) <= RESCORE_CADENCE_MIN, (
        f"cadence eroded the lead: at-cadence={at_cadence} raw={raw}"
    )  # the cadence must not erase the dissociation (G3's whole point)
