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

#: G3 headline floor — the at-cadence AEGIS→threshold lead must clear this. A regression guard set
#: just below the measured 210 sim-min lead (seed=42), NOT an adequacy claim; report the raw number.
AEGIS_LEAD_FLOOR_MIN: int = 180

#: G1 target — RR–SpO₂ decoupling must precede any single-signal breach by ≥ this (sim-minutes).
DECOUPLING_LEAD_MIN: int = 90

#: G1 band — history→outcome AUC must be learnable yet not perfect (too-learnable also fails).
OUTCOME_AUC_BAND: tuple[float, float] = (0.60, 0.90)

#: F2 forecast — trailing samples fit for the trend, and samples projected ahead (5 sim-min each).
FORECAST_WINDOW: int = 12  # 60 sim-min of trailing risk to fit the short-horizon trend
FORECAST_HORIZON: int = 24  # project 120 sim-min ahead — long enough to anticipate the crossing

#: UQ-1 — conformal miscoverage; band half-width at each horizon = the (1−α) residual quantile.
CONFORMAL_ALPHA: float = 0.1

#: F2 — the cone's upper edge must reach the threshold for this many consecutive re-scores before
#: the forecast "fires", so an early transient wobble in the risk trend cannot trip a false alarm.
FORECAST_SUSTAIN: int = 3

#: F7 AEGIS — personal baseline learned from this many leading (pre-decoupling) samples, then a
#: sustained ≥ K·σ departure of the 2-D state position over ≥ SUSTAIN samples is the silent flag.
AEGIS_BASELINE_SAMPLES: int = 24  # first 120 sim-min — stable, well before decoupling (sample 108)
AEGIS_SMOOTH_SAMPLES: int = 12  # trailing mean (60 sim-min) — strips fast homeostatic swing from the trend
AEGIS_K: float = 3.0  # departure threshold in baseline σ units
AEGIS_SUSTAIN: int = 3  # consecutive samples (15 sim-min) above K before AEGIS fires

#: G4 — CALLIOPE faithfulness floor: top-1 named risk driver must match the model's actual top
#: contributor (independent risk ablation) on at least this fraction of the held-out re-scores.
G4_FAITHFULNESS_FLOOR: float = 0.90

#: SIG-1 — the tight vital set that carries the decoupling (RR, SpO₂, HR, temp + one labs proxy).
VITALS: tuple[str, ...] = ("RR", "SpO2", "HR", "temp", "labs_proxy")

#: F1 state-space axes — the named physiological constructs each 2-D latent axis must track.
STATE_AXES: tuple[str, str] = ("oxygenation", "effort")

#: G2 target — each latent axis must correlate with its construct at |r| ≥ this, else fall back.
LEGIBILITY_THRESHOLD: float = 0.60

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
