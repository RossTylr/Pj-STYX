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
# # 03 — Anticipation lead (Gate G3)
#
# Proof for **F2 / F4 / F7**, the anticipation triple. On the silent-hypoxia index case (patient 0)
# three signals fire **in order and stay separated**:
#
# 1. **AEGIS (F7)** — a sustained departure from the patient's *personal baseline* in the 2-D state
#    space (the earliest flag; fires while every vital is still in range).
# 2. **Forecast cone (F2)** — the conformal cone's upper edge projecting the risk waterline *will*
#    cross the escalation threshold, before it actually does.
# 3. **F4 absolute threshold** — the risk waterline crossing 0.5, anchored to NEWS2-style range
#    exceedance, so it fires *last* (at the breach).
#
# The headline is the **AEGIS→threshold lead**, measured on the cadence-windowed re-score. Imports
# `styx.anticipation` (LYR-1 — never reimplements). The demo is replay-of-synthetic (no live data).

# %%
import plotly.graph_objects as go

from styx.anticipation import cadence_indices, fire_times
from styx.config import AEGIS_LEAD_FLOOR_MIN, RESCORE_CADENCE_MIN, THRESHOLDS
from styx.forecast import conformal_band, forecast_fire_index, project
from styx.risk import aegis_signal, risk_series
from styx.state import fit_embedding, learn_basins
from styx.synth import build_cohort
from styx.synth.gates import breach_index, decoupling_onset_index
from styx.viz.cone import cone_figure
from styx.viz.waterline import waterline_figure

cohort = build_cohort(seed=42)
emb = fit_embedding(cohort)
basins = learn_basins(cohort, emb)
p = cohort.silent_case()
t = p.t_min
threshold = THRESHOLDS.risk_escalation

at_cadence = fire_times(cohort, p, RESCORE_CADENCE_MIN)
raw = fire_times(cohort, p, cohort.dt_min)

onset_t, breach_t = float(t[decoupling_onset_index(p)]), float(t[breach_index(p)])
print(f"decoupling onset t={onset_t:.0f}  |  first breach t={breach_t:.0f}")
print(f"at-cadence ({RESCORE_CADENCE_MIN} min): AEGIS={at_cadence.aegis_min:.0f}  "
      f"forecast={at_cadence.forecast_min:.0f}  threshold={at_cadence.threshold_min:.0f}")
print(f"  order AEGIS<forecast<threshold: {at_cadence.ordered}")
print(f"  AEGIS→threshold lead (at-cadence): {at_cadence.aegis_threshold_lead_min:.0f} min")
print(f"raw (per-sample):  AEGIS={raw.aegis_min:.0f}  forecast={raw.forecast_min:.0f}  "
      f"threshold={raw.threshold_min:.0f}  | lead={raw.aegis_threshold_lead_min:.0f} min")
print(f"cadence preserves lead: |{at_cadence.aegis_threshold_lead_min:.0f} − "
      f"{raw.aegis_threshold_lead_min:.0f}| ≤ {RESCORE_CADENCE_MIN}")
print(f"G3 floor {AEGIS_LEAD_FLOOR_MIN} min cleared: "
      f"{at_cadence.aegis_threshold_lead_min >= AEGIS_LEAD_FLOOR_MIN}")

# %% [markdown]
# ## Panel A — the firing-order timeline (the dissociation)
# The risk waterline with the three fire times marked. AEGIS (orange) fires deep in the silent
# window while risk is still low; the forecast (blue) fires as the cone first projects the crossing;
# F4's absolute threshold (red) fires last, at the breach. The grey band is the AEGIS→threshold lead
# — the window a trend monitor buys over a threshold alarm.

# %%
risk = risk_series(p, emb, basins)
figA = waterline_figure(t, risk, threshold, aegis_idx=None)
# Notebook owns rendering (LYR-1): overlay the three fire times + the lead band.
figA.add_vrect(x0=at_cadence.aegis_min, x1=at_cadence.threshold_min,
               fillcolor="#888", opacity=0.12, line_width=0,
               annotation_text=f"lead {at_cadence.aegis_threshold_lead_min:.0f} min")
for x, color, label in [(at_cadence.aegis_min, "#e80", "AEGIS (F7)"),
                        (at_cadence.forecast_min, "#36c", "forecast (F2)"),
                        (at_cadence.threshold_min, "#c33", "threshold (F4)")]:
    figA.add_vline(x=x, line=dict(color=color, width=2, dash="dash"), annotation_text=label)
figA.update_layout(title="Anticipation dissociation — AEGIS → forecast → threshold (patient 0)")
figA.write_html("outputs/03_firing_order.html")
figA

# %% [markdown]
# ## Panel B — the forecast cone at the moment it fires
# The conformal cone (UQ-1) at the forecast-fire re-score: the point forecast (dashed) projects the
# rising risk forward, the shaded band widens honestly with the horizon, and its upper edge reaches
# the escalation threshold — the projection that fires F2 before F4's line is actually crossed.

# %%
idx = cadence_indices(p, RESCORE_CADENCE_MIN)
calibration = [risk_series(q, emb, basins) for q in cohort.patients if q.pid != p.pid]
band = conformal_band(calibration, t)
fire_idx = forecast_fire_index(risk, t, band, threshold, idx)
cone = project(risk, t, fire_idx, band)
figB = cone_figure(t, risk, cone, threshold, now_idx=fire_idx)
figB.update_layout(title=f"Forecast cone at fire (now t={t[fire_idx]:.0f}) — upper edge reaches threshold")
figB.write_html("outputs/03_forecast_cone.html")
figB

# %% [markdown]
# ## Panel C — why AEGIS fires first: the baseline-departure signal
# AEGIS watches the trend-smoothed 2-D state position depart the patient's personal baseline (σ
# units, max over both named axes — so it generalises to effort-led deterioration too, not just
# hypoxia). The sustained crossing of K=3σ is the silent flag, well inside the in-range window.

# %%
from styx.config import AEGIS_K  # noqa: E402 — local to this panel

sig = aegis_signal(p, emb)
figC = go.Figure()
figC.add_trace(go.Scatter(x=t, y=sig, mode="lines", name="baseline departure (σ)",
                          line=dict(color="#e80", width=2)))
figC.add_hline(y=AEGIS_K, line=dict(color="#c33", dash="dot"), annotation_text=f"K={AEGIS_K}σ")
figC.add_vrect(x0=onset_t, x1=breach_t, fillcolor="#36c", opacity=0.08, line_width=0,
               annotation_text="silent window")
figC.add_vline(x=at_cadence.aegis_min, line=dict(color="#e80", width=2, dash="dash"),
               annotation_text="AEGIS fires")
figC.update_layout(title="AEGIS — sustained personal-baseline departure (patient 0)",
                   xaxis_title="sim-minutes", yaxis_title="departure (σ)", height=400)
figC.write_html("outputs/03_aegis_signal.html")
figC
