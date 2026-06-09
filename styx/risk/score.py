"""F4 — continuous risk waterline + absolute escalation trigger.

Risk is a gradient on [0, 1], not a traffic light: it *rises during the silent window* via the
proximity term (approach to the nearest crisis mode — the value STYX adds over NEWS2), but only
*crosses the escalation threshold at breach* because the second term, an absolute NEWS2-style
range-exceedance (which includes ``labs_proxy``), is strictly zero while every vital is in range.
So the trigger is absolute and fires last — it cannot collapse onto AEGIS.

    risk = 0.5 · proximity  +  0.5 · exceedance        (each in [0, 1])

Proximity alone caps at 0.5, so risk can exceed the 0.5 threshold *only* once a vital actually
leaves its range — i.e. at the breach.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np

from styx.config import NORMAL_RANGES, THRESHOLDS, VITALS
from styx.state.embedding import Basins, Embedding, trajectory_path
from styx.synth.cohort import Patient


def _proximity(patient: Patient, emb: Embedding, basins: Basins) -> np.ndarray:
    """Fraction of the basin→nearest-mode distance travelled, per sample, clipped to [0, 1]."""
    path = trajectory_path(patient, emb)
    b = basins.basin_center
    prox = np.zeros(path.shape[0])
    for i, pos in enumerate(path):
        a = basins.attractor_centers[basins.nearest_attractor(pos)]
        d = a - b
        norm = float(np.linalg.norm(d))
        if norm == 0.0:
            continue
        prox[i] = float(np.dot(pos - b, d / norm)) / norm
    return np.clip(prox, 0.0, 1.0)


def _exceedance(patient: Patient) -> np.ndarray:
    """Worst-vital absolute range-exceedance per sample (0 in range), normalised by band width."""
    out = np.zeros(patient.t_min.size)
    for v in VITALS:
        r = NORMAL_RANGES[v]
        width = r.high - r.low
        x = patient.vitals[v]
        e = np.maximum.reduce([np.zeros_like(x), (r.low - x) / width, (x - r.high) / width])
        out = np.maximum(out, e)
    return np.clip(out, 0.0, 1.0)


def risk_series(patient: Patient, emb: Embedding, basins: Basins) -> np.ndarray:
    """The continuous risk waterline on [0, 1] — proximity that rises early, exceedance that fires late."""
    return np.clip(0.5 * _proximity(patient, emb, basins) + 0.5 * _exceedance(patient), 0.0, 1.0)


def escalation_fire_index(
    patient: Patient,
    emb: Embedding,
    basins: Basins,
    indices: Iterable[int] | None = None,
    *,
    threshold: float = THRESHOLDS.risk_escalation,
) -> int | None:
    """First re-score index at which the risk waterline reaches the absolute escalation threshold."""
    risk = risk_series(patient, emb, basins)
    candidates = range(risk.size) if indices is None else indices
    for i in candidates:
        if risk[i] >= threshold:
            return int(i)
    return None
