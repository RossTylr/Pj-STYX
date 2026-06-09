"""F1 — deterministic 2-D state embedding + learned basin / crisis-attractor geometry.

PCA-first (DET-1: full-SVD PCA on standardised vitals, no RNG → bit-identical coordinates).
Standardisation is essential: SpO₂ (94–100), labs_proxy (0–1) and HR (60–100) live on wildly
different scales, so an un-standardised PCA axis is just whichever vital has the largest raw
variance. ``fit_embedding`` auto-forks: keep PCA if its axes are legible against the named
constructs, else fall back to a hand-built oxygenation × effort projection (gate G2).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.decomposition import PCA

from styx.config import LEGIBILITY_THRESHOLD, NORMAL_RANGES, STATE_AXES, VITALS
from styx.state.constructs import effort, oxygenation
from styx.synth.cohort import _ESCALATOR_ARCHETYPES, Cohort, Outcome, Patient

_CONSTRUCTS = {"oxygenation": oxygenation, "effort": effort}


def _vital_matrix(p: Patient) -> np.ndarray:
    """Patient vitals as an (N_SAMPLES, 5) matrix, columns in VITALS order."""
    return np.column_stack([p.vitals[v] for v in VITALS])


def _cohort_matrix(cohort: Cohort) -> np.ndarray:
    """Every sample of every patient stacked into one (n_patients·N, 5) matrix."""
    return np.vstack([_vital_matrix(p) for p in cohort.patients])


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    if a.std() == 0 or b.std() == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


@dataclass(frozen=True, eq=False)
class Embedding:
    """A fitted linear vitals → 2-D map: standardise, then project onto two named axes."""

    mean_: np.ndarray  # (5,) per-channel mean (standardisation)
    scale_: np.ndarray  # (5,) per-channel std (zero guarded to 1.0)
    components_: np.ndarray  # (2, 5) axis loadings in standardised space
    axis_labels: tuple[str, str]  # the named construct each axis tracks
    mode: str  # "pca" | "constructed"

    def transform(self, vitals: np.ndarray) -> np.ndarray:
        """Map an (N, 5) VITALS matrix to (N, 2) latent coordinates."""
        return ((vitals - self.mean_) / self.scale_) @ self.components_.T


@dataclass(frozen=True, eq=False)
class Basins:
    """Learned geometry: the stability basin and one crisis attractor *per escalating archetype*.

    Multi-modal by construction (Phase 0): a single averaged attractor sits in the effort-led
    region, so the silent-hypoxia case — which drifts on oxygenation, away from effort — would
    never register risk. One mode per archetype lets each deteriorator approach its *nearest* mode.
    """

    basin_center: np.ndarray  # (2,)
    basin_radius: np.ndarray  # (2,) per-axis spread
    attractor_centers: np.ndarray  # (K, 2) one crisis mode per escalating archetype
    attractor_radii: np.ndarray  # (K, 2) per-axis spread of each mode
    attractor_labels: tuple[str, ...]  # archetype name per mode, in row order of the arrays

    def nearest_attractor(self, point: np.ndarray) -> int:
        """Index of the crisis mode whose centre is closest to ``point`` (Euclidean)."""
        return int(np.argmin(np.linalg.norm(self.attractor_centers - point, axis=1)))


def _constructed(mean_: np.ndarray, scale_: np.ndarray) -> Embedding:
    """Hand-built oxygenation × effort axes — legible by construction (G2 fallback)."""
    i = {v: k for k, v in enumerate(VITALS)}
    comp = np.zeros((2, len(VITALS)))
    comp[0, i["SpO2"]] = 1.0  # oxygenation axis
    comp[1, i["RR"]] = comp[1, i["HR"]] = 1.0 / np.sqrt(2.0)  # effort axis
    return Embedding(mean_, scale_, comp, STATE_AXES, "constructed")


def fit_embedding(cohort: Cohort) -> Embedding:
    """Fit the PCA embedding; keep it if legible, else fall back to the constructed axes."""
    x = _cohort_matrix(cohort)
    mean_ = x.mean(axis=0)
    scale_ = x.std(axis=0)
    scale_[scale_ == 0] = 1.0
    xs = (x - mean_) / scale_
    comp = PCA(n_components=2).fit(xs).components_.copy()
    proj = xs @ comp.T
    constructs = {
        n: np.concatenate([fn(p) for p in cohort.patients]) for n, fn in _CONSTRUCTS.items()
    }
    # Assign axis 0 to the construct it tracks best, axis 1 to the other; orient each to +corr.
    oxy_first = abs(_pearson(proj[:, 0], constructs["oxygenation"])) >= abs(
        _pearson(proj[:, 0], constructs["effort"])
    )
    labels = ("oxygenation", "effort") if oxy_first else ("effort", "oxygenation")
    for axis, label in enumerate(labels):
        if _pearson(proj[:, axis], constructs[label]) < 0:
            comp[axis] = -comp[axis]
    emb = Embedding(mean_, scale_, comp, labels, "pca")
    # Deferred import keeps the gates → embedding layering while reusing the one canonical corr.
    from styx.state.gates import axis_construct_corr, is_legible

    if is_legible(axis_construct_corr(cohort, emb), LEGIBILITY_THRESHOLD):
        return emb
    return _constructed(mean_, scale_)


def trajectory_path(patient: Patient, emb: Embedding) -> np.ndarray:
    """The full stay as an (N_SAMPLES, 2) path through the latent space."""
    return emb.transform(_vital_matrix(patient))


def now_position(patient: Patient, emb: Embedding) -> np.ndarray:
    """The latest latent coordinate — the pulsing *now* marker."""
    return trajectory_path(patient, emb)[-1]


def learn_basins(cohort: Cohort, emb: Embedding) -> Basins:
    """Basin = in-range samples (any patient); one attractor per escalating archetype.

    Crisis modes are grouped by ``patient.archetype`` (a fixed-order tuple, never dict order) so
    the geometry is fully deterministic — no clustering RNG (DET-1). Each mode is the empirical
    (mean, std) of the breach samples of that archetype's escalators.
    """
    proj, in_range, breach, arch = [], [], [], []
    for p in cohort.patients:
        proj.append(trajectory_path(p, emb))
        inr = np.ones(p.t_min.size, dtype=bool)
        out_any = np.zeros(p.t_min.size, dtype=bool)
        for v in VITALS:
            r = NORMAL_RANGES[v]
            out = (p.vitals[v] < r.low) | (p.vitals[v] > r.high)
            inr &= ~out
            out_any |= out
        in_range.append(inr)
        breach.append(out_any & (p.outcome is Outcome.ESCALATED))
        arch.append(np.full(p.t_min.size, p.archetype.value))
    pts = np.vstack(proj)
    inr_m, brc_m = np.concatenate(in_range), np.concatenate(breach)
    arch_m = np.concatenate(arch)
    centers, radii, labels = [], [], []
    for a in _ESCALATOR_ARCHETYPES:  # fixed order → deterministic mode rows
        mode_m = brc_m & (arch_m == a.value)
        if not mode_m.any():
            continue
        centers.append(pts[mode_m].mean(axis=0))
        radii.append(pts[mode_m].std(axis=0))
        labels.append(a.value)
    return Basins(
        pts[inr_m].mean(axis=0), pts[inr_m].std(axis=0),
        np.vstack(centers), np.vstack(radii), tuple(labels),
    )
