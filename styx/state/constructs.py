"""Named physiological constructs — the G2 legibility targets for the latent axes.

Config-derived and deterministic (no fitted parameters): each construct normalises its vitals
to the clinical band in NORMAL_RANGES, so an axis that tracks oxygenation or effort is *named*,
not a blind PCA blob. The state embedding's axes are scored against these (styx.state.gates).
"""

from __future__ import annotations

import numpy as np

from styx.config import NORMAL_RANGES
from styx.synth.cohort import Patient


def _norm(p: Patient, v: str) -> np.ndarray:
    """Vital v centred on its normal band: 0 at mid-range, ±1 at the band edges."""
    r = NORMAL_RANGES[v]
    mid, halfrange = (r.low + r.high) / 2.0, (r.high - r.low) / 2.0
    return (p.vitals[v] - mid) / halfrange


def oxygenation(p: Patient) -> np.ndarray:
    """Oxygenation construct from SpO₂ — high SpO₂ → high oxygenation."""
    return _norm(p, "SpO2")


def effort(p: Patient) -> np.ndarray:
    """Respiratory + cardiac effort from RR (+HR) — high RR/HR → high effort."""
    return _norm(p, "RR") + _norm(p, "HR")
