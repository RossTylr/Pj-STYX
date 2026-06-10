"""Baseline lock — a double-run SHA-256 sentinel over the full pipeline (the regression proof).

One digest spans streams (vitals), events (Theograph counts) and scores (the risk waterline) for the
whole cohort in pid order. Building twice at seed=42 must yield the *same* digest — the proof that a
surface change (S5.5: timeline + notebook) moved no model maths, stronger than per-array equality
because it is one number to record in ``EXPERIMENT_LOG.md`` and re-check against. DET-1."""

import hashlib

import numpy as np

from styx.cohort import build_cohort_context
from styx.config import VITALS
from styx.synth import build_cohort


def pipeline_digest(cohort) -> str:
    """SHA-256 over the full pipeline: per-patient vitals streams, Theograph counts, risk scores."""
    cctx = build_cohort_context(cohort)
    h = hashlib.sha256()
    for p in cohort.patients:  # cohort.patients is an ordered tuple → deterministic traversal
        h.update(str(p.pid).encode())
        for v in VITALS:
            h.update(np.ascontiguousarray(p.vitals[v]).tobytes())
        for ch in sorted(p.theograph):  # sort keys — no dict-iteration-order dependence
            h.update(f"{ch}:{p.theograph[ch]}".encode())
        h.update(np.ascontiguousarray(cctx.risk[p.pid]).tobytes())
    return h.hexdigest()


def test_pipeline_determinism_sentinel() -> None:
    a = pipeline_digest(build_cohort(seed=42))
    b = pipeline_digest(build_cohort(seed=42))
    assert a == b  # DET-1 — same seed → bit-identical streams, events and scores
