"""Episode-timeline figure — the fire-points on one horizontal strip (data in → Plotly figure out).

Pure builder (LYR-1): no Streamlit, no I/O. The projected-escalation ETA is drawn as a translucent
**band** (a range), never a point marker, so it can't read as false precision; its width is the
cone's (soonest → central) window. The title carries the honesty frame.
"""

from __future__ import annotations

import plotly.graph_objects as go

from styx.timeline import EpisodeTimeline
from styx.viz import palette as pal

#: One palette colour per fire-point; the ETA band is kept faint orange to read as "uncertain window".
_COLOR: dict[str, str] = {
    "aegis": pal.EARLY_WARNING, "forecast": pal.RISK, "breach": pal.THRESHOLD,
}
_SYMBOL: dict[str, str] = {"aegis": "circle", "forecast": "diamond", "breach": "x"}
#: Marker text — UK clinical wording (6j): the absolute breach reads as "threshold crossed".
_DISPLAY: dict[str, str] = {"aegis": "AEGIS", "forecast": "Forecast", "breach": "Threshold"}


def timeline_figure(timeline: EpisodeTimeline) -> go.Figure:
    """Lay AEGIS / forecast / breach as markers and the projected escalation as a faint band."""
    fig = go.Figure()

    eta = next(e for e in timeline.events if e.key == "eta")
    if eta.eta_soonest_min is not None:  # projected escalation — a range (UQ-1), never a point
        x_soon = eta.t_min + eta.eta_soonest_min
        if eta.eta_confident and eta.eta_central_min is not None:  # bounded window [soonest, central]
            x_cen = eta.t_min + eta.eta_central_min
            fig.add_vrect(
                x0=min(x_soon, x_cen), x1=max(x_soon, x_cen), fillcolor=pal.EARLY_WARNING,
                opacity=0.18, line_width=0, annotation_text="projected escalation (window)",
                annotation_position="top left",
            )
        else:  # only the cone's upper edge crosses — escalation no sooner than x_soon, open-ended
            fig.add_trace(go.Scatter(
                x=[x_soon], y=[0.4], mode="markers+text", name="ETA (≥ soonest, open-ended)",
                marker=dict(size=14, color=pal.EARLY_WARNING, symbol="triangle-right",
                            line=dict(color="white", width=1.5)),
                text=["≥ projected"], textposition="top right",
                hovertext=[f"{eta.label_lay} — no sooner than {eta.eta_soonest_min:.0f} min"],
                hoverinfo="text",
            ))

    for e in timeline.events:
        if e.key == "eta" or e.idx is None:
            continue
        fig.add_trace(go.Scatter(
            x=[e.t_min], y=[0], mode="markers+text", name=e.label_tech,
            marker=dict(size=16, color=_COLOR[e.key], symbol=_SYMBOL[e.key],
                        line=dict(color="white", width=1.5)),
            text=[_DISPLAY[e.key]], textposition="bottom center",
            hovertext=[e.label_lay], hoverinfo="text",
        ))

    # The named-standard comparator: where a partial NEWS2 would first escalate (here, last of all).
    if timeline.news2_crossing_min is not None:
        fig.add_trace(go.Scatter(
            x=[timeline.news2_crossing_min], y=[-0.5], mode="markers+text",
            name="NEWS2 (partial) — escalation trigger",
            marker=dict(size=15, color=pal.COMPARATOR, symbol="star",
                        line=dict(color="white", width=1.5)),
            text=["NEWS2"], textposition="bottom center",
            hovertext=["partial NEWS2 (Scale 1) first reaches its escalation trigger"],
            hoverinfo="text",
        ))

    fig.update_layout(
        title="Episode timeline — assembled fire-points (synthetic replay; ETA shown as a band)",
        xaxis_title="sim-minutes", height=220, showlegend=True,
        yaxis=dict(visible=False, range=[-1, 1]),
    )
    return fig
