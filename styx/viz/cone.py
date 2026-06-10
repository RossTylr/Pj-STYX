"""F2 forecast-cone figure — observed risk + the projected cone. Pure builder: data in, figure out.

No Streamlit, no I/O (LYR-1). The app and notebooks call this and own their own rendering.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from styx.forecast import ForecastCone
from styx.viz import palette as pal


def cone_figure(
    t_min: np.ndarray,
    series: np.ndarray,
    cone: ForecastCone,
    threshold: float,
    *,
    now_idx: int,
    ghost: ForecastCone | None = None,
) -> go.Figure:
    """Render the observed risk up to ``now`` and the forecast cone (band + point) beyond it.

    ``ghost`` (optional, default None → existing callers unaffected) overlays an earlier, *stale*
    projection — the cone anchored at the AEGIS fire-time — as a faint dashed path on the realised
    risk (F9: "what STYX saw coming when it first flagged").
    """
    fig = go.Figure()
    if ghost is not None:
        fig.add_trace(go.Scatter(
            x=ghost.t_fore, y=ghost.point, mode="lines", name="Hindsight forecast (at early warning)",
            line=dict(color=pal.EARLY_WARNING, width=2, dash="dot"), opacity=0.7,
        ))
    fig.add_trace(go.Scatter(
        x=t_min[: now_idx + 1], y=series[: now_idx + 1], mode="lines", name="risk (observed)",
        line=dict(color=pal.RISK, width=2),
    ))
    # Conformal band as a filled envelope (upper out, lower back) — widens with the horizon.
    band_x = np.concatenate([cone.t_fore, cone.t_fore[::-1]])
    band_y = np.concatenate([cone.upper, cone.lower[::-1]])
    fig.add_trace(go.Scatter(
        x=band_x, y=band_y, fill="toself", fillcolor=pal.CONE_FILL,
        line=dict(width=0), name="conformal cone", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=cone.t_fore, y=cone.point, mode="lines", name="forecast",
        line=dict(color=pal.RISK, width=1, dash="dash"),
    ))
    fig.add_hline(y=threshold, line=dict(color=pal.THRESHOLD, width=1, dash="dot"),
                  annotation_text="escalation threshold")
    fig.update_layout(
        title="Forecast cone — risk projected past now",
        xaxis_title="sim-minutes", yaxis_title="risk", yaxis_range=[0, 1],
        height=420, showlegend=True,
    )
    return fig
