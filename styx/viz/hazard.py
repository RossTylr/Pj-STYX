"""R1 history-as-prior figure — two Kaplan–Meier curves stratified by care history. Pure builder.

No Streamlit, no I/O (LYR-1). The app and notebooks call this and own their own rendering. Reads the
``HazardStratification`` produced by ``styx.reach.history`` — it renders, it never recomputes.

Descriptive only: the panel face shows the two survival curves and which stratum this patient is in;
the hazard ratio / concordance / log-rank live in the caption and the explainer, off the face (a hub
nurse reads the picture, not the statistics).
"""

from __future__ import annotations

import plotly.graph_objects as go

from styx.explain import DISPLAY_NAMES
from styx.reach.history import HazardStratification
from styx.viz import palette as pal

# Each stratum carries a colour *and* a dash, so the two curves never read by hue alone (6l).
_STYLE: dict[str, tuple[str, str]] = {
    "high": (pal.EARLY_WARNING, "solid"),  # denser history — reaches escalation sooner
    "low": (pal.STABLE, "dash"),  # thinner history — holds longer
}


def hazard_figure(
    stratification: HazardStratification,
    *,
    focus_density: float | None = None,
) -> go.Figure:
    """Render the denser- vs thinner-history survival curves, marking this patient's stratum.

    ``focus_density`` is this patient's care-event density (``sum(theograph.values())``); compared to
    ``stratification.median_density`` it picks the stratum to highlight. Omit it to draw the two
    curves without a patient marker.
    """
    fig = go.Figure()
    focus_key = _focus_key(stratification, focus_density)

    for key, curve in (("high", stratification.high), ("low", stratification.low)):
        colour, dash = _STYLE[key]
        is_focus = key == focus_key
        fig.add_trace(go.Scatter(
            x=curve.t_min, y=curve.survival, mode="lines", name=curve.label,
            line=dict(color=colour, width=4 if is_focus else 2, dash=dash, shape="hv"),
        ))

    if focus_key is not None:
        label = (stratification.high if focus_key == "high" else stratification.low).label
        fig.add_annotation(
            x=0.02, y=0.08, xref="paper", yref="paper", showarrow=False, align="left",
            text=f"This patient: {label.lower()}", font=dict(color=pal.ANNOTATION),
        )
    if stratification.n_events == 0 or stratification.high.survival.size == 0 \
            or stratification.low.survival.size == 0:
        fig.add_annotation(
            x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
            text="insufficient history to stratify", font=dict(color=pal.NEUTRAL),
        )

    fig.update_layout(
        title=f"{DISPLAY_NAMES['history']} — denser recent care history reaches escalation sooner",
        xaxis_title="sim-minutes", yaxis_title="not yet escalated", yaxis_range=[0, 1],
        height=420, showlegend=True,
    )
    return fig


def _focus_key(stratification: HazardStratification, focus_density: float | None) -> str | None:
    """Which stratum the focus patient sits in — denser if above the median split, else thinner."""
    if focus_density is None:
        return None
    return "high" if focus_density > stratification.median_density else "low"
