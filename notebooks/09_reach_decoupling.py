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
# # 09 — R3 CADUCEUS · decoupling onset + cascade verdict (proof)
#
# **Temporal-mechanistic, not predictive — no accuracy/lift claim.** This reach surfaces *why* the
# silent deterioration is silent: the RR–SpO₂ homeostatic coupling collapses before any single vital
# leaves its range. It is read straight off the **existing G1 computation**
# (`synth.gates.windowed_coherence` / `decoupling_onset_index` / `decoupling_lead_min` — the same
# maths that produced the G1 lead 200); nothing is recomputed and nothing in synth/forecast/risk is
# touched. One synthetic silent case (patient 0), replay-of-synthetic.
#
# This notebook settles the **pending cascade decision**: how many STYX markers the eventual 6-d
# state-space carries — is the decoupling onset *detectably earlier* than AEGIS (3 markers), or
# near-coincident (2)? NEWS2 stays the external marker either way. **Measure, don't assume.**

# %%
import sys
from pathlib import Path

import numpy as np
import plotly.graph_objects as go

from styx.config import RESCORE_CADENCE_MIN
from styx.reach.decoupling import cascade_verdict, decoupling_onset
from styx.synth import build_cohort
from styx.synth.gates import _DROP_K, _SUSTAIN, decoupling_lead_min, decoupling_onset_index

cohort = build_cohort(seed=42)
p = cohort.silent_case()
d = decoupling_onset(p)
print(f"decoupling onset = sample {d.onset_index} = {d.onset_min:.0f} sim-min")
print(f"first single-signal breach = {d.breach_min:.0f} sim-min   silent_window = {d.silent_window}")

# %% [markdown]
# ## Single-source check — this *is* the G1-lead signal
#
# The onset and the lead the reach reports are the *same numbers* G1 gates on — not an independent
# recompute. The reach calls `decoupling_onset_index` / `decoupling_lead_min` directly, so equality
# here is by construction (the proof is that nothing else computes a competing coherence).

# %%
assert d.onset_index == decoupling_onset_index(p), "onset drifted from the gates computation"
assert d.g1_lead_min == decoupling_lead_min(p), "lead drifted from the gates computation"
print(f"G1 lead reproduced from windowed_coherence = {d.g1_lead_min:.0f} sim-min  (onset → breach)")
print("single source confirmed: the decoupling signal here IS the G1-lead signal (same maths).")

# %% [markdown]
# ## Claim-integrity — is the coherence drop a real, legible mechanism?
#
# The face: |detrended rolling Pearson r| of RR vs SpO₂. The coupling sits near 1; at decoupling the
# residuals go independent and it collapses. The onset is the first sample sustained (≥ `_SUSTAIN`
# windows) below the pre-onset baseline by `_DROP_K`, and the silent window holds (vitals in range,
# SpO₂ falling). **Verdict: pass / illustrative / cut.**

# %%
coh = np.abs(d.coherence)
stable = coh[: p.t_min.size // 3]
baseline = float(np.nanmedian(stable[~np.isnan(stable)]))
thresh = baseline - _DROP_K
fig = go.Figure()
fig.add_trace(go.Scatter(x=p.t_min, y=coh, mode="lines", name="|RR–SpO₂ coherence|",
                         line=dict(color="#2980b9", width=2)))
fig.add_hline(y=thresh, line_dash="dot", line_color="#7f8c8d",
              annotation_text=f"onset threshold (baseline {baseline:.2f} − {_DROP_K})")
fig.add_vline(x=d.onset_min, line_dash="dash", line_color="#c0392b",
              annotation_text=f"decoupling onset {d.onset_min:.0f}")
fig.add_vline(x=d.breach_min, line_color="#000000",
              annotation_text=f"breach {d.breach_min:.0f}")
fig.update_layout(title="CADUCEUS — RR–SpO₂ decoupling onset (read off the G1 coherence series)",
                  xaxis_title="sim-minutes", yaxis_title="|coherence|",
                  template="plotly_white", height=420)
fig.show()

real = d.silent_window and d.onset_index is not None and d.g1_lead_min > 0
print(f"CLAIM-INTEGRITY VERDICT: {'PASS' if real else 'CUT'} "
      f"— sustained ≥{_SUSTAIN} windows, silent window holds, lead {d.g1_lead_min:.0f} min.")

# %% [markdown]
# ## Cascade verdict — the gate output (2 vs 3 STYX markers)
#
# The decoupling onset (raw mechanism onset) against the AEGIS fire (the *served* S3 signal, from the
# single source `anticipation.fire_times`). A decoupling onset is its own marker only when it leads
# AEGIS by more than one re-score cadence (15 min); otherwise it is near-coincident with AEGIS.

# %%
v = cascade_verdict(cohort, p)
print(f"decoupling onset = {v.onset_min:.0f} sim-min")
print(f"AEGIS fire       = {v.aegis_min:.0f} sim-min  (at-cadence {RESCORE_CADENCE_MIN} min)")
print(f"gap (AEGIS − onset) = {v.gap_min:.0f} sim-min   (margin = {RESCORE_CADENCE_MIN} min)")
print()
print(f"CASCADE VERDICT: {v.markers} STYX markers "
      f"({'decoupling · AEGIS · F4' if v.markers == 3 else 'AEGIS · F4'}); "
      f"NEWS2 remains the external marker.")
if v.markers == 3:
    print(f"  → decoupling is detectably earlier than AEGIS (leads by {v.gap_min:.0f} min > "
          f"{RESCORE_CADENCE_MIN} min) — it carries its own marker.")
else:
    print(f"  → decoupling is near-coincident with AEGIS (gap {v.gap_min:.0f} min ≤ "
          f"{RESCORE_CADENCE_MIN} min) — AEGIS subsumes it.")
print("Mechanism-only: this is a temporal placement, not an accuracy or lift claim.")

# %% [markdown]
# ## Digest re-check — the read did not leak into core
#
# A reach is a read. If the determinism digest moved, this notebook (or the module) touched core —
# stop and report. Bit-identical means synth/forecast/risk are untouched and G1–G4 hold by construction.

# %%
sys.path.insert(0, str(Path("09_reach_decoupling.py").resolve().parent.parent))
from tests.test_baseline import pipeline_digest  # noqa: E402  (single-source digest fn)

_RECORDED = "9ea38949db8e5b8c19f969b9919d804013285fb78e0e48f5449c7e76336a5347"
digest = pipeline_digest(build_cohort(seed=42))
assert digest == _RECORDED, f"DIGEST MOVED — the read leaked into core: {digest}"
print(f"digest {digest[:8]}…{digest[-6:]} — bit-identical (core untouched).")
