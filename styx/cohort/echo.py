"""F10 ECHO — deterministic shape-aware retrieval of the nearest past trajectories.

Pure (LYR-1): no Streamlit, no I/O. ECHO is *grounding, not prediction* — it surfaces other
synthetic patients whose course-so-far most resembles the focus patient's, and shows how *they*
turned out. It never says "this patient will": self is excluded, ties break on pid (DET-1), and the
honesty framing rides in the labels (other synthetic patients; synthetic outcomes; illustration).

The match is on *shape* — a fixed-length resample of the 2-D state-space path up to the clock, not a
single reading — so the four archetypes (which separate in the embedding) retrieve like with like.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from styx.cohort.ranking import CohortContext
from styx.state import trajectory_path

#: Retrieval size and the fixed resample length of the shape key.
ECHO_K: int = 3
ECHO_RESAMPLE: int = 32


@dataclass(frozen=True)
class EchoNeighbour:
    """One retrieved look-alike: a synthetic patient, its distance, and its synthetic outcome."""

    pid: int
    distance: float
    outcome: str  # the neighbour's synthetic Outcome.value ("recovered" | "escalated")
    archetype: str


def _shape_key(cctx: CohortContext, pid: int, now_idx: int) -> np.ndarray:
    """The course-so-far as a fixed-length shape vector (resampled by normalised sample index).

    Index-resampling (not arc-length) is fully deterministic and robust at tiny ``now_idx`` — it
    never divides by a zero-length path — so two stays of different durations still compare on shape.
    """
    patient = cctx.cohort.patients[pid]
    path = trajectory_path(patient, cctx.emb)[: now_idx + 1]  # (m, 2)
    m = path.shape[0]
    s_src = np.linspace(0.0, 1.0, m)
    s_dst = np.linspace(0.0, 1.0, ECHO_RESAMPLE)
    x = np.interp(s_dst, s_src, path[:, 0])
    y = np.interp(s_dst, s_src, path[:, 1])
    return np.concatenate([x, y])  # (2 * ECHO_RESAMPLE,)


def echo_neighbours(
    cctx: CohortContext, focus_pid: int, now_idx: int, *, k: int = ECHO_K
) -> tuple[EchoNeighbour, ...]:
    """The ``k`` nearest trajectories to ``focus_pid`` by shape, excluding self (pid tiebreak)."""
    focus = _shape_key(cctx, focus_pid, now_idx)
    scored: list[EchoNeighbour] = []
    for p in cctx.cohort.patients:
        if p.pid == focus_pid:  # ECHO never matches the patient to themselves
            continue
        dist = float(np.linalg.norm(_shape_key(cctx, p.pid, now_idx) - focus))
        scored.append(EchoNeighbour(p.pid, dist, p.outcome.value, p.archetype.value))
    scored.sort(key=lambda n: (n.distance, n.pid))  # deterministic: distance, then pid (DET-1)
    return tuple(scored[:k])
