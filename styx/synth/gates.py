"""Gate-G1 measurement helpers — importable by both tests/test_g1.py and notebook 01.

LYR-1: the gate's evidence is computed here once and consumed by the test and the proof
notebook alike (never reimplemented in either). These read a Patient; they do not generate one.
"""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from styx.config import NORMAL_RANGES, VITALS
from styx.synth.cohort import Cohort, Outcome, Patient
from styx.synth.scenario import DT_MIN

COHERENCE_WINDOW: int = 12  # 60 sim-min rolling window
_DROP_K: float = 0.4  # coherence must fall this far below its stable baseline to count
_SUSTAIN: int = 2  # ...for this many consecutive windows (rejects single-window noise spikes)


def _detrend(y: np.ndarray) -> np.ndarray:
    """Remove a window's linear trend so coherence reflects fast co-fluctuation, not drift."""
    x = np.arange(y.size, dtype=float)
    return y - np.polyval(np.polyfit(x, y, 1), x)


def windowed_coherence(
    rr: np.ndarray, spo2: np.ndarray, window: int = COHERENCE_WINDOW
) -> np.ndarray:
    """Trailing rolling Pearson r of *detrended* RR vs SpO2; first window-1 entries are nan.

    Detrending is the point: homeostatic coupling lives in the fast anti-phase co-fluctuation
    (r → −1), so removing each window's slow drift stops opposite deterioration trends from
    masquerading as coherence. At decoupling the residuals are independent → r → 0.
    """
    n = rr.size
    out = np.full(n, np.nan)
    for i in range(window - 1, n):
        a, b = _detrend(rr[i - window + 1 : i + 1]), _detrend(spo2[i - window + 1 : i + 1])
        sa, sb = a.std(), b.std()
        out[i] = 0.0 if sa == 0 or sb == 0 else float(np.corrcoef(a, b)[0, 1])
    return out


def decoupling_onset_index(p: Patient, window: int = COHERENCE_WINDOW) -> int | None:
    """First sample index of a sustained RR–SpO2 coherence collapse below the stable baseline."""
    coh = np.abs(windowed_coherence(p.vitals["RR"], p.vitals["SpO2"], window))
    stable = coh[window - 1 : p.t_min.size // 3]  # first third of the stay = pre-onset reference
    baseline = float(np.nanmedian(stable))
    thresh = baseline - _DROP_K
    run = 0
    for i in range(window - 1, coh.size):
        run = run + 1 if coh[i] < thresh else 0
        if run >= _SUSTAIN:
            return i - _SUSTAIN + 1
    return None


def breach_index(p: Patient) -> int | None:
    """First sample of a *sustained* single-signal breach (≥_SUSTAIN samples out of range).

    Sustained, not instantaneous: a clinical breach is a held crossing, not a lone noisy sample.
    """
    first = p.t_min.size
    for v in VITALS:
        r = NORMAL_RANGES[v]
        out = (p.vitals[v] < r.low) | (p.vitals[v] > r.high)
        run = 0
        for i in range(out.size):
            run = run + 1 if out[i] else 0
            if run >= _SUSTAIN:
                first = min(first, i - _SUSTAIN + 1)
                break
    return None if first == p.t_min.size else first


def _first_excursion_index(p: Patient) -> int | None:
    """First sample where any vital is even instantaneously out of range (silent-window end)."""
    first = p.t_min.size
    for v in VITALS:
        r = NORMAL_RANGES[v]
        out = np.where((p.vitals[v] < r.low) | (p.vitals[v] > r.high))[0]
        if out.size:
            first = min(first, int(out[0]))
    return None if first == p.t_min.size else first


def decoupling_lead_min(p: Patient) -> float:
    """Sim-minutes by which the decoupling onset precedes the first single-signal breach."""
    onset, breach = decoupling_onset_index(p), breach_index(p)
    if onset is None or breach is None:
        return 0.0
    return float((breach - onset) * DT_MIN)


_MIN_SILENT_SAMPLES: int = 6  # ≥30 sim-min — a window long enough to read a trend from


def has_silent_window(p: Patient) -> bool:
    """True if a window exists where every vital is in range yet the trend is adverse.

    The window runs from the decoupling onset to the first instantaneous range excursion, so
    the in-range guarantee is strict; the adverse trend (RR rising, SpO2 falling) is what a
    trend detector would catch here while an absolute-threshold check stays silent.
    """
    onset = decoupling_onset_index(p)
    end = _first_excursion_index(p)
    if onset is None or end is None or end - onset < _MIN_SILENT_SAMPLES:
        return False
    seg = slice(onset, end)

    def _in(v: str) -> bool:
        col = p.vitals[v][seg]
        return bool(np.all((col >= NORMAL_RANGES[v].low) & (col <= NORMAL_RANGES[v].high)))

    in_range = all(_in(v) for v in VITALS)
    x = p.t_min[seg] - p.t_min[seg].mean()  # centre for a well-conditioned fit
    rr_slope = float(np.polyfit(x, p.vitals["RR"][seg], 1)[0])
    spo2_slope = float(np.polyfit(x, p.vitals["SpO2"][seg], 1)[0])
    return in_range and rr_slope > 0 and spo2_slope < 0


def cohort_outcome_auc(cohort: Cohort) -> float:
    """In-sample ROC-AUC predicting ESCALATED outcome from the *observable* comorbidity proxy.

    Scores against the noisy event-density observable (``comorbidity_index``), never the latent
    frailty that set the outcome — so the AUC is what a real model could see, not a tautology.
    """
    x = np.array([[p.comorbidity_index] for p in cohort.patients])
    y = np.array([1 if p.outcome is Outcome.ESCALATED else 0 for p in cohort.patients])
    model = LogisticRegression(max_iter=1000).fit(x, y)
    return float(roc_auc_score(y, model.predict_proba(x)[:, 1]))


def replay_windows(p: Patient, cadence_min: int) -> Iterator[tuple[int, slice]]:
    """Yield (sim-minute, trailing-window slice) at each re-score step — the A2 serving scaffold.

    The serving model is a windowed re-score over replay; G3 owns tuning ``cadence_min``.
    """
    step = max(1, cadence_min // DT_MIN)
    for i in range(COHERENCE_WINDOW - 1, p.t_min.size, step):
        yield int(p.t_min[i]), slice(i - COHERENCE_WINDOW + 1, i + 1)
