"""R1 history-as-prior — a *descriptive* hazard stratification over the cohort (no lift claim).

The S5.5 finding is binding: telemetry saturates in-sample (AUC 1.000), so no reach claims
predictive lift. R1's contribution is description — denser Theograph care-history stratifies the
deterioration hazard (shorter time-to-escalation), reported as a hazard ratio + stratified survival
+ a c-index, never an accuracy claim.

Augmentation, not re-derivation (LYR-1, pure — no Streamlit, no I/O): time-to-escalation is *read
off* the existing risk waterline (``CohortContext.risk`` crossing ``threshold``), recomputing nothing
in synth/forecast/risk. lifelines (Cox/KM/log-rank) is deterministic — no RNG, DET-1 safe.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.statistics import logrank_test

from styx.cohort.ranking import CohortContext

_RESIDUAL_QUANTILE: float = 0.25  # bottom-quartile care history — matches ranking.new_low_history


@dataclass(frozen=True)
class KMCurve:
    """One Kaplan–Meier survival step-curve for a density stratum (data for the R1b viz builder)."""

    t_min: np.ndarray  # step times (sim-minutes)
    survival: np.ndarray  # S(t) — fraction not-yet-escalated
    label: str  # "denser history" | "thinner history"


@dataclass(frozen=True)
class HazardStratification:
    """The descriptive R1 result: how care-history density stratifies time-to-escalation."""

    hazard_ratio: float  # Cox HR per +1 care-event of history (>1 ⇒ denser → escalates sooner)
    hr_ci: tuple[float, float]  # 95% CI on the HR
    c_index: float  # Cox concordance — discrimination, NOT a lift claim
    logrank_p: float  # high- vs low-density stratum separation
    high: KMCurve  # above-median density stratum
    low: KMCurve  # at/below-median density stratum
    residual_pids: tuple[int, ...]  # thin history yet escalated — the honest residual (pid 39)
    n_events: int


def _crossing_min(risk: np.ndarray, t_min: np.ndarray, threshold: float) -> tuple[float, int]:
    """Time-to-escalation off the waterline: first sample risk reaches ``threshold`` (event=1),
    else right-censored at episode end (event=0). Reads the MVP risk series — derives nothing."""
    hits = np.flatnonzero(risk >= threshold)
    return (float(t_min[hits[0]]), 1) if hits.size else (float(t_min[-1]), 0)


def survival_table(cctx: CohortContext) -> pd.DataFrame:
    """One right-censored survival row per patient: ``pid, duration_min, event, density``."""
    rows = []
    for p in cctx.cohort.patients:
        duration, event = _crossing_min(cctx.risk[p.pid], cctx.t_min, cctx.threshold)
        rows.append((p.pid, duration, event, sum(p.theograph.values())))
    return pd.DataFrame(rows, columns=["pid", "duration_min", "event", "density"])


def _km_curve(df: pd.DataFrame, label: str) -> KMCurve:
    km = KaplanMeierFitter().fit(df["duration_min"], df["event"])
    sf = km.survival_function_
    return KMCurve(sf.index.to_numpy(dtype=float), sf.iloc[:, 0].to_numpy(dtype=float), label)


def stratify(cctx: CohortContext) -> HazardStratification:
    """Fit the descriptive hazard model and stratify it by Theograph history density.

    Cox PH on the single ``density`` covariate (parsimonious — ≤2 covariates on ~21 events) gives the
    hazard ratio + c-index; a median split gives two KM strata and a log-rank separation p. Residuals
    are the bottom-quartile-density patients who escalated anyway — history-blind, caught by the live
    signal (pid 39), the honest limit of the prior.
    """
    df = survival_table(cctx)
    cph = CoxPHFitter().fit(df[["duration_min", "event", "density"]], "duration_min", "event")
    hr = float(np.exp(cph.params_["density"]))
    lo_ci, hi_ci = (float(np.exp(x)) for x in cph.confidence_intervals_.loc["density"])

    median = float(df["density"].median())
    hi_df, lo_df = df[df["density"] > median], df[df["density"] <= median]
    lr = logrank_test(hi_df["duration_min"], lo_df["duration_min"], hi_df["event"], lo_df["event"])

    q = float(np.quantile(df["density"], _RESIDUAL_QUANTILE))
    residuals = tuple(sorted(df[(df["density"] <= q) & (df["event"] == 1)]["pid"].astype(int)))

    return HazardStratification(
        hazard_ratio=hr,
        hr_ci=(lo_ci, hi_ci),
        c_index=float(cph.concordance_index_),
        logrank_p=float(lr.p_value),
        high=_km_curve(hi_df, "denser history"),
        low=_km_curve(lo_df, "thinner history"),
        residual_pids=residuals,
        n_events=int(df["event"].sum()),
    )
