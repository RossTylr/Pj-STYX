"""Pure display helpers — turn model outputs into display-ready primitives (LYR-1).

No Streamlit, no I/O, no RNG: the *computation* side of presentation (the copy side lives in
``styx.explain``, the colour side in ``styx.viz``). Pages and notebooks call these so a page
never does arithmetic of its own — it only looks up copy and renders what these return.
"""

from __future__ import annotations

import numpy as np

import styx
from styx.config import SEED
from styx.synth.cohort import Patient


def footer_text() -> str:
    """Build + seed provenance line for every page (the determinism discipline, on screen)."""
    return f"STYX v{styx.__version__} · seed {SEED} · synthetic replay"


def styx_index(risk: float) -> int:
    """The risk waterline as a 0–100 integer index — a legible anchor, *not* a NEWS2 score.

    (6f) STYX has only RR/SpO₂/HR/Temp, so it cannot compute a full NEWS2; this is its own
    trajectory index. The caption ``styx.explain.SCORE_CAPTION`` carries the "not NEWS2" warning.
    """
    return int(min(100, max(0, round(risk * 100))))


def sim_clock(t_min: float) -> str:
    """A sim-minute as a ``HH:MM`` stay-clock stamp — the honest provenance of a score (6c)."""
    total = int(round(t_min))
    return f"{total // 60:02d}:{total % 60:02d}"


def eta_ordinal(eta_soonest_min: float | None) -> str:
    """The cone-derived ETA as an ordinal band key (6i) — never a spurious exact minute (UQ-1).

    Bands the *soonest* crossing (the cone's upper edge — the earliest credible escalation).
    Returns one of ``styx.explain.ETA_BANDS``' keys; confidence is shown separately, visually.
    """
    if eta_soonest_min is None:
        return "unclear"
    if eta_soonest_min < 30:
        return "lt30"
    if eta_soonest_min < 60:
        return "30_60"
    if eta_soonest_min <= 120:
        return "1_2h"
    return "gt2h"


# --- Partial NEWS2 comparator (Scale 1) ------------------------------------------------------
# A read-only, named-standard A/B baseline computed over the 4 modelled params (RR, SpO₂, HR,
# Temp). Scale 1 is the correct scale for this scenario (acute respiratory infection — *not* COPD;
# Scale 2 would mis-score a 97% baseline). The missing 3 of 7 params (systolic BP, consciousness,
# O₂ flag) are normal here by construction, so the 4-param partial equals the full score — labelled,
# not hidden (``styx.explain.NEWS2_COMPARATOR_LABEL``). This adds no synthetic data and no model maths.
#
# Cadence model (one stated model, never a mix): NEWS2 scores the wearable vitals *continuously* on
# the telemetry grid — the same stream STYX sees, so STYX wins no frequency advantage. (Nurse-entered
# params, when present, are scored at intermittent obs rounds, step-held — see ``styx.synth.observations``.)

#: Escalation rule (RCP 2017) — the *earliest* of two prompts fires the trigger: the aggregate
#: reaching ``NEWS2_TRIGGER``, OR any single parameter scoring a red ``NEWS2_RED``. The single-
#: parameter red is load-bearing in the silent scenario: the aggregate never reaches 5 (it peaks at
#: 3), so the SpO₂ ≤91 red at 1010 sim-min is what fires NEWS2 — an aggregate-only trigger would
#: never fire and the comparison would be vacuous.
NEWS2_TRIGGER: int = 5
NEWS2_RED: int = 3


def _rr_score(rr: np.ndarray) -> np.ndarray:
    return np.select([rr <= 8, rr <= 11, rr <= 20, rr <= 24], [3, 1, 0, 2], default=3)


def _spo2_scale1_score(spo2: np.ndarray) -> np.ndarray:
    return np.select([spo2 <= 91, spo2 <= 93, spo2 <= 95], [3, 2, 1], default=0)


def _hr_score(hr: np.ndarray) -> np.ndarray:
    return np.select([hr <= 40, hr <= 50, hr <= 90, hr <= 110, hr <= 130], [3, 1, 0, 1, 2], default=3)


def _temp_score(temp: np.ndarray) -> np.ndarray:
    return np.select([temp <= 35.0, temp <= 36.0, temp <= 38.0, temp <= 39.0], [3, 1, 0, 1], default=2)


def _news2_subscores(patient: Patient) -> np.ndarray:
    """Per-sample NEWS2 Scale-1 subscores for the 4 modelled params, shape (4, N)."""
    v = patient.vitals
    return np.vstack([
        _rr_score(v["RR"]), _spo2_scale1_score(v["SpO2"]), _hr_score(v["HR"]), _temp_score(v["temp"]),
    ])


def news2_partial(patient: Patient) -> np.ndarray:
    """Aggregate partial NEWS2 (Scale 1) per sample — the named-standard comparator (read-only)."""
    return _news2_subscores(patient).sum(axis=0)


def _news2_escalates(subscores: np.ndarray) -> np.ndarray:
    """Per-sample boolean for the RCP earliest-of escalation rule over a ``(k, N)`` subscore stack.

    Fires where the aggregate reaches ``NEWS2_TRIGGER`` OR any single parameter scores a red
    ``NEWS2_RED``. The one rule, shared by the partial (4-param) and complete (6-param) comparators
    so both read an identical, explicit trigger — never an incidental ``|``.
    """
    return (subscores.sum(axis=0) >= NEWS2_TRIGGER) | (subscores.max(axis=0) >= NEWS2_RED)


def _first_crossing_min(patient: Patient, subscores: np.ndarray) -> float | None:
    """First sim-minute the escalation rule fires over ``subscores``; None if it never does."""
    hits = np.flatnonzero(_news2_escalates(subscores))
    return float(patient.t_min[hits[0]]) if hits.size else None


def news2_crossing(patient: Patient) -> float | None:
    """First sim-minute the partial NEWS2 reaches its escalation trigger (aggregate ≥ 5 OR a red 3).

    The UK standard's first escalation prompt — for this scenario it lands *after* AEGIS and the
    breach (the partial stays 0–1 through the silent window, then the SpO₂ ≤91 red fires it). None
    if it never triggers.
    """
    return _first_crossing_min(patient, _news2_subscores(patient))


# --- Complete NEWS2 comparator (Scale 1, 6 of 7) ---------------------------------------------
# The partial above scores only the 4 wearable streams. The two NEWS2 params a wearable cannot
# capture — systolic BP and consciousness (ACVPU) — are recorded by a nurse on a 4-hourly obs round
# (``styx.synth.observations``) and folded in here, so the comparator is a *complete* NEWS2 but for
# the binary O₂-uplift flag (0 on room air in this scenario). The nurse obs feed ONLY this lane,
# never STYX's model. They are preserved through the silent window (BP band 0, ACVPU Alert), so the
# completed score equals the partial here — the named-standard baseline, now un-cherry-picked.


def _bp_score(systolic: np.ndarray) -> np.ndarray:
    return np.select([systolic <= 90, systolic <= 100, systolic <= 110, systolic <= 219],
                     [3, 2, 1, 0], default=3)


def _acvpu_score(acvpu: np.ndarray) -> np.ndarray:
    """ACVPU: Alert (code 0) scores 0; any other level (new confusion / V / P / U) is a red 3."""
    return np.where(acvpu <= 0, 0, 3)


def _news2_complete_subscores(patient: Patient) -> np.ndarray:
    """Per-sample subscores for all 6 scored params (4 wearable + nurse BP + ACVPU), shape (6, N)."""
    obs = patient.nurse_obs
    return np.vstack([
        _news2_subscores(patient), _bp_score(obs["systolic_bp"]), _acvpu_score(obs["acvpu"]),
    ])


def news2_complete(patient: Patient) -> np.ndarray:
    """Aggregate complete NEWS2 (Scale 1, 6 of 7) per sample — wearable streams + nurse obs."""
    return _news2_complete_subscores(patient).sum(axis=0)


#: The six scored NEWS2 params, in the row order of ``_news2_complete_subscores`` (4 wearable
#: streams + the two nurse-obs params). Plain display labels — the ward card's parameter pins.
NEWS2_PARAM_LABELS: tuple[str, ...] = ("RR", "SpO₂", "HR", "Temp", "BP", "ACVPU")


def news2_subscores_at(patient: Patient, idx: int) -> dict[str, int]:
    """The six scored NEWS2 Scale-1 subscores at one sample (display helper for the ward card).

    A read-only slice of the existing complete-comparator subscores — no new scoring, no synthetic
    data, no model maths. ``idx`` is a sample index on the shared telemetry grid (the replay clock).
    """
    col = _news2_complete_subscores(patient)[:, idx]
    return {label: int(s) for label, s in zip(NEWS2_PARAM_LABELS, col)}


def news2_complete_crossing(patient: Patient) -> float | None:
    """First sim-minute the complete NEWS2 fires, by the same earliest-of rule over all 6 subscores.

    A single red from *any* of the six escalates (not aggregate-only). With BP/ACVPU preserved here
    the binding prompt is still the SpO₂ ≤91 red, so this equals ``news2_crossing`` for this scenario.
    """
    return _first_crossing_min(patient, _news2_complete_subscores(patient))
