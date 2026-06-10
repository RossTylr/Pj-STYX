"""Per-frame assembly for the replay clock — all the patient-page state, computed in styx (LYR-1).

The Streamlit page holds zero modelling logic: it builds a ``PatientContext`` once (the expensive
cohort-level fit — embedding, basins, conformal band, ghost) and then asks ``patient_frame`` for a
cheap ``Frame`` at each scrub position. Every figure the page draws is fed from one of these.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from styx.anticipation import FireTimes, cadence_indices, fire_times, ghost_cone
from styx.config import RESCORE_CADENCE_MIN, THRESHOLDS
from styx.forecast import ForecastCone, conformal_band, project
from styx.rationale import Rationale, explain
from styx.risk import aegis_fire_index, risk_series
from styx.state import fit_embedding, learn_basins
from styx.state.embedding import Basins, Embedding
from styx.synth.cohort import Cohort, Patient
from styx.theograph import CareEvent, events_on_path, expand_history


@dataclass(frozen=True, eq=False)
class PatientContext:
    """Cohort-level fit for one patient — built once, reused across every scrub frame."""

    cohort: Cohort
    patient: Patient
    emb: Embedding
    basins: Basins
    risk: np.ndarray
    band: np.ndarray
    events: tuple[CareEvent, ...]
    on_path: list[tuple[int, CareEvent]]
    ghost: ForecastCone | None
    aegis_idx: int | None
    indices: list[int]  # the re-score grid the clock scrubs over
    fire: FireTimes  # AEGIS / forecast / threshold fire times — status lead + scrub ticks
    default_idx: int  # the silent-window frame the clock lands on (the demo's money shot)
    ticks: dict[str, int | None]  # re-score indices for the scrub ticks / jump buttons
    threshold: float = THRESHOLDS.risk_escalation
    cadence_min: int = RESCORE_CADENCE_MIN


@dataclass(frozen=True, eq=False)
class Frame:
    """Everything the patient page renders at one scrub position."""

    now_idx: int
    now_min: float
    risk_now: float
    cone: ForecastCone
    rationale: Rationale
    sentinel: float  # confidence in the current estimate ∈ [0, 1] (SENTINEL)
    sentinel_label: str
    regime: str  # "silent" | "crossed" (from the rationale)
    risk_verb: str  # plain status phrase for the metric row


def _nearest_idx(t: np.ndarray, indices: list[int], target_min: float | None) -> int | None:
    """The re-score index closest to a sim-minute target (None if the target never fired)."""
    if target_min is None:
        return None
    return min(indices, key=lambda i: abs(float(t[i]) - target_min))


def _default_idx(t: np.ndarray, indices: list[int], fire: FireTimes) -> int:
    """The silent-window frame the clock lands on: nearest re-score to the forecast fire (the money
    shot — risk rising, still pre-threshold), falling back to the AEGIS flag, then mid-stay."""
    target = fire.forecast_min if fire.forecast_min is not None else (
        fire.aegis_min if fire.aegis_min is not None else float(t[len(t) // 2]))
    return min(indices, key=lambda i: abs(float(t[i]) - target))


def build_context(
    cohort: Cohort, patient: Patient, *, cadence_min: int = RESCORE_CADENCE_MIN
) -> PatientContext:
    """The expensive once-per-patient fit (embedding, basins, conformal band, ghost, events)."""
    emb = fit_embedding(cohort)
    basins = learn_basins(cohort, emb)
    t = patient.t_min
    idx = cadence_indices(patient, cadence_min)
    risk = risk_series(patient, emb, basins)
    calibration = [risk_series(q, emb, basins) for q in cohort.patients if q.pid != patient.pid]
    band = conformal_band(calibration, t)
    events = expand_history(patient)
    fire = fire_times(cohort, patient, cadence_min)
    ticks = {
        "aegis": _nearest_idx(t, idx, fire.aegis_min),
        "forecast": _nearest_idx(t, idx, fire.forecast_min),
        "breach": _nearest_idx(t, idx, fire.threshold_min),
    }
    return PatientContext(
        cohort, patient, emb, basins, risk, band, events,
        events_on_path(patient, emb, events), ghost_cone(cohort, patient, cadence_min=cadence_min),
        aegis_fire_index(patient, emb, idx), idx, fire, _default_idx(t, idx, fire), ticks,
    )


def _sentinel(cone: ForecastCone) -> tuple[float, str]:
    """Confidence from the forecast band width at the near horizon (wider → less certain).

    SENTINEL folds uncertainty in honestly (UQ-1): in this synthetic replay every stream is
    complete, so confidence tracks the conformal band; real missingness would discount it further.
    """
    conf = float(np.clip(1.0 - (cone.upper[0] - cone.lower[0]) / 0.5, 0.0, 1.0))
    label = "high" if conf >= 0.75 else "medium" if conf >= 0.5 else "low"
    return conf, label


def patient_frame(ctx: PatientContext, now_idx: int) -> Frame:
    """Assemble the cheap per-scrub frame at ``now_idx`` from the prebuilt context."""
    t = ctx.patient.t_min
    cone = project(ctx.risk, t, now_idx, ctx.band)
    conf, label = _sentinel(cone)
    rationale = explain(ctx.patient, ctx.emb, ctx.basins, now_idx)
    verb = "threshold crossed" if rationale.regime == "crossed" else "rising, pre-threshold"
    return Frame(
        now_idx, float(t[now_idx]), float(ctx.risk[now_idx]), cone, rationale, conf, label,
        rationale.regime, verb,
    )
