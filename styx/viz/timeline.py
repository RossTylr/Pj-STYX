"""Episode-timeline figure — a layered gantt of the fire-points (data in → Plotly figure out).

Pure builder (LYR-1): no Streamlit, no I/O. One horizontal lane per signal, each drawn as a bar
that opens at its fire-time and runs to the end of the stay — so the *staggered left edges* read
as the lead: early warning opens first, the absolute threshold later, the partial-NEWS2 comparator
last of all. The projected escalation is a **bounded band** (a range), never a point, so it can't
read as false precision. No marker symbols, no emoji — just labelled lanes and bars.
"""

from __future__ import annotations

import plotly.graph_objects as go

from styx.explain import DISPLAY_NAMES
from styx.readouts import sim_clock
from styx.timeline import EpisodeTimeline
from styx.viz import palette as pal

#: Lane label + bar colour per signal. Order here is the fire order (drawn top → bottom).
_LANES: tuple[tuple[str, str, str], ...] = (
    ("aegis", DISPLAY_NAMES["aegis"], pal.EARLY_WARNING),
    ("forecast", "Forecast confirms", pal.RISK),
    ("eta", "Projected escalation", pal.EARLY_WARNING),
    ("breach", "Threshold crossed", pal.THRESHOLD),
    ("news2", "NEWS2 (partial, Scale 1)", pal.COMPARATOR),
)
_LABEL = {key: label for key, label, _ in _LANES}
_COLOR = {key: color for key, _, color in _LANES}


def _bar(fig: go.Figure, label: str, start: float, end: float, color: str, *,
         opacity: float = 0.85, hover: str = "", note: str = "") -> None:
    """One gantt lane: a horizontal bar from ``start`` to ``end`` on the ``label`` row."""
    fig.add_trace(go.Bar(
        y=[label], x=[max(end - start, 0.0)], base=[start], orientation="h", width=0.55,
        marker=dict(color=color, opacity=opacity, line=dict(color="white", width=1)),
        text=[note], textposition="outside", cliponaxis=False,
        hovertext=[hover], hoverinfo="text", showlegend=False,
    ))


def timeline_figure(timeline: EpisodeTimeline) -> go.Figure:
    """Lay each fired signal as a bar opening at its fire-time; the ETA as a bounded band."""
    fig = go.Figure()
    fired = {e.key: e for e in timeline.events if e.idx is not None}
    ends = [e.t_min for e in fired.values() if e.t_min is not None]
    if timeline.news2_crossing_min is not None:
        ends.append(timeline.news2_crossing_min)
    end = timeline.end_min if timeline.end_min is not None else (max(ends) if ends else 0.0)

    # AEGIS / forecast / threshold: each opens at its fire-time and runs to the end of the stay.
    for key in ("aegis", "forecast", "breach"):
        e = fired.get(key)
        if e is None or e.t_min is None:
            continue
        _bar(fig, _LABEL[key], e.t_min, end, _COLOR[key],
             hover=e.label_lay, note=sim_clock(e.t_min))

    # Projected escalation: a *bounded* band (soonest → central), or open-ended (≥ soonest).
    eta = next((e for e in timeline.events if e.key == "eta"), None)
    if eta is not None and eta.t_min is not None and eta.eta_soonest_min is not None:
        soon = eta.t_min + eta.eta_soonest_min
        if eta.eta_confident and eta.eta_central_min is not None:
            stop, note = eta.t_min + eta.eta_central_min, "projected window"
        else:  # only the cone's upper edge crosses — escalation no sooner than `soon`, open-ended
            stop, note = end, "≥ projected (open-ended)"
        _bar(fig, _LABEL["eta"], soon, stop, pal.EARLY_WARNING, opacity=0.3,
             hover=f"{eta.label_lay} — {note}", note=note)

    # The named-standard comparator: opens last, after AEGIS and the breach.
    if timeline.news2_crossing_min is not None:
        _bar(fig, _LABEL["news2"], timeline.news2_crossing_min, end, pal.COMPARATOR,
             hover="partial NEWS2 (Scale 1) first reaches its escalation trigger",
             note=sim_clock(timeline.news2_crossing_min))

    # Lanes top → bottom in fire order (Plotly puts the first category at the bottom → reverse).
    fig.update_layout(
        title="Episode timeline — when each signal fires (synthetic replay; ETA shown as a band)",
        xaxis_title="sim-minutes", height=260, bargap=0.35, showlegend=False,
        yaxis=dict(categoryorder="array", categoryarray=[label for _, label, _ in reversed(_LANES)]),
    )
    return fig
