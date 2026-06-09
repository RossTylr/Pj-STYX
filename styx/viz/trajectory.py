"""F1 trajectory figure — the legible hero view. Pure builder: data in, Plotly figure out.

No Streamlit, no I/O (LYR-1). The app and notebooks call this and own their own rendering.
"""

from __future__ import annotations

import plotly.graph_objects as go

from styx.state.embedding import Basins, Embedding, now_position, trajectory_path
from styx.synth.cohort import Patient
from styx.theograph.events import CareEvent


def _basin_shape(center, radius, color: str) -> dict:
    """An ellipse (1.5σ per axis) marking a learned region of the state space."""
    rx, ry = 1.5 * float(radius[0]), 1.5 * float(radius[1])
    return dict(
        type="circle", xref="x", yref="y", line_width=0, fillcolor=color, opacity=0.18,
        x0=float(center[0]) - rx, x1=float(center[0]) + rx,
        y0=float(center[1]) - ry, y1=float(center[1]) + ry,
    )


def trajectory_figure(
    patient: Patient,
    emb: Embedding,
    basins: Basins,
    *,
    events: list[tuple[int, CareEvent]] | None = None,
) -> go.Figure:
    """Render a stay as a path between the stability basin and the crisis attractor.

    ``events`` (optional, default None → existing callers unaffected) threads in-episode care
    events onto the path at the sample index where each occurred (F3 Layer-1 overlay).
    """
    path = trajectory_path(patient, emb)
    now = now_position(patient, emb)
    fig = go.Figure()
    fig.add_shape(_basin_shape(basins.basin_center, basins.basin_radius, "#2a8"))
    for center, radius in zip(basins.attractor_centers, basins.attractor_radii):
        fig.add_shape(_basin_shape(center, radius, "#c33"))  # one crisis mode per archetype
    fig.add_trace(go.Scatter(
        x=path[:, 0], y=path[:, 1], mode="lines+markers", name="trajectory",
        line=dict(color="#888", width=1),
        marker=dict(size=4, color=patient.t_min, colorscale="Viridis", showscale=False),
    ))
    if events:
        fig.add_trace(go.Scatter(
            x=[float(path[i, 0]) for i, _ in events], y=[float(path[i, 1]) for i, _ in events],
            mode="markers", name="care event", text=[e.channel for _, e in events],
            hovertemplate="%{text}<extra></extra>",
            marker=dict(size=12, symbol="diamond", color="#e80", line=dict(color="white", width=1)),
        ))
    fig.add_trace(go.Scatter(
        x=[now[0]], y=[now[1]], mode="markers", name="now",
        marker=dict(size=18, color="#36c", line=dict(color="white", width=2)),
    ))
    fig.update_layout(
        title=f"State-space trajectory — patient {patient.pid} ({emb.mode} axes)",
        xaxis_title=emb.axis_labels[0], yaxis_title=emb.axis_labels[1],
        height=480, showlegend=True,
    )
    return fig
