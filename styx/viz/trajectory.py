"""F1 trajectory figure — the legible hero view. Pure builder: data in, Plotly figure out.

No Streamlit, no I/O (LYR-1). The app and notebooks call this and own their own rendering.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import plotly.graph_objects as go

from styx.explain import DISPLAY_NAMES
from styx.readouts import _rr_score, _spo2_scale1_score
from styx.state.embedding import Basins, Embedding, now_position, trajectory_path
from styx.synth.cohort import Patient
from styx.theograph.events import CareEvent
from styx.viz import palette as pal


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
    fig.add_shape(_basin_shape(basins.basin_center, basins.basin_radius, pal.STABLE))
    for center, radius in zip(basins.attractor_centers, basins.attractor_radii):
        fig.add_shape(_basin_shape(center, radius, pal.THRESHOLD))  # one crisis mode per archetype
    fig.add_trace(go.Scatter(
        x=path[:, 0], y=path[:, 1], mode="lines+markers", name="trajectory",
        line=dict(color=pal.NEUTRAL, width=1),
        marker=dict(size=4, color=patient.t_min, colorscale="Viridis", showscale=False),
    ))
    if events:
        fig.add_trace(go.Scatter(
            x=[float(path[i, 0]) for i, _ in events], y=[float(path[i, 1]) for i, _ in events],
            mode="markers", name="care event", text=[e.channel for _, e in events],
            hovertemplate="%{text}<extra></extra>",
            marker=dict(size=12, symbol="diamond", color=pal.EARLY_WARNING,
                        line=dict(color="white", width=1)),
        ))
    fig.add_trace(go.Scatter(
        x=[now[0]], y=[now[1]], mode="markers", name="now",
        marker=dict(size=18, color=pal.NOW, line=dict(color="white", width=2)),
    ))
    fig.update_layout(
        title=f"{DISPLAY_NAMES['trajectory']} — patient {patient.pid} ({emb.mode} axes)",
        xaxis_title=emb.axis_labels[0], yaxis_title=emb.axis_labels[1],
        height=480, showlegend=True,
    )
    return fig


# --- Clinical view (the rendered hero) ---------------------------------------------------------
# The patient's path through the literal SpO₂ × RR plane. The warm background *is* the NEWS2
# Scale-1 sub-score for those two vitals (single-sourced from styx.readouts — no duplicated
# thresholds, no new maths), so the shading is clinically honest, not decorative. Static
# retrospective replay parked at the late NEWS2 breach; the interactive scrub follows in 6d.2.

_SPO2_LO, _SPO2_HI = 85.0, 100.0  # SpO₂ axis (%), worse to the left
_RR_LO, _RR_HI = 8.0, 32.0  # respiratory rate axis (breaths/min), worse upward
_SPO2_DIV, _RR_DIV = 94.0, 20.5  # faint quadrant dividers
_GRID = 160  # warm-field resolution per axis


def _warm_colorscale() -> list[list]:
    """A discrete (crisp-banded) Plotly colorscale over the 7-stop warm ramp, for z = 0..6 pts."""
    k = len(pal.WARM_RAMP)
    cs: list[list] = []
    for i, c in enumerate(pal.WARM_RAMP):
        cs.append([i / k, c])
        cs.append([(i + 1) / k, c])
    return cs


def _warm_field() -> go.Heatmap:
    """Background heatmap: the NEWS2 Scale-1 sub-score (SpO₂ + RR) over the plane, white→terracotta."""
    spo2 = np.linspace(_SPO2_LO, _SPO2_HI, _GRID)
    rr = np.linspace(_RR_LO, _RR_HI, _GRID)
    sp, rrg = np.meshgrid(spo2, rr)
    field = np.minimum(_spo2_scale1_score(sp) + _rr_score(rrg), 6)
    return go.Heatmap(
        x=spo2, y=rr, z=field, zmin=0, zmax=6, zsmooth=False, showscale=False,
        colorscale=_warm_colorscale(), hoverinfo="skip", name="news2 points",
    )


def _smooth(a: np.ndarray, w: int = 5) -> np.ndarray:
    """Light centred moving average — presentation only (legibility), not modelling."""
    if a.size < w:
        return a
    pad = w // 2
    return np.convolve(np.pad(a, pad, mode="edge"), np.ones(w) / w, mode="valid")


def _idx(patient: Patient, t_min: float) -> int:
    """Nearest sample index to a sim-minute."""
    return int(np.argmin(np.abs(patient.t_min - t_min)))


def _add_quadrants(fig: go.Figure) -> None:
    """Four named regions + faint dividers (sentence case; silent hypoxia emphasised)."""
    fig.add_vline(x=_SPO2_DIV, line=dict(color="#C9C9C9", width=0.9, dash="dot"))
    fig.add_hline(y=_RR_DIV, line=dict(color="#C9C9C9", width=0.9, dash="dot"))
    quads = [
        (89.0, 28.5, "Decompensating", "effort failing · sats falling", "#1A1A1A", 12.5),
        (97.0, 28.5, "Compensating", "working harder · sats held", "#1A1A1A", 12.5),
        (89.0, 11.0, "Silent hypoxia", "sats falling · no distress", "#1A1A1A", 13.5),
        (97.0, 11.0, "Stable", "effort normal · sats held", "#8A8A8A", 12.0),
    ]
    for x, y, name, desc, col, sz in quads:
        fig.add_annotation(
            x=x, y=y, text=f"<b>{name}</b><br>{desc}", showarrow=False,
            font=dict(size=sz, color=col), align="center",
            bgcolor="rgba(255,255,255,0.0)",
        )


def _add_news2_boundary(fig: go.Figure) -> None:
    """The one emphasised clinical line: the NEWS2 single-parameter red boundary (≥ 3 points)."""
    line = dict(color=pal.THRESHOLD, width=1.9, dash="dash")
    fig.add_shape(type="line", x0=91, x1=91, y0=_RR_LO, y1=24.5, line=line)
    fig.add_shape(type="line", x0=91, x1=_SPO2_HI, y0=24.5, y1=24.5, line=line)
    fig.add_annotation(
        x=91.3, y=23.0, text="NEWS2 escalation (≥ 3 points)", showarrow=False,
        font=dict(size=10, color=pal.THRESHOLD), xanchor="left", yanchor="top",
    )


def clinical_trajectory_figure(
    patient: Patient,
    *,
    decoupling_min: float | None,
    aegis_min: float | None,
    escalation_min: float | None,  # F4 = fire.threshold_min
    news2_min: float | None,
    echo_endpoints: Sequence[tuple[float, float]] = (),  # escalated look-alike (SpO₂, RR) ends
) -> go.Figure:
    """The patient's path through the SpO₂ × RR clinical plane — the rendered hero (clinical view).

    Static retrospective replay: ``now`` is parked at the latest cascade event (the late NEWS2
    breach), and the path is drawn up to it. Geometry is wholly data-driven — markers sit on the
    real trajectory at each fire-time; nothing is hardcoded. The decoupling marker is framed as a
    *mechanism* (the coupling breaking down), not an alert; the lead is the early-warning-vs-NEWS2
    gap. No new maths — the digest is untouched.
    """
    spo2_all, rr_all = patient.vitals["SpO2"], patient.vitals["RR"]
    cascade = [m for m in (decoupling_min, aegis_min, escalation_min, news2_min) if m is not None]
    now_min = max(cascade) if cascade else float(patient.t_min[-1])
    now_i = _idx(patient, now_min)
    xs, ys = _smooth(spo2_all[: now_i + 1]), _smooth(rr_all[: now_i + 1])

    fig = go.Figure()
    fig.add_trace(_warm_field())
    _add_quadrants(fig)
    _add_news2_boundary(fig)

    # the path so far (old → new conveyed by the heading arrow + the "now" ring)
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines", name="path so far", hoverinfo="skip",
        line=dict(color=pal.NEUTRAL, width=2.6),
    ))
    if xs.size >= 2:
        fig.add_annotation(
            x=xs[-1], y=ys[-1], ax=xs[-2], ay=ys[-2], xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1.4, arrowwidth=2.4, arrowcolor=pal.NEUTRAL,
        )

    # the four cascade markers, numbered in time order — marker 1 is the mechanism, not an alert
    markers = [
        (1, decoupling_min, "triangle-up", pal.NEUTRAL, True, "coupling breaks down here"),
        (2, aegis_min, "diamond", pal.RISK, True, "early warning"),
        (3, escalation_min, "x", pal.RISK, True, "escalation crossing"),
        (4, news2_min, "diamond", pal.THRESHOLD, False, "NEWS2 fires"),
    ]
    for n, tmin, symbol, color, filled, hover in markers:
        if tmin is None:
            continue
        i = _idx(patient, tmin)
        mx, my = float(spo2_all[i]), float(rr_all[i])
        marker = dict(size=15, symbol=symbol, line=dict(color="white", width=1.4))
        if filled:
            marker["color"] = color
        else:  # hollow (the comparator) — outline carries it
            marker["color"] = "rgba(0,0,0,0)"
            marker["line"] = dict(color=color, width=2.6)
        fig.add_trace(go.Scatter(
            x=[mx], y=[my], mode="markers", name=f"{n} · {hover}", text=[hover],
            hovertemplate="%{text}<br>SpO₂ %{x:.0f} · RR %{y:.0f}<extra></extra>", marker=marker,
        ))
        fig.add_trace(go.Scatter(
            x=[mx + 0.45], y=[my + 1.0], mode="markers+text", text=[str(n)],
            textfont=dict(color="white", size=10), showlegend=False, hoverinfo="skip",
            marker=dict(size=20, color=color, line=dict(color="white", width=1.2)),
        ))

    # "now" — the retrospective replay cursor (a hollow ring)
    fig.add_trace(go.Scatter(
        x=[float(spo2_all[now_i])], y=[float(rr_all[now_i])], mode="markers", name="now",
        hovertemplate="now<extra></extra>",
        marker=dict(size=20, symbol="circle-open", color=pal.ANNOTATION, line=dict(width=2.4)),
    ))

    # the hero teaching point — real values across the marked stretch (first marker → now)
    start_min = next((m for m in (decoupling_min, aegis_min, escalation_min) if m is not None), None)
    d_i = _idx(patient, start_min) if start_min is not None else 0
    rr_lo, rr_hi = float(rr_all[d_i : now_i + 1].min()), float(rr_all[d_i : now_i + 1].max())
    sp_hi, sp_lo = float(spo2_all[d_i]), float(spo2_all[now_i])
    fig.add_annotation(
        x=(_SPO2_LO + _SPO2_HI) / 2, y=30.6, showarrow=False, align="center",
        text=(f"RR barely moves ({rr_lo:.0f}→{rr_hi:.0f}) while SpO₂ falls {sp_hi:.0f}→{sp_lo:.0f} — "
              "a threshold alarm scores nothing across this stretch."),
        font=dict(size=11, color="#1A1A1A"),
        bgcolor="rgba(255,255,255,0.9)", bordercolor="#9A9A9A", borderwidth=0.9, borderpad=5,
    )

    # the ≈5 h lead bracket — early-warning-vs-NEWS2 only (the framing-guard-correct comparison)
    if aegis_min is not None and news2_min is not None:
        lead_h = (news2_min - aegis_min) / 60.0
        fig.add_annotation(
            x=(_SPO2_LO + _SPO2_HI) / 2, y=9.2, showarrow=False, align="center",
            text=(f"≈ {lead_h:.0f} h lead · early warning {aegis_min:.0f} vs "
                  f"NEWS2 {news2_min:.0f} (sim-min)"),
            font=dict(size=10.5, color=pal.RISK),
        )

    # the past-deterioration cluster — escalated look-alikes' endpoints (no codename)
    if echo_endpoints:
        ex = [float(p[0]) for p in echo_endpoints]
        ey = [float(p[1]) for p in echo_endpoints]
        fig.add_trace(go.Scatter(
            x=ex, y=ey, mode="markers", name="past-deterioration cluster",
            hovertemplate="past deterioration<extra></extra>",
            marker=dict(size=9, symbol="circle", color="rgba(85,85,85,0.45)",
                        line=dict(color="white", width=0.8)),
        ))
        cx, cy = sum(ex) / len(ex), sum(ey) / len(ey)
        fig.add_shape(
            type="circle", xref="x", yref="y", line=dict(color="#8A8A8A", width=1.2, dash="dot"),
            x0=cx - 2.2, x1=cx + 2.2, y0=cy - 2.8, y1=cy + 2.8,
        )
        fig.add_annotation(x=cx, y=cy - 3.4, text="past-deterioration cluster", showarrow=False,
                           font=dict(size=9.2, color="#6F6F6F"))

    # roadmap caption (no clickable toggle), legend strip + honesty footnotes
    fig.add_annotation(xref="paper", yref="paper", x=1.0, y=1.07, showarrow=False,
                       text="Model view — on the roadmap", font=dict(size=10, color="#8A8A8A"),
                       xanchor="right")
    fig.add_annotation(
        xref="paper", yref="paper", x=0.0, y=-0.16, showarrow=False, xanchor="left", align="left",
        text=("Markers — STYX (blue): 1 coupling breaks down · 2 early warning · 3 escalation "
              "crossing.  NEWS2 (orange): 4 fires.  ○ now.  Shading — NEWS2 points for SpO₂ + RR "
              "(deeper = higher)."),
        font=dict(size=9.4, color="#444444"),
    )
    fig.add_annotation(
        xref="paper", yref="paper", x=0.0, y=-0.22, showarrow=False, xanchor="left", align="left",
        text=("Retrospective replay parked at the breach; in live use “now” sits back near the "
              "early warning, with hours of lead. Synthetic replay — not real patient data."),
        font=dict(size=9.0, color="#8A8A8A"),
    )

    fig.update_layout(
        title="Patient trajectory — clinical view",
        xaxis=dict(title="SpO₂ (%) — worse to the left", range=[_SPO2_LO, _SPO2_HI],
                   tickvals=[85, 88, 91, 94, 97, 100], showgrid=False),
        yaxis=dict(title="Respiratory rate (breaths/min) — worse upward", range=[_RR_LO, _RR_HI],
                   tickvals=[8, 12, 16, 20, 24, 28, 32], showgrid=False),
        height=620, showlegend=False, plot_bgcolor="white",
        margin=dict(l=70, r=40, t=70, b=120),
    )
    return fig
