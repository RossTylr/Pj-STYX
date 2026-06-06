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
# # 01 — Synthetic fidelity (Gate G1)
#
# Proof for the **root gate**: the synthetic COPD cohort contains the phenomena the MVP claims
# to detect. This notebook *imports* `styx.synth` (LYR-1 — never reimplements) and renders the
# three G1 panels: the dissociable **silent window**, the genuine **RR–SpO₂ decoupling** with its
# lead over the breach, and the **outcome-vs-history** correlation. Replay-of-synthetic only.

# %%
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from styx.config import DECOUPLING_LEAD_MIN, NORMAL_RANGES, VITALS
from styx.synth import (
    build_cohort,
    cohort_outcome_auc,
    decoupling_lead_min,
    has_silent_window,
    windowed_coherence,
)
from styx.synth.gates import breach_index, decoupling_onset_index

cohort = build_cohort(seed=42)
p = cohort.silent_case()
onset, breach = decoupling_onset_index(p), breach_index(p)
lead = decoupling_lead_min(p)
print(f"determinism (seed 42 ×2 identical): {cohort.equals(build_cohort(seed=42))}")
print(f"cohort size: {len(cohort.patients)}  |  silent window: {has_silent_window(p)}")
print(f"decoupling onset t={p.t_min[onset]:.0f}  breach t={p.t_min[breach]:.0f}  lead={lead:.0f} min")
print(f"lead ≥ G1 target ({DECOUPLING_LEAD_MIN} min): {lead >= DECOUPLING_LEAD_MIN}")
print(f"cohort outcome AUC from history: {cohort_outcome_auc(cohort):.3f}")

# %% [markdown]
# ## Panel 1 — the dissociable silent window
# Every vital stays inside its normal band (shaded) while RR rises and SpO₂ falls: a trend
# detector fires here where an absolute-threshold check stays silent.

# %%
fig1 = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=("RR", "SpO2"))
for row, v in enumerate(("RR", "SpO2"), start=1):
    r = NORMAL_RANGES[v]
    fig1.add_trace(go.Scatter(x=p.t_min, y=p.vitals[v], name=v, line=dict(color="#1b6")), row=row, col=1)
    fig1.add_hrect(y0=r.low, y1=r.high, fillcolor="#2a8", opacity=0.10, line_width=0, row=row, col=1)
fig1.add_vrect(
    x0=p.t_min[onset], x1=p.t_min[breach], fillcolor="#e80", opacity=0.15,
    line_width=0, annotation_text="silent window", annotation_position="top left",
)
fig1.update_layout(title="Silent window — vitals in range, trend adverse", height=480, showlegend=False)
fig1.write_html("outputs/01_silent_window.html")
fig1

# %% [markdown]
# ## Panel 2 — the RR–SpO₂ decoupling and its lead
# Detrended windowed coherence is high (~1) while the homeostatic compensation holds, then
# collapses at onset — **{lead} min before** the single-signal breach.

# %%
coh = np.abs(windowed_coherence(p.vitals["RR"], p.vitals["SpO2"]))
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=p.t_min, y=coh, name="|coherence|", line=dict(color="#36c")))
fig2.add_vline(x=p.t_min[onset], line=dict(color="#e80", dash="dash"), annotation_text="decoupling onset")
fig2.add_vline(x=p.t_min[breach], line=dict(color="#c33", dash="dash"), annotation_text="breach")
fig2.add_annotation(
    x=(p.t_min[onset] + p.t_min[breach]) / 2, y=0.5,
    text=f"lead = {lead:.0f} min", showarrow=False, font=dict(size=14, color="#333"),
)
fig2.update_layout(title="RR–SpO₂ coherence collapse precedes breach", height=420,
                   xaxis_title="sim-minutes", yaxis_title="|windowed coherence|")
fig2.write_html("outputs/01_decoupling_lead.html")
fig2

# %% [markdown]
# ## Panel 3 — history raises the *odds* of escalation (overlapping, not separable)
# Outcome is *sampled* from `sigmoid(k·(frailty − ½))`, and the model sees only the noisy
# observed `comorbidity_index` — so the two distributions overlap. The prior is learnable but
# not perfect: the AUC sits inside the G1 band, the honest signal a real model could capture.

# %%
proxy = np.array([pt.comorbidity_index for pt in cohort.patients])
escal = np.array([pt.outcome.name == "ESCALATED" for pt in cohort.patients])
fig3 = go.Figure()
for label, mask, color in (("ESCALATED", escal, "#c33"), ("RECOVERED", ~escal, "#2a8")):
    fig3.add_trace(go.Box(y=proxy[mask], name=label, marker_color=color, boxpoints="all"))
fig3.update_layout(title=f"Observed comorbidity proxy vs outcome (AUC={cohort_outcome_auc(cohort):.3f})",
                   height=420, yaxis_title="comorbidity index (observed events)")
fig3.write_html("outputs/01_outcome_vs_history.html")
fig3
