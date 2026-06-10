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
# # 05 — Walkthrough (end-to-end story)
#
# The cumulative STYX narrative on the silent-hypoxia index case (patient 0), assembled from the
# same `styx` package the app calls (LYR-1). It grows with each slice; at **S4** it runs:
#
# > silent window → state-space drift → **AEGIS** flags → **forecast** projects the crossing →
# > **threshold** breaches → **Theograph** history in context → **CALLIOPE** says why, faithfully.
#
# Every panel is one `styx.viz` builder fed by one `styx` call. Replay-of-synthetic; no live data.

# %%
from styx.anticipation import fire_times, ghost_cone
from styx.config import THRESHOLDS
from styx.frame import build_context, patient_frame
from styx.synth import build_cohort
from styx.viz.cone import cone_figure
from styx.viz.theograph import detail_strip_figure, ribbon_figure
from styx.viz.trajectory import trajectory_figure
from styx.viz.waterline import waterline_figure

cohort = build_cohort(seed=42)
patient = cohort.silent_case()
ctx = build_context(cohort, patient)
ft = fire_times(cohort, patient)
threshold = THRESHOLDS.risk_escalation
now_idx = ctx.indices[-1]  # end of stay — the full story is visible
frame = patient_frame(ctx, now_idx)

print(f"patient {patient.pid} — archetype {patient.archetype.value}")
print(f"AEGIS → forecast → threshold: {ft.aegis_min:.0f} → {ft.forecast_min:.0f} → "
      f"{ft.threshold_min:.0f} min  (lead {ft.aegis_threshold_lead_min:.0f} min, ordered={ft.ordered})")
print(f"CALLIOPE: {frame.rationale.headline}")
print(f"SENTINEL confidence: {frame.sentinel:.0%} ({frame.sentinel_label})")

# %% [markdown]
# ## 1 — State-space drift (F1), with care events threaded onto the path (F3)
# The trajectory leaves the stability basin toward the silent-hypoxia crisis mode; in-episode care
# events are dropped at the path position where they occurred.

# %%
fig1 = trajectory_figure(patient, ctx.emb, ctx.basins, events=ctx.on_path)
fig1.write_html("outputs/05_1_trajectory.html")
fig1

# %% [markdown]
# ## 2 — Risk waterline (F4) + the AEGIS flag (F7)
# Risk rises early on the proximity term but only crosses the absolute threshold at breach; AEGIS
# fires far to the left, deep in the silent window.

# %%
fig2 = waterline_figure(patient.t_min, ctx.risk, threshold, aegis_idx=ctx.aegis_idx)
fig2.write_html("outputs/05_2_waterline.html")
fig2

# %% [markdown]
# ## 3 — Forecast cone (F2) + the ghost trail (F9)
# The live conformal cone projects the crossing; the **ghost** (dotted) is the forecast we'd have
# drawn back at the AEGIS fire-time, overlaid on the realised path — what STYX saw coming.

# %%
fig3 = cone_figure(patient.t_min, ctx.risk, frame.cone, threshold,
                   now_idx=now_idx, ghost=ghost_cone(cohort, patient))
fig3.write_html("outputs/05_3_cone_ghost.html")
fig3

# %% [markdown]
# ## 4 — Theograph (F3), dual-scale
# Lifelong care history (years) and the recent-days detail strip aligned to the live episode.

# %%
figR = ribbon_figure(ctx.events)
figR.write_html("outputs/05_4_ribbon.html")
figR

# %%
figD = detail_strip_figure(ctx.events)
figD.write_html("outputs/05_5_detail.html")
figD

# %% [markdown]
# ## 5 — CALLIOPE (F8) — the faithful rationale
# One tight clinician-facing line from the real top-1 risk driver, with the AEGIS context in the
# expand. Strict template, closed vocabulary (gate G4).

# %%
print(frame.rationale.headline)
if frame.rationale.additive:  # contributors only shown when they sum to the risk (pre-overshoot)
    for name, val in frame.rationale.top_k:
        print(f"  • {name}: {val:+.2f}")
for line in frame.rationale.context:
    print(f"  • {line}")
