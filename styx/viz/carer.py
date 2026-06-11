"""R4b HERMES carer timeline — a calm "care so far" strip (data in → Plotly figure out).

Pure builder (LYR-1): no Streamlit, no I/O. A patient-safe, *descriptive* lay view of the episode — it
reads the same ``EpisodeTimeline`` the clinician strip does (single source, no recompute, DET-1) but
renders only what has already happened: the span of monitoring up to now, a "now" marker, and the
early-warning moment if it has already been reached. It draws NO projection (no ETA band), no breach /
threshold lane and no NEWS2 comparator — so it can carry no predictive or alarming claim. Labels come
from ``styx.explain.CARER_TIMELINE_NAMES`` (register-linted); colours from the Okabe–Ito palette.
"""

from __future__ import annotations

import plotly.graph_objects as go

from styx.explain import CARER_TIMELINE_NAMES
from styx.timeline import EpisodeTimeline
from styx.viz import palette as pal


def carer_timeline_figure(timeline: EpisodeTimeline) -> go.Figure:
    """A calm "care so far" strip: the monitored span up to now + any early-warning already reached."""
    lane = CARER_TIMELINE_NAMES["monitored"]
    # "now" is the silent-window frame the strip is drawn at — read its sim-minute off the eta event
    # (idx == default_idx); the ETA band itself is never drawn.
    eta = next((e for e in timeline.events if e.key == "eta"), None)
    t_now = eta.t_min if eta is not None and eta.t_min is not None else (timeline.end_min or 0.0)

    fig = go.Figure()
    # the stay so far, as one calm lane from the start of the stay to now
    fig.add_trace(go.Bar(
        y=[lane], x=[max(t_now, 0.0)], base=[0.0], orientation="h", width=0.5,
        marker=dict(color=pal.STABLE, opacity=0.55, line=dict(color="white", width=1)),
        hovertext=[lane], hoverinfo="text", showlegend=False,
    ))

    # the early-warning moment — shown only if it has already happened by now (never a future event).
    aegis = next((e for e in timeline.events if e.key == "aegis"), None)
    if (aegis is not None and aegis.idx is not None and aegis.t_min is not None
            and aegis.idx <= timeline.default_idx):
        fig.add_trace(go.Scatter(
            x=[aegis.t_min], y=[lane], mode="markers", hoverinfo="text",
            hovertext=[CARER_TIMELINE_NAMES["aegis"]], showlegend=False,
            marker=dict(color=pal.EARLY_WARNING, size=13, line=dict(color="white", width=1)),
        ))
        fig.add_annotation(x=aegis.t_min, y=lane, text=CARER_TIMELINE_NAMES["aegis"],
                           showarrow=True, arrowhead=0, ay=-42, yanchor="bottom")

    # "now" — the right edge of the monitored span (no sim-minute number; lay register).
    fig.add_vline(x=max(t_now, 0.0), line=dict(color=pal.ANNOTATION, width=1, dash="dot"),
                  annotation_text=CARER_TIMELINE_NAMES["now"])

    fig.update_layout(
        title="Care so far — synthetic replay",
        height=200, bargap=0.5, showlegend=False,
        xaxis=dict(visible=False),  # lay register: no sim-minute axis chrome
        margin=dict(t=60, b=20),
    )
    return fig
