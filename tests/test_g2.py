"""Gate G2 — state legibility. The latent axes are named, deterministic, and the silent case
drifts basin→attractor. Evidence comes from styx.state (LYR-1: imported, never reimplemented)."""

import numpy as np

from styx.config import LEGIBILITY_THRESHOLD
from styx.state import (
    axis_construct_corr,
    fit_embedding,
    is_legible,
    learn_basins,
    trajectory_drift,
    trajectory_path,
)
from styx.synth import build_cohort


def test_determinism_seed42() -> None:
    a, b = build_cohort(seed=42), build_cohort(seed=42)
    pa = trajectory_path(a.silent_case(), fit_embedding(a))
    pb = trajectory_path(b.silent_case(), fit_embedding(b))
    assert np.array_equal(pa, pb)  # DET-1 — same seed → identical coordinates


def test_axes_are_legible() -> None:
    cohort = build_cohort(seed=42)
    corrs = axis_construct_corr(cohort, fit_embedding(cohort))
    assert is_legible(corrs, LEGIBILITY_THRESHOLD), f"illegible axes: {corrs}"


def test_silent_case_drifts_to_attractor() -> None:
    cohort = build_cohort(seed=42)
    emb = fit_embedding(cohort)
    drift = trajectory_drift(cohort.silent_case(), emb, learn_basins(cohort, emb))
    assert drift > 0, f"silent case must drift basin→attractor, got {drift:.3f}"  # G1↔G2
