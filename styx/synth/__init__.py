"""styx.synth — F5 generator · scenario · cohort · replay.

Public surface for the gate test and the proof notebook (LYR-1: import, never reimplement).
"""

from styx.synth.cohort import Cohort, Outcome, Patient, build_cohort
from styx.synth.gates import (
    cohort_outcome_auc,
    decoupling_lead_min,
    has_silent_window,
    replay_windows,
    windowed_coherence,
)

__all__ = [
    "Cohort",
    "Outcome",
    "Patient",
    "build_cohort",
    "cohort_outcome_auc",
    "decoupling_lead_min",
    "has_silent_window",
    "replay_windows",
    "windowed_coherence",
]
