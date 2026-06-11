"""R3a.2 CADUCEUS — the breathing–oxygen coherence trace (data in → Plotly figure out).

Pure builder (LYR-1): no Streamlit, no I/O, no maths. It renders the RR–SpO₂ windowed coherence the
G1 gate already computed (single source — passed in, never recomputed here) with the decoupling
onset marked as the *mechanism's* onset — where the breathing–oxygen coupling breaks down — and a
light early-warning context marker. Mechanistic/descriptive only: it draws no F4 / NEWS2 lane and no
cascade or lead caption, so it carries no predictive or accuracy claim, and the onset reads as where
the mechanism begins, not STYX's earliest alert. Labels come from ``styx.explain.COHERENCE_LABELS``
(register-linted); colours from the Okabe–Ito palette.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from styx.explain import COHERENCE_LABELS
from styx.viz import palette as pal


def coherence_figure(
    t_min: np.ndarray,
    coherence: np.ndarray,
    onset_min: float,
    *,
    aegis_min: float | None = None,
) -> go.Figure:
    """RR–SpO₂ windowed coherence over time, with the decoupling-onset mechanism marker."""
    fig = go.Figure()
    # the coherence trace — leading-NaN warm-up reads as a gap, never an interpolated line.
    fig.add_trace(go.Scatter(
        x=t_min, y=coherence, mode="lines", name=COHERENCE_LABELS["trace"],
        line=dict(color=pal.RISK, width=2), connectgaps=False, showlegend=False,
        hovertemplate="%{y:.2f}<extra></extra>",
    ))

    # the mechanism onset — where the coupling breaks down (descriptive; not an alert).
    fig.add_vline(x=onset_min, line=dict(color=pal.ANNOTATION, width=2),
                  annotation_text=COHERENCE_LABELS["onset"], annotation_position="top left")

    # light early-warning context marker — the calibrated alert, shown only for the relationship.
    if aegis_min is not None:
        fig.add_vline(x=aegis_min, line=dict(color=pal.EARLY_WARNING, width=1, dash="dot"),
                      annotation_text=COHERENCE_LABELS["aegis"], annotation_position="top right")

    fig.update_layout(
        title=COHERENCE_LABELS["title"],
        xaxis_title=COHERENCE_LABELS["xaxis"], yaxis_title=COHERENCE_LABELS["yaxis"],
        height=260, showlegend=False, margin=dict(t=60, b=20),
    )
    return fig
