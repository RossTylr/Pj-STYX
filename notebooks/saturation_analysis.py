"""Shared saturation analysis for notebooks 06 and 10 — the single source (no duplication).

Construct-validity measurement, **not** ward performance: one synthetic cohort scored in-sample.
It asks whether an in-sample logistic regression recovers the scripted ESCALATED outcome from
history alone, telemetry alone, or both — so the *marginal* value of the telemetry/trajectory panel
over history can be read off. Lifted verbatim from notebook 06 §1 so both notebooks compute it once
and can never drift apart. Pure analysis (LYR-1 spirit): reads a cohort + its prebuilt context, runs
no model maths of STYX's own, touches nothing in ``styx/``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from styx.config import FORECAST_WINDOW
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
