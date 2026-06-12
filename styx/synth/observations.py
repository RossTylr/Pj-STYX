"""Nurse-entered observations — the intermittent NEWS2 params a wearable cannot capture.

Systolic BP and consciousness (ACVPU) are recorded by a nurse on an obs round, not streamed by the
wearable. They feed *only* the NEWS2 comparator (``styx.readouts.news2_complete``), never STYX's
state-space model — so SIG-1 and gate G1 are untouched. In this acute-respiratory-infection scenario
both are clinically preserved through the silent window (perfusion and cognition hold until late), so
the completed NEWS2 still sits flat while STYX is already rising.

Pure + deterministic (LYR-1, DET-1): values are drawn from the patient's existing child Generator as
a *trailing* draw (see ``styx.synth.cohort.build_cohort``), so adding them shifts no existing vital
stream. Each field is returned as a full-length array on the shared grid, step-held between rounds —
the obs stands until the nurse next measures it.
"""

from __future__ import annotations

import numpy as np

from styx.config import NURSE_OBS_CADENCE_MIN

#: Preserved baselines for this scenario. BP 122 mmHg sits well inside NEWS2 band 0 (111–219 → 0);
#: jitter is clipped so a round can never dip into band 1 (≤110), keeping the nurse contribution 0.
#: ACVPU 0 = "Alert" (any other level — new confusion / V / P / U — scores a red 3).
_BP_BASELINE: float = 122.0
_BP_JITTER: float = 3.0
_BP_FLOOR: float = 114.0  # guarantees band 0 (≥ 111) even at the jitter tail
_ACVPU_ALERT: int = 0


def _round_indices(t_min: np.ndarray, cadence_min: int) -> np.ndarray:
    """Indices on the shared grid that fall on a nurse obs round (every ``cadence_min`` sim-min)."""
    dt = int(t_min[1] - t_min[0])
    step = max(1, cadence_min // dt)
    return np.arange(0, len(t_min), step)


def _step_hold(values_at_rounds: np.ndarray, rounds: np.ndarray, n: int) -> np.ndarray:
    """Forward-fill round-recorded values across the full grid (the obs stands until re-measured)."""
    out = np.empty(n, dtype=float)
    for k, idx in enumerate(rounds):
        end = int(rounds[k + 1]) if k + 1 < len(rounds) else n
        out[int(idx):end] = values_at_rounds[k]
    return out


def generate_nurse_obs(t_min: np.ndarray, rng: np.random.Generator) -> dict[str, np.ndarray]:
    """Nurse-recorded systolic BP + ACVPU on 4-hourly rounds, step-held between rounds.

    Preserved through the stay for this scenario (BP in band 0, ACVPU Alert) — see the module
    docstring. Returns two full-length arrays on ``t_min`` so the NEWS2 scorer reads them like any
    other channel.
    """
    rounds = _round_indices(t_min, NURSE_OBS_CADENCE_MIN)
    bp_rounds = np.maximum(_BP_BASELINE + rng.normal(0.0, _BP_JITTER, size=len(rounds)), _BP_FLOOR)
    bp = _step_hold(bp_rounds, rounds, len(t_min))
    acvpu = np.full(len(t_min), float(_ACVPU_ALERT))
    return {"systolic_bp": bp, "acvpu": acvpu}
