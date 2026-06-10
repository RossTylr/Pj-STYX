"""F8 — CALLIOPE: a strict, template-only rationale over the model's real top-k attribution.

Hard Rule 5/6: never free text, never a signal outside the closed vocabulary, never a phenomenon
the model didn't actually attribute. CALLIOPE reads the read-only accessors in ``styx.risk`` and
fills fixed templates — the headline names the **top-1 risk driver** (the exactly-additive risk
decomposition, so the choice is unambiguous and faithful by construction — gate G4), and the
expand surfaces the AEGIS "why this is early" context (departure direction, breathing–oxygen
decoupling) drawn from the same real signals.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from styx.config import FORECAST_WINDOW, NORMAL_RANGES, THRESHOLDS, VITALS
from styx.risk import (
    aegis_axis_departures,
    decoupling_drop,
    exceedance_per_vital,
    proximity_components,
    risk_series,
)
from styx.state.embedding import Basins, Embedding, trajectory_path
from styx.synth.cohort import Patient

#: The closed named vocabulary — CALLIOPE may name nothing else (G4).
OXY_PROX = "oxygenation proximity"
EFFORT_PROX = "effort proximity"
EXCEEDANCE = "per-vital exceedance"
DECOUPLING = "breathing–oxygen decoupling"
DEPARTURE = "departure direction"
VOCABULARY: tuple[str, ...] = (OXY_PROX, EFFORT_PROX, EXCEEDANCE, DECOUPLING, DEPARTURE)
_ORDER = {t: i for i, t in enumerate(VOCABULARY)}  # deterministic tie-break

_STABLE_EPS = 1e-3  # below this, no term is "driving" risk → the stable template
_SLOPE_EPS = 1e-4
_DEPART_FLOOR = 1.0  # σ — name the departure direction once it is a real baseline departure
_DECOUP_FLOOR = 0.05  # coherence-drop units — name decoupling once it is real
_SIGMA_CLAMP = 8.0  # above this, render the departure in words — "26σ" reads as a pegged meter
_ADDITIVE_TOL = 1e-9  # contributions reconstruct risk to here (false once the proximity clips)


@dataclass(frozen=True)
class Rationale:
    """A filled CALLIOPE rationale at one re-score index — regime-aware (silent vs threshold-crossed).

    Post-breach the proximity overshoots the attractor and clips, so the additive contributor split
    no longer sums to the displayed risk: ``additive`` goes False and the renderer must suppress the
    contributor panel (showing it would display 1.30 against a 1.00 risk). The headline verb tracks
    the regime so it never says "approaching" a mode the patient already crashed through.
    """

    headline: str  # one tight clinician-facing line (regime-aware)
    regime: str  # "silent" (pre-threshold) | "crossed" (risk ≥ escalation threshold)
    additive: bool  # top_k sums to the displayed risk → safe to render as contributions
    top_k: tuple[tuple[str, float], ...]  # ranked risk terms — the G4 faithfulness target
    context: tuple[str, ...]  # AEGIS context lines (σ-clamped) — regime-independent
    terms: tuple[str, ...]  # every vocabulary term named (closed-set guarantee)


def _direction(series: np.ndarray, idx: int, window: int = FORECAST_WINDOW) -> str:
    """Trailing-window trend of a series at ``idx`` → 'rising' | 'falling' | 'flat'."""
    lo = max(0, idx - window + 1)
    if idx - lo < 2:
        return "flat"
    x = np.arange(lo, idx + 1, dtype=float)
    slope = float(np.polyfit(x, series[lo : idx + 1], 1)[0])
    return "rising" if slope > _SLOPE_EPS else "falling" if slope < -_SLOPE_EPS else "flat"


def _mode_at(patient: Patient, emb: Embedding, basins: Basins, idx: int) -> str:
    """Human-readable nearest crisis-mode label at the sample (e.g. 'silent hypoxia')."""
    pos = trajectory_path(patient, emb)[idx]
    return basins.attractor_labels[basins.nearest_attractor(pos)].replace("_", " ")


def _headline_phrase(term: str, patient: Patient, emb: Embedding, basins: Basins, idx: int) -> str:
    """Fill the fixed template for the dominant risk term — slots from real values only."""
    mode = _mode_at(patient, emb, basins, idx)
    if term == OXY_PROX:
        return f"{_direction(patient.vitals['SpO2'], idx)} oxygenation, approaching the {mode} mode"
    if term == EFFORT_PROX:
        return f"{_direction(patient.vitals['RR'], idx)} effort, approaching the {mode} mode"
    worst = max(VITALS, key=lambda v: exceedance_per_vital(patient)[v][idx])
    side = "above" if patient.vitals[worst][idx] > NORMAL_RANGES[worst].high else "below"
    return f"{worst} {side} range — absolute breach"


def _context_lines(patient: Patient, emb: Embedding, idx: int) -> tuple[list[str], list[str]]:
    """The AEGIS 'why this is early' lines (σ-clamped), with the vocab terms they name."""
    lines: list[str] = []
    named: list[str] = []
    dep = aegis_axis_departures(patient, emb)
    dom_axis = max(dep, key=lambda a: float(dep[a][idx]))
    dep_mag = float(dep[dom_axis][idx])
    if dep_mag >= _DEPART_FLOOR:
        sigma = ("far beyond personal baseline" if dep_mag > _SIGMA_CLAMP
                 else f"{dep_mag:.1f}σ from personal baseline")
        lines.append(f"{DEPARTURE}: {dom_axis} {sigma}")
        named.append(DEPARTURE)
    dec_mag = float(decoupling_drop(patient)[idx])
    if dec_mag >= _DECOUP_FLOOR:
        lines.append(f"{DECOUPLING}: RR–SpO₂ coherence down {dec_mag:.2f}")
        named.append(DECOUPLING)
    return lines, named


def explain(patient: Patient, emb: Embedding, basins: Basins, idx: int) -> Rationale:
    """Build the CALLIOPE rationale at re-score index ``idx`` (strict template; vocab-closed)."""
    pc = proximity_components(patient, emb, basins)
    ev = exceedance_per_vital(patient)
    risk = float(risk_series(patient, emb, basins)[idx])
    worst = max(VITALS, key=lambda v: ev[v][idx])
    risk_terms = [
        (OXY_PROX, 0.5 * float(pc[OXY_PROX][idx])),
        (EFFORT_PROX, 0.5 * float(pc[EFFORT_PROX][idx])),
        (EXCEEDANCE, 0.5 * float(ev[worst][idx])),
    ]
    top_k = tuple(sorted(risk_terms, key=lambda t: (-t[1], _ORDER[t[0]])))
    regime = "crossed" if risk >= THRESHOLDS.risk_escalation else "silent"
    additive = abs(sum(v for _, v in top_k) - risk) < _ADDITIVE_TOL

    lead, lead_val = top_k[0]
    if lead_val < _STABLE_EPS:
        headline = f"Patient {patient.pid}: stable — risk {risk:.2f}, no dominant driver"
        return Rationale(headline, regime, additive, top_k, (), ())

    mode = _mode_at(patient, emb, basins, idx)
    if regime == "crossed":
        headline = f"Patient {patient.pid}: threshold crossed — in the {mode} mode (risk {risk:.2f})"
    else:
        headline = f"Patient {patient.pid}: {_headline_phrase(lead, patient, emb, basins, idx)} " \
                   f"(risk {risk:.2f})"

    context, ctx_named = _context_lines(patient, emb, idx)
    named = [name for name, _ in top_k] + ctx_named
    return Rationale(headline, regime, additive, top_k, tuple(context), tuple(named))
