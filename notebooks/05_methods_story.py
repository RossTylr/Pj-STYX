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
# # 05 — Methods story (DS credibility)
#
# The methods behind the MVP, for a data-science reader. Five panels, each importing `styx`
# (LYR-1 — never reimplements): **embedding legibility**, **conformal coverage** (empirical vs
# nominal — the calibration that backs UQ-1), **forecast reliability**, the **AEGIS→threshold lead**,
# and **ECHO retrieval sanity**. The demo is replay-of-synthetic — no real patient data, not a live
# deployment; every number below is computed on the seed=42 synthetic cohort.

# %%
import numpy as np
import plotly.graph_objects as go

from styx.anticipation import fire_times
from styx.cohort import build_cohort_context
from styx.cohort.echo import echo_neighbours
from styx.config import CONFORMAL_ALPHA, FORECAST_WINDOW, LEGIBILITY_THRESHOLD, THRESHOLDS
from styx.forecast import project
from styx.state import axis_construct_corr, now_position
from styx.synth import build_cohort

cohort = build_cohort(seed=42)
cctx = build_cohort_context(cohort)
emb, t = cctx.emb, cctx.t_min
threshold = THRESHOLDS.risk_escalation
print(f"cohort n={len(cohort.patients)}  ·  embedding mode={emb.mode}  ·  axes={emb.axis_labels}")

# %% [markdown]
# ## Panel A — embedding legibility (F1)
# The 2-D state space is legible only if each axis tracks its named physiological construct at
# |r| ≥ 0.60. The scatter is every patient's *now* position, coloured by archetype — the four
# deterioration shapes separate off-diagonal (silent hypoxia falls in oxygenation with flat effort;
# compensated climbs in effort holding oxygenation), which is exactly the structure ECHO matches on.

# %%
corr = axis_construct_corr(cohort, emb)
print(f"axis correlations: {{ {', '.join(f'{k}: {v:.3f}' for k, v in corr.items())} }}  "
      f"(legible ≥ {LEGIBILITY_THRESHOLD})")
figA = go.Figure()
for arch in sorted({p.archetype for p in cohort.patients}, key=lambda a: a.value):
    members = [p for p in cohort.patients if p.archetype is arch]
    pos = np.array([now_position(p, emb) for p in members])
    figA.add_trace(go.Scatter(x=pos[:, 0], y=pos[:, 1], mode="markers", name=arch.value,
                              marker=dict(size=8)))
figA.update_layout(title="State-space now-positions by archetype (legible oxygenation × effort)",
                   xaxis_title=emb.axis_labels[0], yaxis_title=emb.axis_labels[1], height=460)
figA.write_html("outputs/05_embedding_legibility.html")
figA

# %% [markdown]
# ## Panel B — conformal coverage: empirical vs nominal (UQ-1)
# The forecast cone is a split-conformal band calibrated to the nominal **1−α = 0.90**. Coverage is
# the headline honesty check: at every re-score and every horizon step, is the realised risk inside
# the projected band? We sweep all patients and all valid now-positions and measure the empirical
# coverage per horizon step. It should sit near 0.90 — marginal (pooled), not a per-patient
# guarantee, which is what the band claims and no more.

# %%
nominal = 1.0 - CONFORMAL_ALPHA
horizon = cctx.band.size
n = t.size
hits = np.zeros(horizon)
total = np.zeros(horizon)
for pid, risk in cctx.risk.items():
    for now_idx in range(FORECAST_WINDOW - 1, n - 1):
        cone = project(risk, t, now_idx, cctx.band)
        for k in range(horizon):
            j = now_idx + 1 + k
            if j >= n:
                break
            inside = cone.lower[k] <= risk[j] <= cone.upper[k]
            hits[k] += float(inside)
            total[k] += 1.0
coverage = hits / np.maximum(total, 1.0)
print(f"empirical coverage: mean={coverage.mean():.3f}  "
      f"min={coverage.min():.3f}  max={coverage.max():.3f}  (nominal {nominal:.2f})")
figB = go.Figure()
figB.add_trace(go.Scatter(x=np.arange(1, horizon + 1), y=coverage, mode="lines+markers",
                          name="empirical", line=dict(color="#36c", width=2)))
figB.add_hline(y=nominal, line=dict(color="#c33", dash="dot"),
               annotation_text=f"nominal {nominal:.2f}")
figB.update_layout(title="Conformal coverage — empirical vs nominal across the horizon",
                   xaxis_title="horizon step", yaxis_title="coverage", yaxis_range=[0.0, 1.0],
                   height=420)
figB.write_html("outputs/05_conformal_coverage.html")
figB

# %% [markdown]
# ## Panel C — forecast reliability
# Beyond coverage, is the *point* forecast unbiased? We bin the projected risk against the realised
# risk one horizon ahead, pooled over the cohort, and plot against the y=x line. Points on the
# diagonal mean the trend projection is calibrated in the mean, not just in its band.

# %%
pred, real = [], []
for pid, risk in cctx.risk.items():
    for now_idx in range(FORECAST_WINDOW - 1, n - cctx.band.size):
        cone = project(risk, t, now_idx, cctx.band)
        pred.append(float(cone.point[-1]))
        real.append(float(risk[now_idx + cctx.band.size]))
pred, real = np.array(pred), np.array(real)
edges = np.linspace(0.0, 1.0, 11)
centres, means = [], []
for lo, hi in zip(edges[:-1], edges[1:]):
    m = (pred >= lo) & (pred < hi)
    if m.any():
        centres.append((lo + hi) / 2.0)
        means.append(float(real[m].mean()))
figC = go.Figure()
figC.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="ideal (y=x)",
                          line=dict(color="#c33", dash="dot")))
figC.add_trace(go.Scatter(x=centres, y=means, mode="lines+markers", name="observed",
                          line=dict(color="#2a8", width=2)))
figC.update_layout(title="Forecast reliability — predicted vs realised risk (binned)",
                   xaxis_title="predicted risk", yaxis_title="realised risk", height=420)
figC.write_html("outputs/05_forecast_reliability.html")
figC

# %% [markdown]
# ## Panel D — the AEGIS→threshold lead, across the escalators
# The headline clinical number: how long before the threshold alarm does AEGIS fire? On the index
# case it is **210 min**; across the escalating cohort it is a distribution, never thin.

# %%
leads = []
for p in cohort.patients:
    ft = fire_times(cohort, p)
    if ft.aegis_threshold_lead_min is not None:
        leads.append(ft.aegis_threshold_lead_min)
leads = np.array(leads)
p0_lead = fire_times(cohort, cohort.silent_case()).aegis_threshold_lead_min
print(f"AEGIS→threshold lead: patient-0={p0_lead:.0f} min  ·  "
      f"cohort n={leads.size} median={np.median(leads):.0f} min  min={leads.min():.0f} min")
figD = go.Figure()
figD.add_trace(go.Histogram(x=leads, nbinsx=12, marker=dict(color="#36c")))
figD.add_vline(x=p0_lead, line=dict(color="#e80", width=2, dash="dash"),
               annotation_text=f"patient 0 ({p0_lead:.0f} min)")
figD.update_layout(title="AEGIS→threshold lead across escalators (sim-minutes)",
                   xaxis_title="lead (min)", yaxis_title="patients", height=420)
figD.write_html("outputs/05_lead_distribution.html")
figD

# %% [markdown]
# ## Panel E — ECHO retrieval sanity (F10)
# ECHO grounds a case in look-alikes — it must retrieve *like with like*. For a focus patient we
# pull the 3 nearest trajectories by shape and check they share its archetype. ECHO illustrates with
# similar synthetic patients and their synthetic outcomes; it does not forecast this patient.

# %%
now_idx = cctx.default_idx
shares = 0
checked = 0
for p in cohort.patients:
    if p.archetype.value == "stable":
        continue
    ns = echo_neighbours(cctx, p.pid, now_idx)
    shares += sum(n.archetype == p.archetype.value for n in ns)
    checked += len(ns)
print(f"ECHO neighbours sharing the focus archetype: {shares}/{checked} = {shares / checked:.3f}")
focus = cohort.silent_case().pid
ns = echo_neighbours(cctx, focus, now_idx)
print(f"patient {focus} ({cohort.silent_case().archetype.value}) nearest:")
for nb in ns:
    print(f"  patient {nb.pid}  {nb.archetype}  {nb.outcome}  d={nb.distance:.3f}")
from styx.viz.echo import echo_figure  # noqa: E402 — local to this panel

figE = echo_figure(cctx, focus, ns, now_idx)
figE.write_html("outputs/05_echo_retrieval.html")
figE
