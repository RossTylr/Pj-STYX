"""(6h) Landing obs-timeline motif — the front-page value proposition, shown in one strip.

Pure builder (LYR-1): no Streamlit, no I/O, no clinical maths. This is *brand chrome*, not a clinical
figure — a schematic of the concept, built from a fixed hand-authored shape (no RNG, deterministic).
Intermittent nurse obs read as discrete dots; the always-on STYX trajectory is the continuous line
through and between them; one alert flag sits in a gap before the next obs, where STYX catches drift
the next scheduled obs would have missed. Brand tokens only (BRAND_* from the palette); it never
touches the warm clinical ramp or the Okabe–Ito ownership markers.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from styx.viz import palette as pal

# Schematic clock (hours). Obs are intermittent; STYX is continuous; drift is caught in the last gap.
_OBS_HOURS: tuple[float, ...] = (6.0, 12.0, 18.0)
_FLAG_HOUR = 16.0  # in the 12:00 → 18:00 gap, before the next obs would catch the drift


def _trajectory(t: np.ndarray) -> np.ndarray:
    """A flat-then-drifting schematic line — steady through the day, departing late. No randomness."""
    return 0.30 + 0.46 * np.clip((t - 9.0) / 11.0, 0.0, 1.0) ** 1.7


def obs_timeline_figure() -> go.Figure:
    """The continuous STYX line, intermittent obs dots, and one alert flag caught between obs."""
    t = np.linspace(0.0, 21.0, 211)
    y = _trajectory(t)
    obs_x = np.array(_OBS_HOURS)
    obs_y = _trajectory(obs_x)
    flag_y = float(_trajectory(np.array([_FLAG_HOUR]))[0])

    fig = go.Figure()
    # the always-on STYX trajectory — the line that runs between the obs.
    fig.add_trace(go.Scatter(
        x=t, y=y, mode="lines", name="STYX",
        line=dict(color=pal.BRAND_TEAL, width=3), showlegend=False, hoverinfo="skip",
    ))
    # intermittent nurse obs / NEWS2 scores — discrete, neutral dots sitting on the same picture.
    fig.add_trace(go.Scatter(
        x=obs_x, y=obs_y, mode="markers", name="obs",
        marker=dict(color=pal.BRAND_GREY, size=12, line=dict(color="#FFFFFF", width=2)),
        showlegend=False, hoverinfo="skip",
    ))
    # the alert flag — STYX catches drift in the gap, before the next obs would.
    fig.add_trace(go.Scatter(
        x=[_FLAG_HOUR], y=[flag_y], mode="markers", name="caught here",
        marker=dict(color=pal.BRAND_ALERT, size=15, symbol="triangle-up",
                    line=dict(color="#FFFFFF", width=1)),
        showlegend=False, hoverinfo="skip",
    ))

    fig.add_annotation(x=obs_x[0], y=obs_y[0], text="obs", showarrow=False,
                       yshift=18, font=dict(color=pal.BRAND_GREY, size=12))
    fig.add_annotation(x=_FLAG_HOUR, y=flag_y, text="caught between obs", showarrow=False,
                       yshift=22, font=dict(color=pal.BRAND_ALERT, size=12))

    fig.update_layout(
        height=150, margin=dict(t=24, b=12, l=8, r=8), showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False, range=[-0.5, 21.5]),
        yaxis=dict(visible=False, range=[0.1, 0.95]),
    )
    return fig
