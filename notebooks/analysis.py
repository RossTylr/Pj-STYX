"""Shared in-sample analysis helpers for the proof notebooks — the single source (no duplication).

Construct-validity measurement, **not** ward performance: one synthetic cohort scored in-sample.
The analyses live here so the notebooks that report them compute them once and cannot drift apart:
``trajectory_features`` (the per-patient history + silent-window telemetry panel — the single
source consumed by the saturation AUC *and* E3's survival model, same panel, two targets),
``saturation_aucs`` (history vs telemetry vs combined AUC — notebook 06 §1, notebook 10 §11) and
``conformal_coverage`` (empirical vs nominal cone coverage — notebook 10 §6; the same computation
notebook 05 Panel B performs inline). Pure analysis (LYR-1 spirit): reads a cohort + its prebuilt
context, runs no model maths of STYX's own, touches nothing in ``styx/``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from styx.config import CONFORMAL_ALPHA, FORECAST_WINDOW
from styx.forecast import project
from styx.synth import Outcome

#: The telemetry-panel feature names (the silent-window snapshot the saturation AUC + E3 Cox share).
TELEMETRY_FEATURES: tuple[str, ...] = ("risk_snap", "aegis_fired", "risk_slope")


def trajectory_features(cohort, cctx) -> pd.DataFrame:
    """Per-patient history + silent-window telemetry panel — the single source for the saturation
    AUC and E3's survival model (same panel, two targets). One row per patient, in pid order.

    Columns: ``pid``, ``history`` (observable ``comorbidity_index``), the three telemetry features
    ``risk_snap`` / ``aegis_fired`` / ``risk_slope`` at the silent-window frame ``cctx.default_idx``,
    and ``escalated`` (the binary outcome label, for the baseline contrast).
    """
    di = cctx.default_idx  # the silent-window frame (the demo's money shot)

    def _slope(pid: int) -> float:
        seg = cctx.risk[pid][max(0, di - FORECAST_WINDOW):di + 1]
        x = np.arange(len(seg)) - (len(seg) - 1) / 2
        return float(np.polyfit(x, seg, 1)[0]) if len(seg) > 1 else 0.0

    rows = [
        (
            p.pid,
            float(p.comorbidity_index),
            float(cctx.risk[p.pid][di]),
            1.0 if (cctx.aegis_idx[p.pid] is not None and cctx.aegis_idx[p.pid] <= di) else 0.0,
            _slope(p.pid),
            1 if p.outcome is Outcome.ESCALATED else 0,
        )
        for p in cohort.patients
    ]
    return pd.DataFrame(
        rows, columns=["pid", "history", "risk_snap", "aegis_fired", "risk_slope", "escalated"]
    )


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
    feats = trajectory_features(cohort, cctx)  # single-source panel (shared with E3's Cox)
    y = feats["escalated"].to_numpy()

    def auc(*cols) -> float:
        X = np.column_stack(cols)
        m = LogisticRegression(max_iter=1000).fit(X, y)
        return float(roc_auc_score(y, m.predict_proba(X)[:, 1]))

    hist = feats["history"].to_numpy()
    r_snap = feats["risk_snap"].to_numpy()
    aegis_fired = feats["aegis_fired"].to_numpy()
    r_slope = feats["risk_slope"].to_numpy()

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


@dataclass(frozen=True)
class Calibration:
    """In-sample survival calibration of an already-fitted Cox — predicted vs observed S(t)."""

    horizons: np.ndarray  # (H,) fixed horizons spanning the observed events
    predicted: dict  # group -> (H,) mean Cox-predicted survival
    observed: dict  # group -> (H,) Kaplan–Meier observed survival (censoring-aware)
    max_gap: dict  # group -> sup-norm |predicted − observed| (the discrepancy summary)
    c_index: float  # discrimination, carried from the same fitted model (no refit)


def survival_calibration(cph, surv_df, covs, *, group_col="arch", n_horizons=40) -> Calibration:
    """Mean Cox-predicted S(t) vs Kaplan–Meier observed S(t) at fixed horizons (E3 §4).

    Reuses the **already-fitted** ``cph`` (no refit — discrimination ``c_index`` is carried through
    unchanged). Censoring-aware via KM for the observed curve. ``max_gap`` is the sup-norm
    predicted-vs-observed discrepancy, computed ``overall`` and per ``group_col`` value — so a tight
    overall (calibration-in-the-large) cannot hide a miscalibrated subgroup. In-sample only.
    """
    from lifelines import KaplanMeierFitter  # lazy — keep the module import light for nb 06/10

    ev = surv_df.loc[surv_df.event == 1, "duration"].to_numpy()
    horizons = np.linspace(float(ev.min()), float(ev.max()), n_horizons)
    sf = cph.predict_survival_function(surv_df[covs], times=horizons)  # cols = surv_df.index
    predicted, observed, max_gap = {}, {}, {}

    def _add(name: str, mask: np.ndarray) -> None:
        km = KaplanMeierFitter().fit(surv_df.loc[mask, "duration"], surv_df.loc[mask, "event"])
        obs = np.array([float(km.predict(h)) for h in horizons])
        pred = sf[surv_df.index[mask]].mean(axis=1).to_numpy()
        predicted[name], observed[name] = pred, obs
        max_gap[name] = float(np.max(np.abs(pred - obs)))

    _add("overall", np.ones(len(surv_df), dtype=bool))
    for g in sorted(surv_df[group_col].unique()):
        _add(g, (surv_df[group_col] == g).to_numpy())
    return Calibration(horizons, predicted, observed, max_gap, float(cph.concordance_index_))
