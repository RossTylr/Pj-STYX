"""F2 — short-horizon forecast of a scalar risk series with conformal residual bands.

Deterministic (DET-1): a least-squares trend on the trailing window, projected forward, widened
by split-conformal residual quantiles calibrated on the cohort (UQ-1; empirical quantiles, no
sampling). The forecast is of the F4 risk waterline, so the cone's *upper* edge reaching the
escalation threshold is directly comparable to F4's absolute trigger — the "forecast fires" event
of gate G3, which by construction can fire *before* the risk itself crosses.

Coverage is marginal (residuals pooled across the calibration cohort), not subtype-conditional —
honest for the demo; it is not a per-patient guarantee. The cone is clipped to [0, 1] because the
target is a bounded risk (a linear projection + symmetric bands would otherwise overshoot).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np

from styx.config import CONFORMAL_ALPHA, FORECAST_HORIZON, FORECAST_SUSTAIN, FORECAST_WINDOW


@dataclass(frozen=True, eq=False)
class ForecastCone:
    """A short-horizon forecast: point path plus the conformal band edges, all clipped to [0, 1]."""

    t_fore: np.ndarray  # (H,) future sim-minutes
    point: np.ndarray  # (H,) point forecast
    lower: np.ndarray  # (H,) lower band edge
    upper: np.ndarray  # (H,) upper band edge


def _fit_trend(t: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Deterministic least-squares degree-1 fit → (slope, intercept) in sim-minute units.

    A degenerate trailing window — a single sample, at the very first clock tick (now_idx 0) — has
    no trend to fit, so project it flat (slope 0) from the lone value rather than letting polyfit's
    SVD fail on an underdetermined system. Matches forecast_fire_index, which skips now_idx < window-1.
    """
    if t.size < 2:
        return 0.0, float(y[-1]) if y.size else 0.0
    slope, intercept = np.polyfit(t, y, 1)
    return float(slope), float(intercept)


def project(
    series: np.ndarray,
    t_min: np.ndarray,
    now_idx: int,
    band: np.ndarray,
    *,
    window: int = FORECAST_WINDOW,
    horizon: int = FORECAST_HORIZON,
) -> ForecastCone:
    """Project the trailing-window trend ``horizon`` steps past ``now_idx`` with conformal bands."""
    lo = max(0, now_idx - window + 1)
    slope, intercept = _fit_trend(t_min[lo : now_idx + 1], series[lo : now_idx + 1])
    dt = float(t_min[1] - t_min[0])
    t_fore = t_min[now_idx] + np.arange(1, horizon + 1, dtype=float) * dt
    point = slope * t_fore + intercept
    half = band[:horizon]
    return ForecastCone(
        t_fore,
        np.clip(point, 0.0, 1.0),
        np.clip(point - half, 0.0, 1.0),
        np.clip(point + half, 0.0, 1.0),
    )


def conformal_band(
    series_list: Iterable[np.ndarray],
    t_min: np.ndarray,
    *,
    window: int = FORECAST_WINDOW,
    horizon: int = FORECAST_HORIZON,
    alpha: float = CONFORMAL_ALPHA,
) -> np.ndarray:
    """Per-horizon band half-widths = (1−α) quantile of |actual − predicted|, pooled over the cohort.

    Split-conformal on a fixed calibration set (the caller passes the non-index series): deterministic,
    and monotone-ish growing with the horizon, so the cone widens honestly with uncertainty.
    """
    resid: list[list[float]] = [[] for _ in range(horizon)]
    n = int(t_min.size)
    for series in series_list:
        for now_idx in range(window - 1, n - 1):
            lo = now_idx - window + 1
            slope, intercept = _fit_trend(t_min[lo : now_idx + 1], series[lo : now_idx + 1])
            for k in range(1, horizon + 1):
                j = now_idx + k
                if j >= n:
                    break
                resid[k - 1].append(abs(float(series[j]) - (slope * float(t_min[j]) + intercept)))
    q = 1.0 - alpha
    return np.array([float(np.quantile(r, q)) if r else 0.0 for r in resid])


def forecast_fire_index(
    series: np.ndarray,
    t_min: np.ndarray,
    band: np.ndarray,
    threshold: float,
    indices: Iterable[int],
    *,
    window: int = FORECAST_WINDOW,
    horizon: int = FORECAST_HORIZON,
    sustain: int = FORECAST_SUSTAIN,
) -> int | None:
    """Index at which the cone upper edge first reaches ``threshold`` for ``sustain`` consecutive re-scores.

    Indices before a full trailing window exists (``< window - 1``) are skipped — the forecast has
    no trend to fit yet. The sustain requirement rejects the early transient wobble in the risk
    trend (an isolated re-score whose wide cone happens to graze the threshold) while passing the
    real, persistent approach — so the forecast cannot fire before AEGIS on noise.
    """
    run = 0
    for now_idx in indices:
        if now_idx < window - 1:
            continue
        cone = project(series, t_min, now_idx, band, window=window, horizon=horizon)
        run = run + 1 if bool((cone.upper >= threshold).any()) else 0
        if run >= sustain:
            return int(now_idx)
    return None
