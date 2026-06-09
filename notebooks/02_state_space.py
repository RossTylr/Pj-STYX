# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 02 — State space (Gate G2)
#
# Proof for **F1**, the legible trajectory hero: the 5-D `VITALS` vector projected to a 2-D state
# space whose axes are *named* physiological constructs (oxygenation, effort), with a learned
# stability **basin** and crisis **attractor**. Imports `styx.state` (LYR-1 — never reimplements).
# G2 is the fork: keep PCA if its axes clear |r| ≥ 0.60 against the constructs, else fall back to
# the hand-built oxygenation × effort projection. Either is a valid pass.

# %%
import plotly.graph_objects as go

from styx.config import LEGIBILITY_THRESHOLD
from styx.state import (
    axis_construct_corr,
    fit_embedding,
    is_legible,
    learn_basins,
    now_position,
    trajectory_drift,
)
from styx.synth import Archetype, build_cohort
from styx.viz.trajectory import trajectory_figure

cohort = build_cohort(seed=42)
emb = fit_embedding(cohort)
basins = learn_basins(cohort, emb)
corrs = axis_construct_corr(cohort, emb)
p_silent = cohort.silent_case()
emb2 = fit_embedding(build_cohort(seed=42))

same = emb.mode == emb2.mode and (emb.components_ == emb2.components_).all()
drift = trajectory_drift(p_silent, emb, basins)
print(f"determinism (seed 42 ×2 identical embedding): {same}")
print(f"embedding mode: {emb.mode}  |  axis labels: {emb.axis_labels}")
print(f"axis↔construct corr: {dict((k, round(v, 4)) for k, v in corrs.items())}")
print(f"legible at |r| ≥ {LEGIBILITY_THRESHOLD}: {is_legible(corrs, LEGIBILITY_THRESHOLD)}")
print(f"silent-case basin→attractor drift: {drift:+.3f} (>0 = toward crisis)")

# %% [markdown]
# ## Panel A — the axes are legible
# Each latent axis correlates with its named construct above the 0.60 line. If PCA's axes failed
# (they collapse the anti-correlated oxygenation/effort onto one PC, leaving the other on labs),
# the fork fell back to the constructed projection — legible by construction.

# %%
figA = go.Figure()
figA.add_trace(go.Bar(x=list(corrs.keys()), y=[abs(v) for v in corrs.values()],
                      marker_color="#36c", text=[f"{v:+.3f}" for v in corrs.values()]))
figA.add_hline(y=LEGIBILITY_THRESHOLD, line=dict(color="#c33", dash="dash"),
               annotation_text=f"G2 threshold {LEGIBILITY_THRESHOLD}")
figA.update_layout(title=f"Axis ↔ construct legibility ({emb.mode} axes)",
                   yaxis_title="|Pearson r|", height=400, yaxis_range=[0, 1.05])
figA.write_html("outputs/02_axis_legibility.html")
figA

# %% [markdown]
# ## Panel B — the archetypes separate off-diagonal
# Every patient's *now* position, coloured by deterioration archetype. Silent-hypoxia (SpO₂ falls,
# effort flat) and compensated (effort climbs, SpO₂ holds) land on **opposite ends of the effort
# axis** — genuine 2-D spread, not one diagonal. This is the differentiator a single risk line can't
# show: two patients equally "deteriorating" sit in clinically different regions of the state space.

# %%
_COLORS = {"silent_hypoxia": "#c33", "compensated": "#e80", "coupled": "#a4c", "stable": "#2a8"}
figB = go.Figure()
for arch in Archetype:
    pts = [now_position(p, emb) for p in cohort.patients if p.archetype is arch]
    if pts:
        xs, ys = zip(*pts)
        figB.add_trace(go.Scatter(x=xs, y=ys, mode="markers", name=arch.value,
                                  marker=dict(size=9, color=_COLORS[arch.value])))
figB.update_layout(title=f"Now-position by archetype ({emb.mode} axes)",
                   xaxis_title=emb.axis_labels[0], yaxis_title=emb.axis_labels[1], height=460)
figB.write_html("outputs/02_archetype_separation.html")
figB

# %% [markdown]
# ## Panel C — three labelled trajectories, visibly different shapes
# One stay per deteriorating archetype: silent-hypoxia (patient 0) drifts toward the attractor along
# oxygenation with effort flat; compensated climbs the effort axis; coupled tracks the diagonal.

# %%
examples = {"silent": p_silent}
examples["compensated"] = next(p for p in cohort.patients if p.archetype is Archetype.COMPENSATED)
examples["coupled"] = next(p for p in cohort.patients if p.archetype is Archetype.COUPLED)
for tag, pt in examples.items():
    fig = trajectory_figure(pt, emb, basins)
    fig.write_html(f"outputs/02_trajectory_{tag}.html")
    fig.show()
