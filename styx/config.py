"""Single source of constants for STYX (DET-1: SEED lives here; no module-level RNG).

Placeholders here are tuned at their owning gates — RESCORE_CADENCE_MIN at G3,
THRESHOLDS as the risk/AEGIS slices land. Nothing in this module instantiates an RNG.
"""

from __future__ import annotations

from dataclasses import dataclass

#: DET-1 — the one seed used everywhere; pass into generators, never a module RNG.
SEED: int = 42

#: A2 serving window in sim-minutes; OWNED by gate G3 (must preserve the AEGIS→threshold lead).
RESCORE_CADENCE_MIN: int = 15

#: G1 target — RR–SpO₂ decoupling must precede any single-signal breach by ≥ this (sim-minutes).
DECOUPLING_LEAD_MIN: int = 90

#: SIG-1 — the tight vital set that carries the decoupling (RR, SpO₂, HR, temp + one labs proxy).
VITALS: tuple[str, ...] = ("RR", "SpO2", "HR", "temp", "labs_proxy")


@dataclass(frozen=True)
class Thresholds:
    """Escalation thresholds (placeholder values; tuned at S3/risk slice)."""

    risk_escalation: float = 0.5  # F4 absolute-risk escalation level on [0, 1]


#: Default threshold instance, imported by risk/forecast slices.
THRESHOLDS: Thresholds = Thresholds()
