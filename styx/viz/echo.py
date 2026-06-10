"""F10 ECHO figure — the focus trajectory with its nearest look-alikes drawn faint behind it.

Pure builder (LYR-1): data in, Plotly figure out — no Streamlit, no I/O. The title carries the
honesty frame: ECHO illustrates with similar synthetic cases; it does not forecast this patient.
"""

from __future__ import annotations

from collections.abc import Sequence

import plotly.graph_objects as go

from styx.cohort.echo import EchoNeighbour
from styx.cohort.ranking import CohortContext
from styx.state import trajectory_path

#: Neighbour outcomes get an honest colour — escalated leans warm, recovered cool — kept faint.
_OUTCOME_COLOR: dict[str, str] = {"escalated": "#c33", "recovered": "#2a8"}


def echo_figure(
    cctx: CohortContext,
    focus_pid: int,
    neighbours: Sequence[EchoNeighbour],
    now_idx: int,
) -> go.Figure:
    """Draw each neighbour's course-so-far faint, the focus patient's bold on top, now-marker last."""
    fig = go.Figure()
    for n in neighbours:
        path = trajectory_path(cctx.cohort.patients[n.pid], cctx.emb)[: now_idx + 1]
        fig.add_trace(go.Scatter(
            x=path[:, 0], y=path[:, 1], mode="lines", opacity=0.35,
            line=dict(color=_OUTCOME_COLOR.get(n.outcome, "#888"), width=1.5),
            name=f"patient {n.pid} · {n.outcome}",
        ))
    focus = trajectory_path(cctx.cohort.patients[focus_pid], cctx.emb)[: now_idx + 1]
    fig.add_trace(go.Scatter(
        x=focus[:, 0], y=focus[:, 1], mode="lines", line=dict(color="#222", width=3),
        name=f"patient {focus_pid} (focus)",
    ))
    fig.add_trace(go.Scatter(
        x=[float(focus[-1, 0])], y=[float(focus[-1, 1])], mode="markers", name="now",
        marker=dict(size=16, color="#36c", line=dict(color="white", width=2)),
    ))
    fig.update_layout(
        title="ECHO — similar synthetic trajectories (illustration, not a forecast of this patient)",
        xaxis_title=cctx.emb.axis_labels[0], yaxis_title=cctx.emb.axis_labels[1],
        height=480, showlegend=True,
    )
    return fig
