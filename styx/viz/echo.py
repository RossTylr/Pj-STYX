"""F10 ECHO figure — the focus trajectory with its nearest look-alikes drawn faint behind it.

Pure builder (LYR-1): data in, Plotly figure out — no Streamlit, no I/O. The title carries the
honesty frame: ECHO illustrates with similar synthetic cases; it does not forecast this patient.
"""

from __future__ import annotations

from collections.abc import Sequence

import plotly.graph_objects as go

from styx.cohort.echo import EchoNeighbour
from styx.cohort.ranking import CohortContext
from styx.explain import DISPLAY_NAMES
from styx.state import trajectory_path
from styx.viz import palette as pal

#: Outcome → (palette colour, line dash) — colour *and* dash, so outcome is never hue alone.
_OUTCOME_STYLE: dict[str, tuple[str, str]] = {
    "escalated": (pal.OUTCOMES["escalated"], "solid"),
    "recovered": (pal.OUTCOMES["recovered"], "dash"),
}


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
        color, dash = _OUTCOME_STYLE.get(n.outcome, (pal.NEUTRAL, "dot"))
        fig.add_trace(go.Scatter(
            x=path[:, 0], y=path[:, 1], mode="lines", opacity=0.35,
            line=dict(color=color, width=1.5, dash=dash),
            name=f"patient {n.pid} · {n.outcome}",
        ))
    focus = trajectory_path(cctx.cohort.patients[focus_pid], cctx.emb)[: now_idx + 1]
    fig.add_trace(go.Scatter(
        x=focus[:, 0], y=focus[:, 1], mode="lines", line=dict(color=pal.BLACK, width=3),
        name=f"patient {focus_pid} (focus)",
    ))
    fig.add_trace(go.Scatter(
        x=[float(focus[-1, 0])], y=[float(focus[-1, 1])], mode="markers", name="now",
        marker=dict(size=16, color=pal.NOW, line=dict(color="white", width=2)),
    ))
    fig.update_layout(
        title=f"{DISPLAY_NAMES['echo']} — illustration, not a forecast of this patient",
        xaxis_title=cctx.emb.axis_labels[0], yaxis_title=cctx.emb.axis_labels[1],
        height=480, showlegend=True,
    )
    return fig
