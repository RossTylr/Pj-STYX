"""F2 forecast-cone figure — observed risk + the projected cone. Pure builder: data in, figure out.

No Streamlit, no I/O (LYR-1). The app and notebooks call this and own their own rendering.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from styx.forecast import ForecastCone


def cone_figure(
    t_min: np.ndarray,
    series: np.ndarray,
    cone: ForecastCone,
    threshold: float,
    *,
    now_idx: int,
) -> go.Figure:
    """Render the observed risk up to ``now`` and the forecast cone (band + point) beyond it."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=t_min[: now_idx + 1], y=series[: now_idx + 1], mode="lines", name="risk (observed)",
        line=dict(color="#36c", width=2),
    ))
    # Conformal band as a filled envelope (upper out, lower back) — widens with the horizon.
    band_x = np.concatenate([cone.t_fore, cone.t_fore[::-1]])
    band_y = np.concatenate([cone.upper, cone.lower[::-1]])
    fig.add_trace(go.Scatter(
        x=band_x, y=band_y, fill="toself", fillcolor="rgba(51,102,204,0.18)",
        line=dict(width=0), name="conformal cone", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=cone.t_fore, y=cone.point, mode="lines", name="forecast",
        line=dict(color="#36c", width=1, dash="dash"),
    ))
    fig.add_hline(y=threshold, line=dict(color="#c33", width=1, dash="dot"),
                  annotation_text="escalation threshold")
    fig.update_layout(
        title="Forecast cone — risk projected past now",
        xaxis_title="sim-minutes", yaxis_title="risk", yaxis_range=[0, 1],
        height=420, showlegend=True,
    )
    return fig
