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
# not hidden (``styx.explain.NEWS2_PARTIAL_LABEL``). This adds no synthetic data and no model maths.

#: Escalation trigger: aggregate ≥ 5, OR any single parameter scores a red 3.
NEWS2_TRIGGER: int = 5


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


def news2_crossing(patient: Patient) -> float | None:
    """First sim-minute the partial NEWS2 reaches its escalation trigger (aggregate ≥ 5 OR a red 3).

    The UK standard's first escalation prompt — for this scenario it lands *after* AEGIS and the
    breach (the partial stays 0–1 through the silent window). None if it never triggers.
    """
    sub = _news2_subscores(patient)
    triggered = (sub.sum(axis=0) >= NEWS2_TRIGGER) | (sub.max(axis=0) >= 3)
    hits = np.flatnonzero(triggered)
    return float(patient.t_min[hits[0]]) if hits.size else None
