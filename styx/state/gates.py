"""Gate-G2 measurement helpers — importable by tests/test_g2.py and notebook 02 alike.

LYR-1: the legibility evidence (axis ↔ construct correlation) and the basin→attractor drift are
computed here once and consumed by the test, the proof notebook, and ``fit_embedding``'s own
PCA-vs-constructed fork — never reimplemented. These read a fitted Embedding; they do not fit one.
"""

from __future__ import annotations

import numpy as np

from styx.state.constructs import effort, oxygenation
from styx.state.embedding import Basins, Embedding, _cohort_matrix, _pearson, trajectory_path
from styx.synth.cohort import Cohort, Patient
from styx.synth.gates import breach_index, decoupling_onset_index

_CONSTRUCTS = {"oxygenation": oxygenation, "effort": effort}


def axis_construct_corr(cohort: Cohort, emb: Embedding) -> dict[str, float]:
    """Pearson r of each latent axis against the construct it is labelled with, keyed by name.

    Scored over every sample in the cohort — the canonical legibility number for gate G2.
    """
    proj = ((_cohort_matrix(cohort) - emb.mean_) / emb.scale_) @ emb.components_.T
    series = {n: np.concatenate([fn(p) for p in cohort.patients]) for n, fn in _CONSTRUCTS.items()}
    return {lab: _pearson(proj[:, ax], series[lab]) for ax, lab in enumerate(emb.axis_labels)}


def is_legible(corrs: dict[str, float], threshold: float) -> bool:
    """Legible iff the axes track two *distinct* constructs, each at |r| ≥ threshold."""
    return len(corrs) == 2 and all(abs(r) >= threshold for r in corrs.values())


def trajectory_drift(patient: Patient, emb: Embedding, basins: Basins) -> float:
    """Net basin→attractor displacement over the silent→breach window (+ve = toward attractor).

    Projects the patient's latent travel from decoupling onset to first breach onto the unit
    direction toward its *nearest* crisis mode — the G1↔G2 link: the silent case should drift
    toward crisis. The nearest mode is chosen by the patient's position at breach, so the
    silent-hypoxia case selects the oxygenation-led attractor rather than the effort-led one.
    """
    path = trajectory_path(patient, emb)
    onset, breach = decoupling_onset_index(patient), breach_index(patient)
    if onset is None or breach is None:
        return 0.0
    mode = basins.nearest_attractor(path[breach])
    direction = basins.attractor_centers[mode] - basins.basin_center
    norm = float(np.linalg.norm(direction))
    if norm == 0:
        return 0.0
    return float(np.dot(path[breach] - path[onset], direction / norm))
