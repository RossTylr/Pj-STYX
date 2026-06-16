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
# # 06 — Cohort signal (pre-R1 measurement)
#
# **Read-only analysis — measures for a decision, ships no demo claim.** These numbers inform R1's
# design and the pitch; none becomes a demo claim without claim-integrity. Everything is framed as
# **construct validity** (does the detector recover what the generator scripted?), *not* real-ward
# performance — it is one synthetic cohort, scored in-sample.
#
# Four measurements:
# 1. **History's marginal value** — the go/no-go on R1's framing (claim vs descriptive).
# 2. **Watchlist precision/recall** vs outcomes at the silent-window frame.
# 3. **Quietest ∩ watchlist** — is the calmest patient silently deteriorating?
# 4. **New-low-history profile** — the R1 residual (caught by the signal, not the prior).

# %%
import numpy as np

from saturation_analysis import saturation_aucs  # §1 lifted to a shared helper (notebook 10 §11 reuses it)
from styx.cohort import build_cohort_context, ward_frame
from styx.risk import escalation_fire_index
from styx.synth import Outcome, build_cohort

cohort = build_cohort(seed=42)
cctx = build_cohort_context(cohort)
pats = cohort.patients
di = cctx.default_idx  # the silent-window frame (the demo's money shot)
t = cctx.t_min
y = np.array([1 if p.outcome is Outcome.ESCALATED else 0 for p in pats])
print(f"cohort n={len(pats)}, escalators={int(y.sum())}, silent-window frame di={di} (t={t[di]:.0f} min)")

# %% [markdown]
# ## 1. History's marginal value — R1's contract
#
# AUC predicting ESCALATED from {history-only} vs a small {telemetry} panel vs {combined}, all
# in-sample logistic regression (the `cohort_outcome_auc` pattern). History = the **observable**
# `comorbidity_index` (event-density proxy + noise), never latent frailty. Telemetry = the
# silent-window risk snapshot, the AEGIS-fired flag, and the trailing risk slope. The gap
# `combined − telemetry` **is** R1's marginal value: if ≈0, R1 is decorative as a *predictor* and
# should be reframed as *descriptive* (history *explains* the baseline) before it is built.

# %%
sat = saturation_aucs(cohort, cctx)  # the shared single-source computation
print(f"history-only (comorbidity_index):        AUC {sat.history:.3f}")
print(f"  telemetry singles — risk_snap {sat.risk_snap:.3f} · aegis_fired {sat.aegis_fired:.3f} · slope {sat.slope:.3f}")
print(f"telemetry-only (panel of 3):             AUC {sat.telemetry:.3f}")
print(f"history + telemetry (combined):          AUC {sat.combined:.3f}")
print(f"R1 MARGINAL VALUE (combined − telemetry): {sat.marginal:+.3f}")

# %% [markdown]
# **Read.** The silent-window telemetry already **saturates** AUC in-sample — a construct artifact:
# by `di` the escalating archetypes' risk has begun separating (the engine scripted them), so the
# snapshot already encodes who escalates. With no headroom above telemetry, history adds **no marginal
# predictive value** here. **Verdict: R1 is descriptive** — *history explains the baseline / basin /
# hazard*, it does not improve the prediction. (This is in-silico on one cohort; it bounds R1's
# *framing*, not a real-ward claim.)

# %% [markdown]
# ## 2. Watchlist precision / recall vs outcomes (construct validity)
#
# At the silent-window frame, the watchlist = the `silent_but_rising` rows (AEGIS fired, risk still
# pre-threshold). Precision = fraction of the watchlist that eventually escalates; recall = fraction
# of eventual escalators the watchlist caught; plus the median AEGIS→threshold lead for the caught.
# This asks whether the detector **recovers what the generator scripted** — not ward performance.

# %%
rows = ward_frame(cctx, di)
watch = {r.pid for r in rows if r.silent_but_rising}
esc = {p.pid for p in pats if p.outcome is Outcome.ESCALATED}
caught = watch & esc
precision = len(caught) / len(watch) if watch else float("nan")
recall = len(caught) / len(esc) if esc else float("nan")

leads = []
for pid in caught:
    ai, ei = cctx.aegis_idx[pid], escalation_fire_index(pats[pid], cctx.emb, cctx.basins, cctx.indices)
    if ai is not None and ei is not None:
        leads.append(float(t[ei] - t[ai]))
median_lead = float(np.median(leads))
print(f"watchlist={len(watch)} · escalators={len(esc)} · caught={len(caught)}")
print(f"precision={precision:.3f}  recall={recall:.3f}")
print(f"median AEGIS→threshold lead (caught): {median_lead:.0f} min  (n={len(leads)}, range {min(leads):.0f}–{max(leads):.0f})")

# %% [markdown]
# ## 3. Quietest ∩ watchlist
#
# Is the single calmest patient (lowest absolute exceedance) also on the watchlist — the "calmest
# patient is silently deteriorating" beat?

# %%
q = next(r for r in rows if r.quietest)
overlap = q.silent_but_rising
print(f"quietest pid={q.pid} · archetype={q.archetype} · status={q.status} · risk_now={q.risk_now:.3f}")
print(f"quietest on watchlist (silent_but_rising)? {overlap}")
print("→ the single quietest is genuinely stable; the silent-deterioration beat is carried by the"
      " silent-but-rising watchlist patients (e.g. patient 0), who read in-range but are NOT the"
      " single calmest." if not overlap else "→ the calmest patient is itself silently deteriorating.")

# %% [markdown]
# ## 4. New-low-history profile — the R1 residual
#
# Characterise the new-low-history case: bottom-quartile Theograph density, yet deteriorating —
# caught by the **live signal**, not the prior. This is the patient R1 (a history view) would *miss*.

# %%
densities = {p.pid: sum(p.theograph.values()) for p in pats}
q25 = float(np.quantile(list(densities.values()), 0.25))
nlh = [r for r in rows if r.new_low_history]
print(f"cohort density: q25={q25:.1f} · median={np.median(list(densities.values())):.1f}")
print(f"new-low-history pids: {[r.pid for r in nlh]}")
for r in nlh:
    p = pats[r.pid]
    print(f"  pid={r.pid} · density={densities[r.pid]} (<q25) · {r.archetype} · outcome={p.outcome.value}"
          f" · AEGIS idx={cctx.aegis_idx[r.pid]} (≤di) · risk_now={r.risk_now:.3f} · {r.status}")

# %% [markdown]
# **Summary (the four headline numbers — see `EXPERIMENT_LOG.md`):**
# 1. History marginal value `combined − telemetry ≈ 0.00` (telemetry saturates) → **R1 descriptive**.
# 2. Watchlist precision/recall `1.00 / 1.00`, median lead **270 min** — perfect construct validity.
# 3. Quietest (pid 2) is **stable, not on the watchlist** — overlap empty; the beat belongs to
#    patient 0, not the single calmest.
# 4. New-low-history = **pid 39** (density 15 < q25, compensated, escalated, AEGIS fired pre-`di`) —
#    the live-signal catch a history prior would miss.
