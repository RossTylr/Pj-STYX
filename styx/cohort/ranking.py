"""F6 ward triage — re-score the whole cohort at the replay clock and rank by time-to-escalation.

Pure (LYR-1): no Streamlit, no I/O. A *surface* over the existing per-patient maths — it organises
risk / forecast / AEGIS outputs the rest of ``styx`` already produces, and changes none of them.

The expensive cohort-level fit (embedding, basins, conformal band) happens **once** in
``build_cohort_context`` — unlike ``styx.frame.build_context`` which re-fits per patient (fine for
one patient, O(N²) for a ward). ``ward_frame`` is then a cheap per-clock re-score.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from styx.anticipation import FireTimes, cadence_indices, fire_times
from styx.config import RESCORE_CADENCE_MIN, THRESHOLDS, VITALS
from styx.forecast import ForecastCone, conformal_band, project
from styx.risk import aegis_fire_index, exceedance_per_vital, risk_series
from styx.state import fit_embedding, learn_basins
from styx.state.embedding import Basins, Embedding
from styx.synth.cohort import Cohort


@dataclass(frozen=True, eq=False)
class CohortContext:
    """The once-per-cohort fit, reused across every replay-clock re-score (the ward analogue of
    ``PatientContext``). All per-patient series are precomputed so ``ward_frame`` stays cheap."""

    cohort: Cohort
    emb: Embedding
    basins: Basins
    band: np.ndarray  # (H,) one conformal band, pooled over the whole cohort (marginal coverage)
    risk: dict[int, np.ndarray]  # pid -> (N_SAMPLES,) risk waterline
    aegis_idx: dict[int, int | None]  # pid -> AEGIS fire sample-index (None if it never fires)
    exceed: dict[int, dict[str, np.ndarray]]  # pid -> per-vital exceedance (quietest / silent flags)
    indices: list[int]  # the shared cadence grid the clock scrubs over (all patients share t_min)
    default_idx: int  # the silent-window frame the clock lands on (the silent case's forecast fire)
    t_min: np.ndarray
    threshold: float = THRESHOLDS.risk_escalation
    cadence_min: int = RESCORE_CADENCE_MIN


def _silent_window_idx(t: np.ndarray, indices: list[int], fire: FireTimes) -> int:
    """The default clock: nearest re-score to the silent case's forecast fire (risk rising, still
    pre-threshold — the money shot), falling back to its AEGIS flag, then mid-stay."""
    target = fire.forecast_min if fire.forecast_min is not None else (
        fire.aegis_min if fire.aegis_min is not None else float(t[len(t) // 2]))
    return min(indices, key=lambda i: abs(float(t[i]) - target))


def build_cohort_context(
    cohort: Cohort,
    *,
    cadence_min: int = RESCORE_CADENCE_MIN,
    threshold: float = THRESHOLDS.risk_escalation,
) -> CohortContext:
    """Fit the embedding, basins and conformal band **once**, then cache every per-patient series.

    The conformal band is pooled over the whole cohort (a deterministic marginal-coverage choice;
    the methods notebook validates its empirical coverage against the nominal 1−α).
    """
    emb = fit_embedding(cohort)
    basins = learn_basins(cohort, emb)
    t = cohort.patients[0].t_min
    idx = cadence_indices(cohort.patients[0], cadence_min)
    risk = {p.pid: risk_series(p, emb, basins) for p in cohort.patients}
    band = conformal_band(list(risk.values()), t)
    aegis = {p.pid: aegis_fire_index(p, emb, idx) for p in cohort.patients}
    exceed = {p.pid: exceedance_per_vital(p) for p in cohort.patients}
    fire0 = fire_times(cohort, cohort.silent_case(), cadence_min, threshold=threshold)
    default_idx = _silent_window_idx(t, idx, fire0)
    return CohortContext(
        cohort, emb, basins, band, risk, aegis, exceed, idx, default_idx, t, threshold, cadence_min,
    )


@dataclass(frozen=True)
class WardRow:
    """One patient's standing on the triage board at the current replay clock."""

    pid: int
    archetype: str
    status: str  # the trichotomy: "escalated" | "escalating" | "no-forecast"
    risk_now: float
    eta_soonest_min: float | None  # cone *upper* edge crosses the line (fires soonest)
    eta_central_min: float | None  # cone *point* crosses the line (None if the point never reaches)
    eta_confident: bool  # True only when the point forecast itself crosses within the horizon
    silent_but_rising: bool  # AEGIS has fired by now, yet risk is still below the escalation line
    quietest: bool  # the single lowest absolute exceedance in the cohort (the "greenest" board row)
    new_low_history: bool  # bottom-quartile care history, yet on the watchlist


# The trichotomy's sort order: who's already over the line, then who's heading there, then the rest.
_STATUS_RANK: dict[str, int] = {"escalated": 0, "escalating": 1, "no-forecast": 2}


def _first_crossing_min(edge: np.ndarray, t_fore: np.ndarray, threshold: float) -> float | None:
    """Sim-minutes until ``edge`` first reaches ``threshold`` over the horizon (None if it never does)."""
    hits = np.flatnonzero(edge >= threshold)
    return float(t_fore[hits[0]]) if hits.size else None


def _eta_band(
    cone: ForecastCone, now_min: float, risk_now: float, threshold: float
) -> tuple[str, float | None, float | None, bool]:
    """The banded time-to-escalation (UQ-1: a range off the cone, never a hard minute).

    The upper edge crosses at or before the point forecast (``upper ≥ point``), so the band runs
    (soonest, central). Already-over and never-crossing are handled explicitly — no NaN ever sorts.
    """
    if risk_now >= threshold:
        return "escalated", None, None, False
    soonest = _first_crossing_min(cone.upper, cone.t_fore, threshold)
    central = _first_crossing_min(cone.point, cone.t_fore, threshold)
    if soonest is None:  # upper edge never reaches the line within the horizon
        return "no-forecast", None, None, False
    eta_soonest = soonest - now_min
    eta_central = central - now_min if central is not None else None
    return "escalating", eta_soonest, eta_central, eta_central is not None


def ward_frame(cctx: CohortContext, now_idx: int) -> list[WardRow]:
    """Re-score the whole cohort at the replay clock ``now_idx`` and rank it (the F6 board)."""
    now_min = float(cctx.t_min[now_idx])
    density = {p.pid: sum(p.theograph.values()) for p in cctx.cohort.patients}
    low_history = float(np.quantile(list(density.values()), 0.25))  # bottom-quartile care history
    max_exc = {  # the worst single-vital exceedance each patient shows right now
        pid: max(float(cctx.exceed[pid][v][now_idx]) for v in VITALS) for pid in cctx.risk
    }
    quietest_pid = min(max_exc, key=lambda pid: (max_exc[pid], pid))  # pid tiebreak (DET-1)

    rows: list[WardRow] = []
    for p in cctx.cohort.patients:
        risk_now = float(cctx.risk[p.pid][now_idx])
        cone = project(cctx.risk[p.pid], cctx.t_min, now_idx, cctx.band)
        status, eta_soon, eta_cen, confident = _eta_band(cone, now_min, risk_now, cctx.threshold)
        a = cctx.aegis_idx[p.pid]
        silent = a is not None and a <= now_idx and risk_now < cctx.threshold
        # `new_low_history`: deteriorating without the frailty history that would have predicted it.
        # (Alternative reading: a thin history is a thinner prior → *higher model uncertainty* about
        # this patient, not necessarily lower risk. We surface it as a watch-flag, not a risk claim.)
        new_low = density[p.pid] <= low_history and status != "no-forecast"
        rows.append(WardRow(
            p.pid, p.archetype.value, status, risk_now, eta_soon, eta_cen, confident,
            silent, p.pid == quietest_pid, new_low,
        ))
    rows.sort(key=lambda r: (
        _STATUS_RANK[r.status],
        r.eta_soonest_min if r.eta_soonest_min is not None else math.inf,
        r.pid,
    ))
    return rows
