"""F3 Theograph figures — dual-scale care history. Pure builders: data in, Plotly figure out.

Two scales over the same derived event timeline: a compressed *lifelong* ribbon (years) and a
*recent-days* detail strip aligned to the live episode. No Streamlit, no I/O (LYR-1).
"""

from __future__ import annotations

import plotly.graph_objects as go

from styx.config import CHANNELS
from styx.theograph.events import RECENT_DAYS, CareEvent
from styx.viz import palette as pal

#: Per-channel colours from the shared palette (fixed order → deterministic legend, never dict order).
_CHANNEL_COLORS: dict[str, str] = pal.CHANNELS
_LANE = {c: i for i, c in enumerate(CHANNELS)}  # row per channel, fixed order


def _lane_axis(fig: go.Figure) -> None:
    """Label the y-axis with one tick per channel lane (shared by both scales)."""
    fig.update_yaxes(
        tickmode="array", tickvals=list(_LANE.values()), ticktext=list(_LANE.keys()),
        range=[-0.5, len(CHANNELS) - 0.5],
    )


def _glyphs(fig: go.Figure, events: tuple[CareEvent, ...], xs: list[float]) -> None:
    """Drop one marker per event on its channel lane at the supplied x positions."""
    for channel in CHANNELS:
        idx = [i for i, e in enumerate(events) if e.channel == channel]
        if not idx:
            continue
        fig.add_trace(go.Scatter(
            x=[xs[i] for i in idx], y=[_LANE[channel]] * len(idx), mode="markers",
            name=channel, marker=dict(size=9, color=_CHANNEL_COLORS[channel],
                                      line=dict(color="white", width=1)),
        ))


def ribbon_figure(events: tuple[CareEvent, ...], *, now_days: float = 0.0) -> go.Figure:
    """Compressed lifelong overview — one lane per channel, glyphs along a multi-year x-axis."""
    fig = go.Figure()
    _glyphs(fig, events, [e.t_days / 365.25 for e in events])
    fig.add_vline(x=now_days / 365.25, line=dict(color=pal.ANNOTATION, width=1, dash="dot"),
                  annotation_text="now")
    _lane_axis(fig)
    fig.update_layout(
        title="Theograph — lifelong care history", xaxis_title="years before now",
        height=240, showlegend=False, margin=dict(l=140, t=40, b=40),
    )
    return fig


def detail_strip_figure(
    events: tuple[CareEvent, ...], *, window_days: float = RECENT_DAYS
) -> go.Figure:
    """Recent-days swimlane aligned to the live episode — the run-up to (and into) the stay."""
    recent = tuple(e for e in events if e.t_days >= -window_days)
    fig = go.Figure()
    _glyphs(fig, recent, [e.t_days for e in recent])
    fig.add_vline(x=0.0, line=dict(color=pal.ANNOTATION, width=1, dash="dot"), annotation_text="now")
    _lane_axis(fig)
    fig.update_layout(
        title=f"Theograph — last {int(window_days)} days", xaxis_title="days before now",
        xaxis_range=[-window_days, 0.5], height=240, showlegend=False,
        margin=dict(l=140, t=40, b=40),
    )
    return fig
