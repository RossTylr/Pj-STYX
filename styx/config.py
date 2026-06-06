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

#: G1 band — history→outcome AUC must be learnable yet not perfect (too-learnable also fails).
OUTCOME_AUC_BAND: tuple[float, float] = (0.60, 0.90)

#: SIG-1 — the tight vital set that carries the decoupling (RR, SpO₂, HR, temp + one labs proxy).
VITALS: tuple[str, ...] = ("RR", "SpO2", "HR", "temp", "labs_proxy")

#: Theograph care-event channels (Layer-1/3). Fixed order — iterate this, never dict order.
CHANNELS: tuple[str, ...] = (
    "primary_care",
    "ae",
    "non_elective_admission",
    "outpatient",
    "mental_health",
    "social_care",
)


@dataclass(frozen=True)
class VitalRange:
    """Clinical normal-range bounds for one vital (a breach is leaving [low, high])."""

    low: float
    high: float


#: Clinical absolute normal ranges per vital (keys align to VITALS). Owned here as the single
#: source — used by S1 (breach + silent-window checks) and S3 (styx/risk absolute threshold).
NORMAL_RANGES: dict[str, VitalRange] = {
    "RR": VitalRange(12.0, 20.0),  # breaths/min
    "SpO2": VitalRange(94.0, 100.0),  # %
    "HR": VitalRange(60.0, 100.0),  # bpm
    "temp": VitalRange(36.0, 37.8),  # °C
    "labs_proxy": VitalRange(0.0, 1.0),  # unit-scaled inflammation proxy
}


@dataclass(frozen=True)
class Thresholds:
    """Escalation thresholds (placeholder values; tuned at S3/risk slice)."""

    risk_escalation: float = 0.5  # F4 absolute-risk escalation level on [0, 1]


#: Default threshold instance, imported by risk/forecast slices.
THRESHOLDS: Thresholds = Thresholds()
