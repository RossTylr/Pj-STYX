"""NEWS2 A/B comparison — the same stay scored two ways on one clock. Pure builder (LYR-1).

Two stacked lanes on a shared time axis, each score against *its own* escalation line: the STYX
risk (0–1) above, the partial NEWS2 (Scale 1) below on its honest full 0–12 range. Separate lanes,
not a dual y-axis — two incommensurable scales on one plot is the chart genre that invites rigged
axes; here the lead is read off the shared clock, never off amplitude. No new maths: both series
arrive already computed (risk from the context, partial NEWS2 from ``styx.readouts`` — the fair,
single-sourced comparator, never re-scored here), so the digest is untouched. Retrospective replay
driven by ``now_idx``; the lead bracket (early-warning-vs-NEWS2 only) appears only once "now" has
passed both fire-times — never a phenomenon "now" hasn't reached.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from styx.explain import COMPARISON_LABELS
from styx.viz import palette as pal

#: NEWS2 lane y-range — the full Scale-1 aggregate range, never zoomed to flatter the flat line.
_NEWS2_RANGE: tuple[float, float] = (0.0, 12.0)


def comparison_figure(
    t_min: np.ndarray,
    risk: np.ndarray,
    threshold: float,
    news2: np.ndarray,
    news2_trigger: int,
    *,
    aegis_min: float | None,
    escalation_min: float | None,
    news2_crossing_min: float | None,
    now_idx: int | None = None,
) -> go.Figure:
    """Render the A/B: STYX risk vs the partial NEWS2 comparator, clipped at the replay clock.

    ``news2`` / ``news2_crossing_min`` are ``styx.readouts.news2_partial`` / ``news2_crossing``
    output passed through unchanged; ``escalation_min`` is the fire-times threshold crossing.
    ``now_idx=None`` parks "now" at the end of the stay — the full static view.
    """
    now_i = int(now_idx) if now_idx is not None else len(t_min) - 1
    now_min = float(t_min[now_i])

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.07)
    fig.add_trace(go.Scatter(
        x=t_min[: now_i + 1], y=risk[: now_i + 1], mode="lines",
        name=COMPARISON_LABELS["styx_lane"], line=dict(color=pal.RISK, width=2),
    ), row=1, col=1)
    fig.add_hline(y=threshold, line=dict(color=pal.THRESHOLD, width=1, dash="dot"),
                  annotation_text=COMPARISON_LABELS["threshold"], row=1, col=1)
    fig.add_trace(go.Scatter(
        x=t_min[: now_i + 1], y=news2[: now_i + 1], mode="lines", line_shape="hv",
        name=COMPARISON_LABELS["news2_lane"], line=dict(color=pal.COMPARATOR, width=2),
    ), row=2, col=1)
    fig.add_hline(y=news2_trigger, line=dict(color=pal.THRESHOLD, width=1, dash="dot"),
                  annotation_text=COMPARISON_LABELS["trigger"], row=2, col=1)

    # crossing markers sit on the real series at each fire-time, revealed only once "now" passes
    # (the hero's convention: STYX crossing an × on the risk, NEWS2 a hollow vermilion diamond).
    if escalation_min is not None and escalation_min <= now_min:
        i = int(np.searchsorted(t_min, escalation_min))
        fig.add_trace(go.Scatter(
            x=[escalation_min], y=[float(risk[i])], mode="markers",
            name=COMPARISON_LABELS["escalation"],
            marker=dict(size=13, symbol="x", color=pal.RISK, line=dict(color="white", width=1.2)),
        ), row=1, col=1)
    if news2_crossing_min is not None and news2_crossing_min <= now_min:
        i = int(np.searchsorted(t_min, news2_crossing_min))
        fig.add_trace(go.Scatter(
            x=[news2_crossing_min], y=[float(news2[i])], mode="markers",
            name=COMPARISON_LABELS["news2_fires"],
            marker=dict(size=13, symbol="diamond", color="rgba(0,0,0,0)",
                        line=dict(color=pal.THRESHOLD, width=2.4)),
        ), row=2, col=1)
    if aegis_min is not None and aegis_min <= now_min:
        fig.add_vline(x=aegis_min, line=dict(color=pal.EARLY_WARNING, width=1.6, dash="dash"))
        fig.add_annotation(x=aegis_min, y=0.97, text=COMPARISON_LABELS["early_warning"],
                           showarrow=False, xanchor="left", xshift=4,
                           font=dict(size=10.5, color=pal.EARLY_WARNING), row=1, col=1)

    # the headline lead bracket — early-warning-vs-NEWS2 only, display arithmetic on the fire-times
    if (aegis_min is not None and news2_crossing_min is not None
            and aegis_min <= now_min and news2_crossing_min <= now_min):
        lead = news2_crossing_min - aegis_min
        fig.add_shape(type="line", x0=aegis_min, x1=news2_crossing_min, y0=10.4, y1=10.4,
                      line=dict(color=pal.RISK, width=1.6), row=2, col=1)
        fig.add_annotation(x=(aegis_min + news2_crossing_min) / 2, y=11.4, showarrow=False,
                           text=COMPARISON_LABELS["lead"].format(hours=lead / 60, minutes=lead),
                           font=dict(size=10.5, color=pal.RISK), row=2, col=1)

    fig.update_yaxes(title_text=COMPARISON_LABELS["yaxis_risk"], range=[0, 1], row=1, col=1)
    fig.update_yaxes(title_text=COMPARISON_LABELS["yaxis_news2"], range=list(_NEWS2_RANGE),
                     row=2, col=1)
    fig.update_xaxes(title_text=COMPARISON_LABELS["xaxis"], row=2, col=1)
    fig.update_layout(
        title=COMPARISON_LABELS["title"], height=460, showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.14, xanchor="left", x=0),
    )
    return fig
