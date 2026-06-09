"""Anticipation wiring — the three S3 signals fired on the windowed re-score (gate G3).

The integrative layer over state · forecast · risk: it re-scores a patient on the A2 cadence and
reports when each signal fires — AEGIS (baseline departure), the forecast cone crossing, and the
F4 absolute threshold — so the order and the AEGIS→threshold lead can be measured. The app and the
proof notebook call this; nobody reimplements it (LYR-1). Deterministic (DET-1): every input is.
"""

from __future__ import annotations

from dataclasses import dataclass

from styx.config import RESCORE_CADENCE_MIN, THRESHOLDS
from styx.forecast import ForecastCone, conformal_band, forecast_fire_index, project
from styx.risk import aegis_fire_index, escalation_fire_index, risk_series
from styx.state import fit_embedding, learn_basins
from styx.synth.cohort import Cohort, Patient


@dataclass(frozen=True, eq=False)
class FireTimes:
    """When each S3 signal fires for a patient (sim-minutes, or None if it never fires)."""

    aegis_min: float | None
    forecast_min: float | None
    threshold_min: float | None
    cadence_min: int

    @property
    def ordered(self) -> bool:
        """True iff all three fired and in the anticipation order AEGIS → forecast → threshold."""
        ts = (self.aegis_min, self.forecast_min, self.threshold_min)
        return None not in ts and ts[0] < ts[1] < ts[2]

    @property
    def aegis_threshold_lead_min(self) -> float | None:
        """The headline lead: sim-minutes from the AEGIS flag to the absolute threshold breach."""
        if self.aegis_min is None or self.threshold_min is None:
            return None
        return self.threshold_min - self.aegis_min


def cadence_indices(patient: Patient, cadence_min: int) -> list[int]:
    """Sample indices of the re-score grid at ``cadence_min`` (per-sample when ≤ the sample step)."""
    dt = int(patient.t_min[1] - patient.t_min[0])
    step = max(1, cadence_min // dt)
    return list(range(0, patient.t_min.size, step))


def fire_times(
    cohort: Cohort,
    patient: Patient,
    cadence_min: int = RESCORE_CADENCE_MIN,
    *,
    threshold: float = THRESHOLDS.risk_escalation,
) -> FireTimes:
    """Re-score ``patient`` on the cadence grid and report the three fire times (gate G3 input)."""
    emb = fit_embedding(cohort)
    basins = learn_basins(cohort, emb)
    t = patient.t_min
    idx = cadence_indices(patient, cadence_min)
    calibration = [risk_series(q, emb, basins) for q in cohort.patients if q.pid != patient.pid]
    band = conformal_band(calibration, t)
    risk = risk_series(patient, emb, basins)

    ai = aegis_fire_index(patient, emb, idx)
    fi = forecast_fire_index(risk, t, band, threshold, idx)
    ei = escalation_fire_index(patient, emb, basins, idx, threshold=threshold)

    def tmin(i: int | None) -> float | None:
        return None if i is None else float(t[i])

    return FireTimes(tmin(ai), tmin(fi), tmin(ei), cadence_min)


def ghost_cone(
    cohort: Cohort, patient: Patient, *, cadence_min: int = RESCORE_CADENCE_MIN
) -> ForecastCone | None:
    """F9 — the *stale* forecast: the cone we'd have drawn at the AEGIS fire-time, re-run now.

    Anchors ``project`` at the AEGIS fire index and projects forward with the same conformal band,
    so the page can overlay that earlier projection on the realised path — the ghost of what STYX
    saw coming when it first flagged. None if AEGIS never fired. Pure re-run; no new model (LYR-1).
    """
    emb = fit_embedding(cohort)
    basins = learn_basins(cohort, emb)
    t = patient.t_min
    ai = aegis_fire_index(patient, emb, cadence_indices(patient, cadence_min))
    if ai is None:
        return None
    calibration = [risk_series(q, emb, basins) for q in cohort.patients if q.pid != patient.pid]
    band = conformal_band(calibration, t)
    return project(risk_series(patient, emb, basins), t, ai, band)
