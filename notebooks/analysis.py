"""Shared in-sample analysis helpers for the proof notebooks — the single source (no duplication).

Construct-validity measurement, **not** ward performance: one synthetic cohort scored in-sample.
Two analyses live here so the notebooks that report them compute them once and cannot drift apart:
``saturation_aucs`` (history vs telemetry vs combined AUC — notebook 06 §1, notebook 10 §11) and
``conformal_coverage`` (empirical vs nominal cone coverage — notebook 10 §6; the same computation
notebook 05 Panel B performs inline). Pure analysis (LYR-1 spirit): reads a cohort + its prebuilt
context, runs no model maths of STYX's own, touches nothing in ``styx/``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from styx.config import CONFORMAL_ALPHA, FORECAST_WINDOW
from styx.forecast import project
from styx.synth import Outcome


@dataclass(frozen=True)
class Saturation:
    """The four headline AUCs (in-sample) plus the marginal value of telemetry over history."""

    history: float  # history-only (observable comorbidity_index)
    telemetry: float  # telemetry panel (silent-window risk snapshot, AEGIS-fired flag, risk slope)
    combined: float  # history + telemetry
    risk_snap: float  # telemetry single — risk snapshot at the silent-window frame
    aegis_fired: float  # telemetry single — AEGIS-fired-by-frame flag
    slope: float  # telemetry single — trailing risk slope

    @property
    def marginal(self) -> float:
        """R1's marginal value: combined − telemetry (≈ 0 ⇒ telemetry already saturates → descriptive)."""
        return self.combined - self.telemetry


def saturation_aucs(cohort, cctx) -> Saturation:
    """In-sample AUCs predicting ESCALATED from history / telemetry / combined (notebook 06 §1)."""
    pats = cohort.patients
    di = cctx.default_idx  # the silent-window frame (the demo's money shot)
    y = np.array([1 if p.outcome is Outcome.ESCALATED else 0 for p in pats])

    def auc(*cols) -> float:
        X = np.column_stack(cols)
        m = LogisticRegression(max_iter=1000).fit(X, y)
        return float(roc_auc_score(y, m.predict_proba(X)[:, 1]))

    hist = np.array([p.comorbidity_index for p in pats])
    r_snap = np.array([cctx.risk[p.pid][di] for p in pats])
    aegis_fired = np.array(
        [1.0 if (cctx.aegis_idx[p.pid] is not None and cctx.aegis_idx[p.pid] <= di) else 0.0
         for p in pats]
    )

    def _slope(pid: int) -> float:
        seg = cctx.risk[pid][max(0, di - FORECAST_WINDOW):di + 1]
        x = np.arange(len(seg)) - (len(seg) - 1) / 2
        return float(np.polyfit(x, seg, 1)[0]) if len(seg) > 1 else 0.0

    r_slope = np.array([_slope(p.pid) for p in pats])

    return Saturation(
        history=auc(hist),
        telemetry=auc(r_snap, aegis_fired, r_slope),
        combined=auc(hist, r_snap, aegis_fired, r_slope),
        risk_snap=auc(r_snap),
        aegis_fired=auc(aegis_fired),
        slope=auc(r_slope),
    )


@dataclass(frozen=True)
class Coverage:
    """Empirical conformal-cone coverage — pooled (marginal), not a per-patient guarantee."""

    per_horizon: np.ndarray  # (H,) empirical coverage at each horizon step
    mean: float  # mean over the horizon
    nominal: float  # the band's nominal target, 1 − α


def conformal_coverage(cctx) -> Coverage:
    """Empirical vs nominal cone coverage, swept over all patients and re-score anchors (nb 05 B).

    At every anchor and horizon step, is the realised risk inside the projected band? Coverage is
    **marginal** — pooled across the calibration cohort — exactly the claim the band makes, no more.
    """
    t = cctx.t_min
    horizon, n = cctx.band.size, t.size
    hits, total = np.zeros(horizon), np.zeros(horizon)
    for risk in cctx.risk.values():
        for now_idx in range(FORECAST_WINDOW - 1, n - 1):
            cone = project(risk, t, now_idx, cctx.band)
            for k in range(horizon):
                j = now_idx + 1 + k
                if j >= n:
                    break
                hits[k] += float(cone.lower[k] <= risk[j] <= cone.upper[k])
                total[k] += 1.0
    per_horizon = hits / np.maximum(total, 1.0)
    return Coverage(per_horizon, float(per_horizon.mean()), 1.0 - CONFORMAL_ALPHA)
