"""styx.state — F1 embedding · stability basin / crisis attractor.

Public surface for the gate test and the proof notebook (LYR-1: import, never reimplement).
"""

from styx.state.constructs import effort, oxygenation
from styx.state.embedding import (
    Basins,
    Embedding,
    fit_embedding,
    learn_basins,
    now_position,
    trajectory_path,
)
from styx.state.gates import axis_construct_corr, is_legible, trajectory_drift

__all__ = [
    "Basins",
    "Embedding",
    "axis_construct_corr",
    "effort",
    "fit_embedding",
    "is_legible",
    "learn_basins",
    "now_position",
    "oxygenation",
    "trajectory_drift",
    "trajectory_path",
]
