"""R3 CADUCEUS — the breathing–oxygen decoupling onset, read off the G1 coherence series.

A *floor* reach: temporal-mechanistic, **not predictive**. It surfaces *why* the silent
deterioration is silent — the RR–SpO₂ homeostatic coupling collapses before any single vital
leaves its range — and never claims better discrimination or lift (S5.5 is binding: telemetry
saturates AUC 1.000 in-sample). This module *reads* the existing G1 computation
(``synth.gates.windowed_coherence`` / ``decoupling_onset_index`` / ``decoupling_lead_min`` —
the same maths that produced the G1 lead 200); it never recomputes coherence.

Augmentation, not re-derivation (LYR-1, pure — no Streamlit, no I/O, no RNG): reach imports
core, core never imports reach. The cascade verdict reads AEGIS off the single S3 source
(``anticipation.fire_times``); nothing in synth/forecast/risk is touched, so the digest is
unchanged by construction.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from styx.anticipation import fire_times
from styx.config import RESCORE_CADENCE_MIN
from styx.synth.cohort import Cohort, Patient
from styx.synth.gates import (
    breach_index,
    decoupling_lead_min,
    decoupling_onset_index,
    has_silent_window,
    windowed_coherence,
)

# A decoupling onset counts as its *own* STYX marker only if it would surface at least one
# served re-score before AEGIS — i.e. it leads AEGIS by more than one cadence step.
_DETECTABLE_MARGIN_MIN: int = RESCORE_CADENCE_MIN


@dataclass(frozen=True)
class DecouplingOnset:
    """The decoupling onset, read off the G1 coherence series — recomputes nothing."""

    onset_index: int  # first sample of the sustained RR–SpO2 coherence collapse (from gates)
    onset_min: float  # sim-minute of that onset (p.t_min[onset_index])
    coherence: np.ndarray  # the windowed_coherence series — single source for the R3a.2 face
    g1_lead_min: float  # decoupling_lead_min(p) — reproduces the G1 lead (onset → breach)
    breach_min: float  # sim-minute of the first sustained single-signal breach the lead measures to
    silent_window: bool  # has_silent_window(p) — claim-integrity (in-range + SpO2 falling)


@dataclass(frozen=True)
class CascadeVerdict:
    """The cascade gate output: how many STYX markers the eventual 6-d state-space carries."""

    onset_min: float  # decoupling onset (sim-min), measured directly off the coherence series
    aegis_min: float  # AEGIS fire (sim-min) from anticipation.fire_times — the single S3 source
    gap_min: float  # aegis_min − onset_min  (> 0 ⇒ decoupling leads AEGIS)
    detectably_earlier: bool  # gap exceeds one re-score cadence
    markers: int  # 3 if decoupling is detectably earlier than AEGIS, else 2 (near-coincident)


def decoupling_onset(p: Patient) -> DecouplingOnset:
    """Read the decoupling onset and the G1 lead off the existing coherence computation."""
    onset = decoupling_onset_index(p)
    breach = breach_index(p)
    if onset is None or breach is None:
        raise ValueError("silent case carries no decoupling onset / breach — G1 phenomenon absent")
    return DecouplingOnset(
        onset_index=onset,
        onset_min=float(p.t_min[onset]),
        coherence=windowed_coherence(p.vitals["RR"], p.vitals["SpO2"]),
        g1_lead_min=decoupling_lead_min(p),
        breach_min=float(p.t_min[breach]),
        silent_window=has_silent_window(p),
    )


def cascade_verdict(
    cohort: Cohort, patient: Patient, cadence_min: int = RESCORE_CADENCE_MIN
) -> CascadeVerdict:
    """Compare the decoupling onset to the AEGIS fire and count the STYX markers (the gate output).

    Measures, does not assume: the onset is the raw mechanism onset; AEGIS is the served signal
    from the same source G3 uses. A decoupling onset is its own marker only when it leads AEGIS by
    more than one re-score cadence; otherwise the two are near-coincident (2 markers: AEGIS · F4).
    """
    onset = decoupling_onset(patient).onset_min
    aegis = fire_times(cohort, patient, cadence_min).aegis_min
    if aegis is None:
        raise ValueError("AEGIS never fires — cannot place the decoupling onset in the cascade")
    gap = aegis - onset
    earlier = gap > _DETECTABLE_MARGIN_MIN
    return CascadeVerdict(
        onset_min=onset,
        aegis_min=aegis,
        gap_min=gap,
        detectably_earlier=earlier,
        markers=3 if earlier else 2,
    )
