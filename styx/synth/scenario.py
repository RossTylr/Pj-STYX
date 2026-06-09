"""One-patient physiology generator — COPD-exacerbation *archetypes* (F5 core).

DET-1: all randomness arrives via a passed ``np.random.Generator``; nothing here owns an RNG.
The load-bearing physics: in the stable regime RR and SpO2 share a *fast* homeostatic
compensatory co-oscillation (high windowed coherence); at decoupling onset that shared drive
fails — each signal acquires independent fast fluctuation plus its own slow trend, so windowed
coherence collapses while both stay in range (the silent window) until a single signal breaches.

Deterioration comes in *archetypes* that dissociate oxygenation from effort (so the F1 state
space is genuinely 2-D, not one diagonal): SILENT_HYPOXIA (SpO2 falls, effort flat — the AEGIS
phenomenon), COMPENSATED (effort rises, SpO2 holds), and COUPLED (both move, the legacy shape).
"""

from __future__ import annotations

import enum

import numpy as np

#: Replay grid — 24 h stay sampled every 5 sim-min.
DT_MIN: int = 5
N_SAMPLES: int = 288

#: Scenario clock (sim-min). RR–SpO2 decoupling onset; a signal then breaches by ~T_BREACH.
T_DEC_MIN: int = 540  # sample 108 — earlier than the breach by design, with lead headroom
T_BREACH_MIN: int = 780  # sample 156 — SpO2 crosses 94.0 in the coupled/silent shapes
T_LABS_MIN: int = 660  # inflammation rises later, on its own clock → labs is semi-independent

#: Personal baselines (a healthy mid-range start; conditioned mildly by frailty in cohort.py).
BASE: dict[str, float] = {"RR": 16.0, "SpO2": 97.0, "HR": 78.0, "temp": 36.8, "labs_proxy": 0.3}

#: Fast homeostatic compensation: RR and SpO2 co-fluctuate anti-phase on a 60-min cycle.
FAST_PERIOD_MIN: float = 60.0
A_SPO2: float = 1.5  # SpO2 swing amplitude (coupled regime)
B_RR: float = 1.2  # RR swing amplitude (coupled regime), anti-phase to SpO2

#: Decoupled regime: shared drive gone → independent fast fluctuation (kills coherence).
DECOUP_FAST_SPO2: float = 0.4
DECOUP_FAST_RR: float = 0.35

#: Slow trends after onset (per sim-min), scaled per archetype by _ARCHETYPE_SLOPES.
SLOPE_SPO2: float = -3.0 / (T_BREACH_MIN - T_DEC_MIN)  # SpO2 97 → 94 over the lead window
SLOPE_RR: float = +3.0 / (T_BREACH_MIN - T_DEC_MIN)  # RR 16 → 19 at full scale
SLOPE_HR: float = 0.01  # bpm/min at full scale
SLOPE_TEMP: float = 0.0005
SLOPE_LABS: float = 0.0006  # over the (later, shorter) labs window — modest amplitude

NOISE: float = 0.12  # measurement noise (small — must not cause a spurious early breach)


class Archetype(enum.Enum):
    """Episode shape. STABLE = recovery; the rest are deterioration trajectories."""

    STABLE = "stable"
    COUPLED = "coupled"
    COMPENSATED = "compensated"
    SILENT_HYPOXIA = "silent_hypoxia"


#: Post-onset (SpO2, RR, HR) slope multipliers — how each archetype splits oxygenation vs effort.
_ARCHETYPE_SLOPES: dict[Archetype, tuple[float, float, float]] = {
    Archetype.COUPLED: (1.0, 1.0, 1.0),  # both deteriorate together → the diagonal
    Archetype.SILENT_HYPOXIA: (1.0, 0.0, 0.0),  # SpO2 falls, effort flat (low-effort off-diagonal)
    Archetype.COMPENSATED: (0.3, 2.0, 1.5),  # effort climbs, SpO2 holds (high-effort off-diagonal)
}


def time_grid() -> np.ndarray:
    """Shared sim-minute time grid for every patient."""
    return np.arange(N_SAMPLES, dtype=float) * DT_MIN


def generate_episode(
    rng: np.random.Generator, *, archetype: Archetype, severity: float = 1.0
) -> dict[str, np.ndarray]:
    """Generate one stay as {vital: array[N_SAMPLES]} keyed by VITALS, per the archetype shape."""
    t = time_grid()
    d = np.sin(2.0 * np.pi * t / FAST_PERIOD_MIN)  # shared fast compensatory drive
    eps = lambda: rng.normal(0.0, NOISE, N_SAMPLES)  # noqa: E731 — local measurement noise

    # Coupled regime everywhere as the baseline; deterioration overwrites the post-onset segment.
    spo2 = BASE["SpO2"] - A_SPO2 * d + eps()
    rr = BASE["RR"] + B_RR * d + eps()

    if archetype is Archetype.STABLE:
        hr = BASE["HR"] + eps()
        temp = BASE["temp"] + eps()
        labs = BASE["labs_proxy"] + eps()
    else:
        f_spo2, f_rr, f_hr = _ARCHETYPE_SLOPES[archetype]
        post = t >= T_DEC_MIN
        dec_t = np.clip(t - T_DEC_MIN, 0.0, None)
        labs_t = np.clip(t - T_LABS_MIN, 0.0, None)  # later, independent onset
        indep_spo2 = rng.normal(0.0, DECOUP_FAST_SPO2, N_SAMPLES)
        indep_rr = rng.normal(0.0, DECOUP_FAST_RR, N_SAMPLES)
        spo2_post = BASE["SpO2"] + severity * f_spo2 * SLOPE_SPO2 * dec_t + indep_spo2
        rr_post = BASE["RR"] + severity * f_rr * SLOPE_RR * dec_t + indep_rr
        spo2 = np.where(post, spo2_post, spo2)
        rr = np.where(post, rr_post, rr)
        hr = BASE["HR"] + severity * f_hr * SLOPE_HR * dec_t + eps()
        temp = BASE["temp"] + severity * SLOPE_TEMP * dec_t + eps()
        labs = BASE["labs_proxy"] + severity * SLOPE_LABS * labs_t + eps()

    # Physiological clipping: SpO2 ≤ 100%, inflammation proxy ≥ 0 (a low value is not a breach).
    spo2 = np.clip(spo2, 0.0, 100.0)
    labs = np.clip(labs, 0.0, None)
    return {"RR": rr, "SpO2": spo2, "HR": hr, "temp": temp, "labs_proxy": labs}
