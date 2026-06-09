"""F7 — AEGIS, the personal-baseline silent-deterioration flag (the earliest of the three signals).

Baseline-relative, *not* attractor-relative: learn each patient's own stable opening window in the
2-D state space, then flag a sustained departure from it. This is the mechanism a global absolute
threshold and a global risk score both miss — it fires while the patient still looks fine.

The departure signal is the **2-D state-position** z-distance from baseline (max over both named
axes), not the oxygenation axis alone — so AEGIS generalises to the effort-led (compensated)
deteriorator too, not just the silent-hypoxia case. A single-axis signal would pass G3 on patient 0
yet silently miss half the ward at S5. The position is trend-smoothed first (a trailing mean) so the
fast homeostatic swing does not inflate the baseline σ and drown the slow silent drift.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np

from styx.config import AEGIS_BASELINE_SAMPLES, AEGIS_K, AEGIS_SMOOTH_SAMPLES, AEGIS_SUSTAIN
from styx.state.embedding import Embedding, trajectory_path
from styx.synth.cohort import Patient


def _trailing_mean(x: np.ndarray, w: int) -> np.ndarray:
    """Causal trailing mean over ≤ w samples (partial at the start) — deterministic, no look-ahead."""
    cum = np.cumsum(np.insert(x, 0, 0.0))
    out = np.empty(x.size)
    for i in range(x.size):
        lo = max(0, i - w + 1)
        out[i] = (cum[i + 1] - cum[lo]) / (i + 1 - lo)
    return out


def aegis_signal(patient: Patient, emb: Embedding) -> np.ndarray:
    """Per-sample baseline departure of the *trend-smoothed* state position, in σ units (max axis)."""
    path = trajectory_path(patient, emb)
    smooth = np.column_stack([_trailing_mean(path[:, k], AEGIS_SMOOTH_SAMPLES) for k in range(2)])
    base = smooth[:AEGIS_BASELINE_SAMPLES]
    mu = base.mean(axis=0)
    sd = base.std(axis=0)
    sd[sd == 0.0] = 1e-9
    return np.abs((smooth - mu) / sd).max(axis=1)


def _first_sustained(mask: np.ndarray, sustain: int) -> int | None:
    """Index at which ``mask`` first completes ``sustain`` consecutive True values (the confirm point)."""
    run = 0
    for i, hot in enumerate(mask):
        run = run + 1 if hot else 0
        if run >= sustain:
            return i
    return None


def aegis_fire_index(
    patient: Patient,
    emb: Embedding,
    indices: Iterable[int] | None = None,
    *,
    k: float = AEGIS_K,
    sustain: int = AEGIS_SUSTAIN,
) -> int | None:
    """Re-score index at which AEGIS confirms a sustained baseline departure (None if it never does)."""
    confirm = _first_sustained(aegis_signal(patient, emb) > k, sustain)
    if confirm is None:
        return None
    if indices is None:
        return confirm
    for i in indices:  # serving semantics: first re-score at or after the confirm sample
        if i >= confirm:
            return int(i)
    return None
