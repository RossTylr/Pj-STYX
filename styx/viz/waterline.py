"""F4 risk-waterline figure — rising risk, absolute threshold, AEGIS flag. Pure builder.

No Streamlit, no I/O (LYR-1). The app and notebooks call this and own their own rendering.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from styx.viz import palette as pal


def waterline_figure(
    t_min: np.ndarray,
    risk: np.ndarray,
    threshold: float,
    *,
    aegis_idx: int | None = None,
) -> go.Figure:
    """Render the risk waterline with the escalation threshold and the AEGIS fire marker."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=t_min, y=risk, mode="lines", name="risk", line=dict(color=pal.RISK, width=2),
        fill="tozeroy", fillcolor=pal.RISK_FILL,
    ))
    fig.add_hline(y=threshold, line=dict(color=pal.THRESHOLD, width=1, dash="dot"),
                  annotation_text="escalation threshold")
    if aegis_idx is not None:
        fig.add_vline(x=float(t_min[aegis_idx]), line=dict(color=pal.EARLY_WARNING, width=2, dash="dash"),
                      annotation_text="Early warning (AEGIS)")
    fig.update_layout(
        title="Risk waterline — rises early, crosses late",
        xaxis_title="sim-minutes", yaxis_title="risk", yaxis_range=[0, 1],
        height=420, showlegend=True,
    )
    return fig
