"""One-patient physiology generator — the COPD-exacerbation decoupling scenario (F5 core).

DET-1: all randomness arrives via a passed ``np.random.Generator``; nothing here owns an RNG.
The load-bearing physics: in the stable regime RR and SpO2 share a *fast* homeostatic
compensatory co-oscillation (high windowed coherence); at decoupling onset that shared drive
fails — each signal acquires independent fast fluctuation plus its own slow adverse trend, so
windowed coherence collapses while both stay in range (the silent window) until SpO2 finally
breaches its normal-low (the single-signal breach the coherence drop precedes).
"""

from __future__ import annotations

import numpy as np

#: Replay grid — 24 h stay sampled every 5 sim-min.
DT_MIN: int = 5
N_SAMPLES: int = 288

#: Scenario clock (sim-min). Onset of RR–SpO2 decoupling; SpO2 then breaches ~T_BREACH.
T_DEC_MIN: int = 600  # sample 120
T_BREACH_MIN: int = 780  # sample 156 — SpO2 crosses 94.0; lead = 180 min by construction

#: Personal baselines (a healthy mid-range start; conditioned mildly by frailty in cohort.py).
BASE: dict[str, float] = {"RR": 16.0, "SpO2": 97.0, "HR": 78.0, "temp": 36.8, "labs_proxy": 0.3}

#: Fast homeostatic compensation: RR and SpO2 co-fluctuate anti-phase on a 60-min cycle.
FAST_PERIOD_MIN: float = 60.0
A_SPO2: float = 1.5  # SpO2 swing amplitude (coupled regime)
B_RR: float = 1.2  # RR swing amplitude (coupled regime), anti-phase to SpO2

#: Decoupled regime: shared drive gone → independent fast fluctuation (kills coherence).
#: Sized to dominate measurement noise (so detrended coherence collapses) yet stay small in
#: absolute terms (so the SpO2 breach is set by the slow trend, not a noise spike).
DECOUP_FAST_SPO2: float = 0.4
DECOUP_FAST_RR: float = 0.35

#: Slow adverse trends after onset (per sim-min). SpO2 reaches 94.0 at T_BREACH by design.
SLOPE_SPO2: float = -3.0 / (T_BREACH_MIN - T_DEC_MIN)  # -0.01667
SLOPE_RR: float = +3.0 / (T_BREACH_MIN - T_DEC_MIN)  # +0.01667 → RR 16→19 by breach (< 20)
SLOPE_HR: float = 0.01  # 78 → ~92 over the stay (< 100)
SLOPE_TEMP: float = 0.0005  # 36.8 → ~37.5 (< 37.8)
SLOPE_LABS: float = 0.0003  # 0.3 → ~0.73 (< 1.0)

NOISE: float = 0.12  # measurement noise (small — must not cause a spurious early breach)


def time_grid() -> np.ndarray:
    """Shared sim-minute time grid for every patient."""
    return np.arange(N_SAMPLES, dtype=float) * DT_MIN


def generate_episode(
    rng: np.random.Generator, *, deteriorate: bool, severity: float = 1.0
) -> dict[str, np.ndarray]:
    """Generate one stay as {vital: array[N_SAMPLES]} keyed by VITALS.

    ``deteriorate`` selects the COPD-exacerbation template (decoupling + breach); otherwise a
    stable, in-range, homeostatically-coupled recovery. ``severity`` scales the adverse slopes.
    """
    t = time_grid()
    d = np.sin(2.0 * np.pi * t / FAST_PERIOD_MIN)  # shared fast compensatory drive
    eps = lambda: rng.normal(0.0, NOISE, N_SAMPLES)  # noqa: E731 — local measurement noise

    # Coupled regime everywhere as the baseline; decoupling overwrites the post-onset segment.
    spo2 = BASE["SpO2"] - A_SPO2 * d + eps()
    rr = BASE["RR"] + B_RR * d + eps()

    if deteriorate:
        post = t >= T_DEC_MIN
        dec_t = np.clip(t - T_DEC_MIN, 0.0, None)
        indep_spo2 = rng.normal(0.0, DECOUP_FAST_SPO2, N_SAMPLES)
        indep_rr = rng.normal(0.0, DECOUP_FAST_RR, N_SAMPLES)
        spo2 = np.where(post, BASE["SpO2"] + severity * SLOPE_SPO2 * dec_t + indep_spo2, spo2)
        rr = np.where(post, BASE["RR"] + severity * SLOPE_RR * dec_t + indep_rr, rr)
        hr = BASE["HR"] + severity * SLOPE_HR * dec_t + eps()
        temp = BASE["temp"] + severity * SLOPE_TEMP * dec_t + eps()
        labs = BASE["labs_proxy"] + severity * SLOPE_LABS * dec_t + eps()
    else:
        hr = BASE["HR"] + eps()
        temp = BASE["temp"] + eps()
        labs = BASE["labs_proxy"] + eps()

    # Physiological clipping: SpO2 ≤ 100%, inflammation proxy ≥ 0 (a low value is not a breach).
    spo2 = np.clip(spo2, 0.0, 100.0)
    labs = np.clip(labs, 0.0, None)
    return {"RR": rr, "SpO2": spo2, "HR": hr, "temp": temp, "labs_proxy": labs}
