"""Cohort assembly — frailty → Theograph history → conditioned physiology → labelled outcome.

DET-1: one seed tree. ``build_cohort(seed)`` spawns one child Generator per patient, so the
whole cohort is reproducible bit-for-bit and ``Cohort.equals`` is exact array equality.
The causal chain (PRD §9): latent frailty raises both the Theograph event density *and* the
*odds* of a crisis — outcome is a stochastic (not deterministic) function of frailty, so a model
on the observable history predicts it better than chance but never perfectly (gate G1 band).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

import numpy as np

from styx.config import CHANNELS, RESCORE_CADENCE_MIN, SEED, VITALS
from styx.synth.observations import generate_nurse_obs
from styx.synth.scenario import Archetype, generate_episode, time_grid

#: Per-channel baseline event rate + frailty loading (events ~ Poisson(base + load·frailty)).
_CHANNEL_BASE: float = 1.0
_CHANNEL_LOAD: float = 8.0

#: Outcome is sampled: P(adverse) = sigmoid(k·(frailty − midpoint)). k sets how learnable the
#: prior is — tuned so the history→outcome AUC sits in OUTCOME_AUC_BAND, not at a perfect 1.0.
_OUTCOME_K: float = 5.0
_OUTCOME_MIDPOINT: float = 0.5

#: Measurement noise (event units) on the observed comorbidity proxy — what a real model sees.
_COMORBIDITY_NOISE: float = 3.0

#: Deterioration shapes an escalator can take (drawn uniformly) — they span the oxy×effort plane.
_ESCALATOR_ARCHETYPES: tuple[Archetype, ...] = (
    Archetype.SILENT_HYPOXIA,
    Archetype.COMPENSATED,
    Archetype.COUPLED,
)


def _sigmoid(z: float) -> float:
    return 1.0 / (1.0 + float(np.exp(-z)))


class Outcome(enum.Enum):
    """Episode outcome label (the cohort's supervised target)."""

    RECOVERED = "recovered"
    ESCALATED = "escalated"


@dataclass(frozen=True)
class Patient:
    """One synthetic patient: lifelong history + the virtual-ward physiological episode."""

    pid: int
    frailty: float
    theograph: dict[str, int]  # channel -> multi-year event count (iterate via CHANNELS)
    comorbidity_index: float  # observed event-density proxy + measurement noise (not frailty)
    vitals: dict[str, np.ndarray]  # keyed by VITALS, each length N_SAMPLES
    outcome: Outcome
    archetype: Archetype  # the deterioration shape (STABLE for recovered)
    t_min: np.ndarray  # shared sim-minute time grid
    nurse_obs: dict[str, np.ndarray]  # NEWS2-comparator-only (systolic_bp, acvpu) — NOT in VITALS


@dataclass(frozen=True)
class Cohort:
    """A virtual ward of patients on a shared replay clock."""

    patients: tuple[Patient, ...]
    dt_min: int = field(default=0)  # set from the scenario grid in build_cohort
    rescore_cadence_min: int = RESCORE_CADENCE_MIN

    def silent_case(self) -> Patient:
        """The scripted index patient that carries the full G1 phenomenon (decoupling + breach)."""
        return self.patients[0]

    def equals(self, other: "Cohort") -> bool:
        """Exact (bit-identical) equality across streams, history, and labels — the DET-1 check."""
        if len(self.patients) != len(other.patients):
            return False
        for a, b in zip(self.patients, other.patients):
            if a.pid != b.pid or a.frailty != b.frailty or a.outcome is not b.outcome:
                return False
            if a.archetype is not b.archetype:
                return False
            if a.comorbidity_index != b.comorbidity_index:
                return False
            if any(a.theograph[c] != b.theograph[c] for c in CHANNELS):
                return False
            if any(not np.array_equal(a.vitals[v], b.vitals[v]) for v in VITALS):
                return False
            if any(not np.array_equal(a.nurse_obs[k], b.nurse_obs[k]) for k in a.nurse_obs):
                return False
        return True


def _theograph(rng: np.random.Generator, frailty: float) -> dict[str, int]:
    """Multi-year care-event counts whose density reflects (and so reveals) latent frailty."""
    return {c: int(rng.poisson(_CHANNEL_BASE + _CHANNEL_LOAD * frailty)) for c in CHANNELS}


def build_cohort(seed: int = SEED, n_patients: int = 50) -> Cohort:
    """Build a deterministic acute-respiratory-infection cohort (≥12 floor; 50 default for AUC).

    Patient 0 is the scripted silent case (forced escalating); its draw order is preserved so its
    decoupling lead and silent window are bit-identical to the validated baseline.
    """
    grid = time_grid()
    children = np.random.default_rng(seed).spawn(n_patients)
    patients: list[Patient] = []
    for pid, child in enumerate(children):
        if pid == 0:
            # Scripted silent-hypoxia index case — no frailty/outcome draw (keeps patient 0 stable).
            frailty, archetype = 0.85, Archetype.SILENT_HYPOXIA
        else:
            frailty = float(child.uniform(0.1, 0.9))
            p_adverse = _sigmoid(_OUTCOME_K * (frailty - _OUTCOME_MIDPOINT))
            if child.uniform() < p_adverse:  # outcome SAMPLED, not thresholded
                archetype = _ESCALATOR_ARCHETYPES[int(child.integers(len(_ESCALATOR_ARCHETYPES)))]
            else:
                archetype = Archetype.STABLE
        outcome = Outcome.RECOVERED if archetype is Archetype.STABLE else Outcome.ESCALATED
        theograph = _theograph(child, frailty)
        vitals = generate_episode(child, archetype=archetype)
        # Trailing draws (after the episode) so adding them cannot shift patient 0's vital stream.
        comorbidity = float(sum(theograph.values()) + child.normal(0.0, _COMORBIDITY_NOISE))
        nurse_obs = generate_nurse_obs(grid, child)  # comparator-only; drawn last (DET-1 safe)
        patients.append(
            Patient(pid, frailty, theograph, comorbidity, vitals, outcome, archetype, grid, nurse_obs)
        )
    return Cohort(tuple(patients), dt_min=int(grid[1] - grid[0]))
