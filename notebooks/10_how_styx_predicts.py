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
# # 10 — How STYX Predicts (visual mechanism walkthrough)
#
# The visual companion to `docs/STYX_METHODOLOGY.md`. This notebook *explains the
# mechanism* by which STYX anticipates deterioration — raw signal → state space →
# the AEGIS/decoupling/forecast/risk cascade → CALLIOPE rationale → cohort view —
# and closes on the saturation honesty and the limits.
#
# It is a **thin client over `styx/`** (LYR-1): every number and figure comes from
# the package's own builders and detectors. It reimplements no scoring logic.
#
# Built **phased**. §0 is implemented now; §1–§12 are stubbed headers, filled in
# later phases. The notebook is designed to restart-run-all clean at every phase.

# %% [markdown]
# ## §0 — Honesty preamble & deterministic load
#
# ### Plain
# Everything here runs on **synthetic patients** that we replay — there is **no real
# patient data**, and STYX is **not** deployed live or streaming. This notebook's job
# is to *show how the method works*; it makes **no performance claim**. Any accuracy
# figures it reports are measured **on the same synthetic data the model saw**
# (in-sample), so they describe behaviour, not real-ward performance.
#
# **Scope caveat** — this is a *single acute-respiratory-infection cohort* scored
# against **NEWS2 Scale 1**. The warm band shading is clinically *wrong* for a patient
# on **Scale 2** (e.g. COPD / hypercapnic respiratory failure, target SpO₂ 88–92%).
#
# ### Dev
# We load the canonical cohort once with `build_cohort(seed=42)` and pin two
# invariants before anything else runs: (1) **DET-1** — building twice at the same
# seed is bit-identical (`Cohort.equals`); (2) the **pipeline digest** — a SHA-256
# over every patient's vitals streams, Theograph counts and risk waterline — matches
# the recorded baseline. The digest helper is imported from `tests.test_baseline`
# (the same single source `tests/test_observations.py` asserts against), so this
# notebook can never silently drift from the regression sentinel. `cohort.silent_case()`
# returns the scripted index patient (pid 0) used throughout §1–§9.
#
# ### Tech
# `pipeline_digest` traverses `cohort.patients` (an ordered tuple) in pid order,
# hashing `np.ascontiguousarray(...).tobytes()` of each vital in `VITALS`, the
# Theograph counts in sorted-key order (no dict-iteration-order dependence), and the
# per-patient risk series from `build_cohort_context`. Nurse obs are deliberately
# **excluded** — they are comparator-only and must never leak into a model path, which
# is exactly why the digest stays stable when only the obs change. Determinism rests
# on `SEED=42` threaded into the generator (DET-1: no module-level RNG). Failure mode:
# if any modelling change moves the streams/events/scores, the digest assertion below
# fires loudly — that is the intended regression tripwire, not a number to update here.
#
# **Three-register convention** — every numbered section (§1–§12) carries three
# labelled markdown blocks before its code:
# - **Plain** — for clinicians/stakeholders; no maths.
# - **Dev** — for engineers; inputs/outputs, shapes, where it lives in `styx/`.
# - **Tech** — for data scientists; the maths, parameters, assumptions, failure modes.

# %%
import sys
from pathlib import Path

# Repo-root bootstrap so the regression sentinel in `tests/` is importable when the
# kernel's cwd is `notebooks/` (no root conftest; `tests` is not a declared package).
_root = next(d for d in [Path.cwd(), *Path.cwd().parents] if (d / "pyproject.toml").is_file())
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

# Emit a static PNG (kaleido) alongside the interactive figure so the committed .ipynb
# renders on github.com (its viewer runs no JS); Jupyter still gets the live mimetype.
import plotly.io as pio  # noqa: E402

pio.renderers.default = "plotly_mimetype+png"

from styx.config import SEED  # noqa: E402
from styx.synth import build_cohort  # noqa: E402
from tests.test_baseline import pipeline_digest  # noqa: E402  single-source w/ test_observations.py

# Pinned regression sentinel — must reproduce exactly (tests/test_observations.py:30).
CANONICAL_DIGEST = "c9380e9cf7c134a82f2a45dd15c9769129540eee3c7d5db5aa54dc587860b1d9"

cohort = build_cohort(seed=SEED)
assert cohort.equals(build_cohort(seed=SEED)), "DET-1: seed 42 ×2 must be bit-identical"

digest = pipeline_digest(cohort)
assert digest == CANONICAL_DIGEST, f"DIGEST MOVED — a read leaked into core: {digest}"

p = cohort.silent_case()
print(f"seed={SEED}  digest={digest[:8]}…{digest[-7:]}  (matches recorded baseline)")
print(
    f"cohort n={len(cohort.patients)}  ·  index pid={p.pid}  ·  "
    f"archetype={p.archetype.value}  ·  outcome={p.outcome.name}"
)
print("framing: synthetic replay · in-sample · mechanism walkthrough, no performance claim")

# %% [markdown]
# ## §1 — Raw signal: the four vitals
#
# ### Plain
# Here are the index patient's four wearable vitals — breathing rate, oxygen (SpO₂),
# heart rate, temperature — across the whole stay, with the NEWS2 colour bands behind
# each. **If you only glance at the numbers, the patient looks fine**: early on the
# readings sit in their normal (white) bands, and even as they drift no single number
# is alarming — a spot check reads "unremarkable" right up until the late oxygen dip.
# That is exactly the trap STYX is built for: the numbers stay calm while the
# *trajectory* is already turning.
#
# ### Dev
# Vitals come from `cohort.silent_case().vitals` (a `dict[str, np.ndarray]` keyed by
# `styx.config.VITALS = (RR, SpO2, HR, temp)`, each length-N on the shared `p.t_min`
# grid). The band shading is **not** hardcoded: it is derived by evaluating the
# Scale-1 per-parameter scoring functions in `styx.readouts` (`_rr_score`,
# `_spo2_scale1_score`, `_hr_score`, `_temp_score`) over each panel's value domain, so
# the bands track the single source of NEWS2 truth. Band colour is `palette.WARM_RAMP`
# indexed by sub-score. Output: a 4-row Plotly figure (new plotting — no per-vital band
# builder exists in `styx/viz`).
#
# ### Tech
# The telemetry grid is the cohort's `dt_min` step (the same stream NEWS2 and STYX both
# read — no frequency advantage to STYX). "In band" = the parameter's Scale-1 sub-score
# is 0; `_score_bands` finds contiguous equal-score runs of `score_fn(linspace(y0, y1))`
# and shades each as an `hrect`. Assumption: Scale 1 is correct for this ARI cohort
# (per §0 caveat — Scale 2 would mis-score a ~97% baseline). The "% of readings in band"
# stat below is computed from the 4 wearable sub-scores, not asserted (descriptive).

# %%
import numpy as np  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
from plotly.subplots import make_subplots  # noqa: E402

from styx.config import VITALS  # noqa: E402
from styx.readouts import (  # noqa: E402  band defs + comparator path — single source, never recomputed
    NEWS2_PARAM_LABELS,
    NEWS2_RED,
    NEWS2_TRIGGER,
    _hr_score,
    _news2_complete_subscores,
    _rr_score,
    _spo2_scale1_score,
    _temp_score,
    news2_complete,
    news2_complete_crossing,
    news2_crossing,
)
from styx.viz import palette as pal  # noqa: E402

p = cohort.silent_case()
t = p.t_min

_AXIS = {"RR": "RR (min⁻¹)", "SpO2": "SpO₂ (%)", "HR": "HR (min⁻¹)", "temp": "Temp (°C)"}
_SCORE_FN = {"RR": _rr_score, "SpO2": _spo2_scale1_score, "HR": _hr_score, "temp": _temp_score}


def _score_bands(score_fn, y0: float, y1: float, n: int = 1500):
    """Contiguous (lo, hi, sub-score) bands of ``score_fn`` over [y0, y1] — reuses readouts."""
    ys = np.linspace(y0, y1, n)
    s = score_fn(ys).astype(int)
    cut = np.flatnonzero(np.diff(s)) + 1
    starts, ends = np.concatenate(([0], cut)), np.concatenate((cut, [n]))
    return [(float(ys[a]), float(ys[b - 1]), int(s[a])) for a, b in zip(starts, ends)]


fig1 = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                     subplot_titles=[_AXIS[v] for v in VITALS])
for r, v in enumerate(VITALS, start=1):
    data = p.vitals[v]
    pad = 0.06 * float(data.max() - data.min()) + 0.5
    y0, y1 = float(data.min()) - pad, float(data.max()) + pad
    for lo, hi, sc in _score_bands(_SCORE_FN[v], y0, y1):
        fig1.add_hrect(y0=lo, y1=hi, row=r, col=1, line_width=0, layer="below",
                       fillcolor=pal.WARM_RAMP[sc], opacity=0.65)
    fig1.add_trace(go.Scatter(x=t, y=data, mode="lines", name=v, showlegend=False,
                              line=dict(color=pal.ANNOTATION, width=1.6)), row=r, col=1)
    fig1.update_yaxes(range=[y0, y1], row=r, col=1)

# "looks normal on a spot check" — fraction of samples where all 4 wearable params score 0
_in_band = float(np.mean(_news2_complete_subscores(p)[:4].max(axis=0) == 0))
fig1.add_annotation(
    x=0.5, y=1.07, xref="paper", yref="paper", showarrow=False,
    text=f"on {_in_band:.0%} of samples all four vitals score 0 — a spot check reads "
         f"'unremarkable' while the trajectory is already turning",
    font=dict(size=11, color=pal.ANNOTATION))
fig1.update_xaxes(title_text="stay clock (sim-min)", row=4, col=1)
fig1.update_layout(title="§1 — Raw vitals with NEWS2 Scale-1 bands (index patient, pid 0)",
                   height=720, margin=dict(t=90))
fig1.write_html(str(_root / "outputs" / "10_s1_raw_signal.html"))
print(f"§1 raw signal: {_in_band:.0%} of readings score 0 on all 4 wearable vitals")
fig1

# %% [markdown]
# ## §2 — NEWS2 over time
#
# ### Plain
# Now score that same stay with NEWS2. The aggregate barely moves — it **peaks at 3 and
# never reaches the urgent threshold of 5**. The single thing that finally trips NEWS2 is
# the oxygen reading falling to ≤91% — a single-parameter "red" — and it fires **late**.
# The two parameters a nurse adds (blood pressure, consciousness) stay normal throughout,
# so even the fuller 6-of-7 score escalates on nothing but that one late oxygen red.
#
# ### Dev
# The aggregate is `readouts.news2_complete(p)` and the per-parameter strip is
# `readouts._news2_complete_subscores(p)` (shape (6, N), rows = `NEWS2_PARAM_LABELS`).
# The escalation time is read from the **same comparator path the A/B uses** —
# `news2_complete_crossing` / `news2_crossing` (which call `_first_crossing_min` →
# `_news2_escalates`); NEWS2 is **not** recomputed here. Heat-strip colour reuses
# `palette.WARM_RAMP` as a discrete 0–6 scale. Output: a 2-row Plotly figure
# (aggregate line + sub-score heatmap).
#
# ### Tech
# RCP-2017 escalation is the *earliest-of* rule: aggregate ≥ `NEWS2_TRIGGER` (5) OR any
# single parameter scoring a red `NEWS2_RED` (3). On this scenario the aggregate maxes at
# 3, so an aggregate-only trigger would never fire — the SpO₂ ≤91 red at 1010 sim-min is
# the entire escalation (load-bearing, pinned in the self-check). Nurse obs (BP, ACVPU)
# are step-held at the 4-hourly round and preserved in band 0, so the complete score
# equals the partial here and adds no earlier crossing. Failure mode: a synth change that
# lifted the aggregate to 5 would make NEWS2 fire aggregate-first — the assertions catch it.

# %%
agg = news2_complete(p)               # 6-of-7 aggregate (equals the 4-param partial here)
sub6 = _news2_complete_subscores(p)   # (6, N) per-parameter Scale-1 sub-scores
cross = news2_complete_crossing(p)    # == news2_crossing(p) == 1010.0 (single-source fire-time)

# discrete warm colourscale keyed to the comparator's own 0–6 points field
_cscale = []
for i, c in enumerate(pal.WARM_RAMP):
    _cscale.append([i / 6, c])
    _cscale.append([min((i + 1) / 6, 1.0), c])

fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.09,
                     row_heights=[0.42, 0.58],
                     subplot_titles=["Aggregate NEWS2 (6 of 7, Scale 1)",
                                     "Per-parameter NEWS2 sub-score"])
fig2.add_trace(go.Scatter(x=t, y=agg, mode="lines", line_shape="hv", showlegend=False,
                          line=dict(color=pal.COMPARATOR, width=2)), row=1, col=1)
fig2.add_hline(y=NEWS2_TRIGGER, line=dict(color=pal.THRESHOLD, width=1, dash="dot"),
               annotation_text=f"aggregate trigger ({NEWS2_TRIGGER})", row=1, col=1)
fig2.add_trace(go.Heatmap(x=t, y=list(NEWS2_PARAM_LABELS), z=sub6, zmin=0, zmax=6,
                          colorscale=_cscale, showscale=True, xgap=0, ygap=1,
                          colorbar=dict(title="pts", tickvals=[0, 1, 2, 3], len=0.5, y=0.24)),
               row=2, col=1)
if cross is not None:
    fig2.add_vline(x=cross, line=dict(color=pal.THRESHOLD, width=1.4, dash="dash"))
    fig2.add_annotation(x=cross, y=NEWS2_RED + 0.4, row=1, col=1, showarrow=True, arrowhead=2,
                        text=f"SpO₂ ≤91 single-param red fires NEWS2 — {cross:.0f} sim-min",
                        font=dict(size=10.5, color=pal.THRESHOLD), xanchor="right", ax=-40, ay=0)
fig2.add_annotation(x=float(t[len(t) // 4]), y=4.2, row=1, col=1, showarrow=False,
                    text=f"aggregate peaks at {int(agg.max())} — never reaches the trigger of "
                         f"{NEWS2_TRIGGER}", font=dict(size=10.5, color=pal.ANNOTATION))
fig2.update_yaxes(title_text="points", range=[0, 7], row=1, col=1)
fig2.update_xaxes(title_text="stay clock (sim-min)", row=2, col=1)
fig2.update_layout(title="§2 — NEWS2 over time: flat aggregate, one late single-param red",
                   height=560, margin=dict(t=70))
fig2.write_html(str(_root / "outputs" / "10_s2_news2_over_time.html"))
fig2

# %% [markdown]
# ### §2 self-check — canonical numbers (fails loudly on drift)

# %%
NEWS2_RED_CROSSING_MIN = 1010.0
assert news2_complete_crossing(p) == news2_crossing(p) == NEWS2_RED_CROSSING_MIN, (
    f"NEWS2 escalation moved off 1010: complete={news2_complete_crossing(p)} "
    f"partial={news2_crossing(p)}"
)
assert int(agg.max()) == 3 < NEWS2_TRIGGER, f"NEWS2 aggregate peak moved off 3: {agg.max()}"
_i = int(np.searchsorted(t, NEWS2_RED_CROSSING_MIN))
assert int(sub6[:, _i].max()) == NEWS2_RED and int(agg[_i]) < NEWS2_TRIGGER, (
    "the 1010 crossing must be single-param-red driven, not aggregate-driven"
)
assert int(sub6[4:].max()) == 0, "nurse-obs params (BP, ACVPU) must stay band-0 in this scenario"
print(f"✓ NEWS2 single-param-red escalation at {NEWS2_RED_CROSSING_MIN:.0f} sim-min "
      f"(complete == partial)")
print(f"✓ aggregate peaks at {int(agg.max())} (< trigger {NEWS2_TRIGGER}) — escalation is the "
      f"SpO₂ red alone")
print("✓ BP + ACVPU stay band-0 → the 6-of-7 comparator escalates only on the single-param red")

# %% [markdown]
# ## §3 — State space: oxygenation × effort
#
# ### Plain
# The same stay, drawn as a **path** rather than a row of numbers. Oxygen runs left
# (worse to the left), breathing effort runs up (worse upward), and the warm shading is
# the NEWS2 points for those two vitals. Watch the path slide down-left toward the
# "silent hypoxia" corner during the very window where NEWS2 (§2) stayed flat — the
# slide a single-reading threshold cannot see, here made visible as a trajectory.
#
# This view shows the **whole journey at once** — all four cascade markers, including the
# forecast (marker 3) and risk-threshold (marker 4) stages that §6–§8 only introduce
# below, plus the ≈5 h lead bracket. Read it as a preview of the cascade; §4–§8 detail
# each stage in turn, and §8 lays the same fires out on a *time* axis.
#
# ### Dev
# This is the **exact builder the Patient view renders** — `styx.viz.trajectory`
# `.clinical_trajectory_figure` (the app's hero; `app/pages/01_patient.py:168`). The
# notebook does not re-embed or rebuild anything: `build_context(cohort, p)` produces
# the same `emb`/`basins`/fire-times the page uses, and the cascade fire-times come from
# the same single sources (`decoupling_onset`, `ctx.fire`, `news2_complete_crossing`).
# `now_idx=None` parks "now" at the late breach so the whole path and all four markers
# show. Output: one `go.Figure`, byte-for-byte the same construction a judge sees in app.
#
# ### Tech — the by-construction caveat (stated plainly, not softened)
# The plotted plane is the literal **SpO₂ × RR** clinical plane. On this cohort the PCA
# embedding **fails its legibility check and falls back to *constructed* axes**
# (`emb.mode == "constructed"`, asserted below): oxygenation is defined *as* SpO₂ and
# effort *as* a function of RR & HR. So the headline "axis fidelity |r| ≈ 1.0" is
# **partly tautological** — the axes correlate with the vitals because they are built
# from them. This is a real limitation, not a result: the state space is legible here
# *by construction*, and a PCA that genuinely separated the axes on richer data is the
# claim we are **not** making. The warm ramp is the ratified NEWS2-points encoding and
# is deliberately *not* recoloured to the brand cool palette.

# %%
from styx.config import AEGIS_BASELINE_SAMPLES, AEGIS_K, AEGIS_SUSTAIN  # noqa: E402
from styx.frame import build_context  # noqa: E402
from styx.reach.decoupling import decoupling_onset  # noqa: E402
from styx.risk.aegis import aegis_axis_departures, aegis_signal  # noqa: E402
from styx.synth.gates import _DROP_K, COHERENCE_WINDOW  # noqa: E402  detector constants, single source
from styx.viz.coherence import coherence_figure  # noqa: E402
from styx.viz.trajectory import clinical_trajectory_figure  # noqa: E402

ctx = build_context(cohort, p)          # the app's once-per-patient fit: emb, basins, fire-times, risk
emb, fire = ctx.emb, ctx.fire
dec = decoupling_onset(p)               # reads the G1 coherence series — never recomputes it
news2_min = news2_complete_crossing(p)  # bound once, shared with the hero (== 1010)
print(f"embedding: mode={emb.mode}  axes={emb.axis_labels}")
print(f"cascade (sim-min): decoupling={dec.onset_min:.0f}  AEGIS={fire.aegis_min:.0f}  "
      f"threshold={fire.threshold_min:.0f}  NEWS2={news2_min:.0f}")

# %%
fig3 = clinical_trajectory_figure(
    p, decoupling_min=dec.onset_min, aegis_min=fire.aegis_min,
    escalation_min=fire.threshold_min, news2_min=news2_min, now_idx=None,
)
fig3.write_html(str(_root / "outputs" / "10_s3_state_space.html"))
print(f"§3 state space: {emb.mode} axes {emb.axis_labels} — same builder as the Patient view hero")
fig3

# %% [markdown]
# ## §4 — Decoupling (cascade stage 1)
#
# ### Plain
# The earliest sign. Normally breathing and oxygen move together — as oxygen dips the
# body breathes a little harder, a tight coupling. Here that coupling **starts to break
# down**: the two signals stop tracking each other, *while both are still inside their
# NEWS2 bands*. Nothing has breached yet; the relationship between the signals is what
# has changed.
#
# ### Dev
# Reuses the decoupling detector via `reach.decoupling.decoupling_onset(p)`, which reads
# the G1 series `synth.gates.windowed_coherence` (`dec.coherence`) and the onset
# `dec.onset_min` — the correlation is **not** recomputed in the notebook. The figure is
# the app's CADUCEUS face `viz.coherence.coherence_figure`, augmented with the detector's
# own decision geometry: the `|r|` series and the baseline / `baseline − _DROP_K`
# threshold lines, using the gate constants `COHERENCE_WINDOW` and `_DROP_K`.
#
# ### Tech
# `windowed_coherence` is the trailing rolling **Pearson r of *detrended* RR vs SpO₂**
# over a `COHERENCE_WINDOW` (= 12 samples / 60 sim-min) window; detrending isolates the
# fast anti-phase co-fluctuation (coupled → `|r| → 1`, decoupled → `|r| → 0`). The
# detector works on `|r|`: onset = the first sample where `|r|` falls `_DROP_K` (= 0.4)
# below its stable baseline (median `|r|` over the first third of the stay) and **stays
# there ≥ `_SUSTAIN` = 2** windows. So the marked threshold is `baseline − 0.4`, not a
# literal −0.4 coherence. Failure modes: short windows make `r` noisy (false onsets);
# a long window smears the onset late; carer-counted RR artefact would corrupt `r`
# directly (a named deployment-readiness item, out of scope here).

# %%
coh_abs = np.abs(dec.coherence)
_stable = coh_abs[COHERENCE_WINDOW - 1 : p.t_min.size // 3]  # detector's pre-onset reference third
_baseline = float(np.nanmedian(_stable))
_thresh = _baseline - _DROP_K

fig4 = coherence_figure(p.t_min, dec.coherence, dec.onset_min, aegis_min=fire.aegis_min)
fig4.add_trace(go.Scatter(x=p.t_min, y=coh_abs, mode="lines", name="|r| (the detected quantity)",
                          line=dict(color=pal.NEUTRAL, width=1, dash="dot"),
                          connectgaps=False, hoverinfo="skip"))
fig4.add_hline(y=_baseline, line=dict(color=pal.STABLE, width=1, dash="dot"),
               annotation_text=f"stable baseline |r| ≈ {_baseline:.2f}",
               annotation_position="bottom left")
fig4.add_hline(y=_thresh, line=dict(color=pal.THRESHOLD, width=1, dash="dash"),
               annotation_text=f"onset threshold = baseline − {_DROP_K:.1f}",
               annotation_position="bottom right")
fig4.write_html(str(_root / "outputs" / "10_s4_decoupling.html"))
print(f"§4 decoupling onset = {dec.onset_min:.0f} sim-min  (|r| drops {_DROP_K:.1f} below baseline "
      f"≈ {_baseline:.2f}, sustained ×2)")
fig4

# %% [markdown]
# ## §5 — AEGIS (cascade stage 2)
#
# ### Plain
# This is the calibrated early warning, and its trick is that it is **personal**. It does
# not ask "is this reading abnormal for people?" — it asks "is this abnormal **for this
# patient**, versus how they looked in their own first few hours?" A patient who quietly
# drifts away from their own steady baseline is flagged even though every number is still
# in a normal population band.
#
# ### Dev
# Reuses the AEGIS detector unchanged: `risk.aegis.aegis_axis_departures(p, emb)` (per
# named-axis σ-departure) and `aegis_signal(p, emb)` (the max-axis signal AEGIS fires on);
# the served fire-time is `ctx.fire.aegis_min`. Nothing is recomputed. New plotting (no
# AEGIS-trace builder exists in `styx/viz`): the per-axis and max-axis departure traces,
# the shaded baseline window, the `AEGIS_K` threshold, and the fire marker.
#
# ### Tech
# The state position is trend-smoothed (a trailing mean, `AEGIS_SMOOTH_SAMPLES`) so a
# fast homeostatic swing does not inflate the baseline σ. The baseline mean/σ are learned
# from the **first `AEGIS_BASELINE_SAMPLES` (= 24) samples / 120 sim-min** — a window
# assumed stable and well before the decoupling onset (sample ~108). The signal is the
# **max over both named axes** of `|(x − μ)/σ|`; AEGIS fires when it exceeds
# `AEGIS_K = 3σ` for `AEGIS_SUSTAIN = 3` consecutive re-scores (rejects single-window
# noise). Assumption/failure mode: if the opening window is *not* stable (early
# instability), the baseline σ inflates and AEGIS fires late or not at all.

# %%
deps = aegis_axis_departures(p, emb)              # dict: axis label -> (N,) σ-departure
sig = aegis_signal(p, emb)                        # max-axis departure — what AEGIS fires on
baseline_end_min = float(p.t_min[AEGIS_BASELINE_SAMPLES])
_axis_colours = (pal.REDDISH_PURPLE, pal.GREY)

fig5 = go.Figure()
fig5.add_vrect(x0=float(p.t_min[0]), x1=baseline_end_min, line_width=0,
               fillcolor=pal.STABLE, opacity=0.12,
               annotation_text=f"baseline window (first {AEGIS_BASELINE_SAMPLES} samples)",
               annotation_position="top left")
for (axis, z), col in zip(deps.items(), _axis_colours):
    fig5.add_trace(go.Scatter(x=p.t_min, y=z, mode="lines", name=f"{axis} departure",
                              line=dict(color=col, width=1.3)))
fig5.add_trace(go.Scatter(x=p.t_min, y=sig, mode="lines", name="departure (max axis)",
                          line=dict(color=pal.RISK, width=2.4)))
fig5.add_hline(y=AEGIS_K, line=dict(color=pal.THRESHOLD, width=1, dash="dash"),
               annotation_text=f"AEGIS threshold ({AEGIS_K:.0f}σ, sustained ×{AEGIS_SUSTAIN})")
fig5.add_vline(x=fire.aegis_min, line=dict(color=pal.EARLY_WARNING, width=2),
               annotation_text=f"AEGIS fires — {fire.aegis_min:.0f} sim-min",
               annotation_position="top right")
fig5.update_layout(title="§5 — AEGIS: departure from the patient's own baseline (σ units)",
                   xaxis_title="stay clock (sim-min)", yaxis_title="baseline departure (σ)",
                   height=380, showlegend=True,
                   legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
fig5.write_html(str(_root / "outputs" / "10_s5_aegis.html"))
print(f"§5 AEGIS fires at {fire.aegis_min:.0f} sim-min (max-axis z > {AEGIS_K:.0f}σ, "
      f"sustained ×{AEGIS_SUSTAIN})")
fig5

# %% [markdown]
# ### §3–§5 self-check — canonical numbers (fails loudly on drift)

# %%
DECOUPLING_ONSET_MIN = 590.0
AEGIS_FIRE_MIN = 705.0
assert dec.onset_min == DECOUPLING_ONSET_MIN, f"decoupling onset moved off 590: {dec.onset_min}"
assert fire.aegis_min == AEGIS_FIRE_MIN, f"AEGIS fire moved off 705: {fire.aegis_min}"
# the §3 by-construction caveat is a fact about the fitted embedding — pin it, not just narrate it
assert emb.mode == "constructed", (
    f"embedding mode changed to {emb.mode!r} — the §3 by-construction caveat assumes constructed axes"
)
print(f"✓ decoupling onset at {DECOUPLING_ONSET_MIN:.0f} sim-min (cascade stage 1)")
print(f"✓ AEGIS fires at {AEGIS_FIRE_MIN:.0f} sim-min (cascade stage 2) — "
      f"{AEGIS_FIRE_MIN - DECOUPLING_ONSET_MIN:.0f} min after onset")
print(f"✓ embedding mode = '{emb.mode}' → §3 by-construction caveat holds")

# %% [markdown]
# ## §6 — Forecast cone
#
# ### Plain
# Don't just watch the risk — **extrapolate it**. STYX fits the recent slope of the risk
# and projects it forward as a cone: a central guess plus an honest band of uncertainty.
# The moment even the *optimistic* (upper) edge of that band would reach the escalation
# line, STYX raises a forecast flag — acting on a credible worst case before it arrives.
#
# ### Dev
# Reuses the forecast builder end-to-end: the projection is `styx.forecast.project(risk,
# t, now_idx, band)` and the figure is `styx.viz.cone.cone_figure`. Inputs are the
# already-computed `ctx.risk` and the cohort conformal `ctx.band` (from `build_context`);
# nothing is re-fit here. The cone is anchored at the forecast fire-time (`fire.forecast_min`)
# so the rendered "now" is the instant the band's upper edge first reaches threshold.
#
# ### Tech
# The projection is a **degree-1 least-squares fit on the trailing `FORECAST_WINDOW` = 12
# samples** (60 sim-min), extended over the horizon. The band half-widths are the
# **(1 − α) = 90th-percentile of absolute residuals, pooled across the cohort** (a single
# marginal `conformal_band`, computed once). Crucial honesty point: the empirical coverage
# (**0.915**, computed live below) is **pooled / marginal** — it holds on average over the
# calibration cohort, and is **not** a per-patient guarantee; an individual cone can under- or
# over-cover. The band is also marginal (not conditional on the current state), so it widens
# uniformly with the horizon rather than adapting to local volatility.

# %%
from styx.forecast import project  # noqa: E402
from styx.viz.cone import cone_figure  # noqa: E402
from styx.viz.waterline import waterline_figure  # noqa: E402

_fi = int(np.searchsorted(p.t_min, fire.forecast_min))  # sample index of the forecast fire-time
cone = project(ctx.risk, p.t_min, _fi, ctx.band)        # reuse the forecast projection (no re-fit)
fig6 = cone_figure(p.t_min, ctx.risk, cone, ctx.threshold, now_idx=_fi)

# mark where the band's upper (optimistic) edge first reaches the threshold
_up = np.flatnonzero(cone.upper >= ctx.threshold)
if _up.size:
    _h = int(_up[0])
    fig6.add_trace(go.Scatter(
        x=[float(cone.t_fore[_h])], y=[float(cone.upper[_h])], mode="markers",
        name="upper edge reaches threshold",
        marker=dict(size=14, symbol="circle-open", color=pal.THRESHOLD, line=dict(width=2.6))))
fig6.add_vline(x=fire.forecast_min, line=dict(color=pal.RISK, width=1, dash="dash"),
               annotation_text=f"forecast fires — {fire.forecast_min:.0f} sim-min",
               annotation_position="top left")
fig6.write_html(str(_root / "outputs" / "10_s6_forecast_cone.html"))
print(f"§6 forecast fires at {fire.forecast_min:.0f} sim-min "
      f"(upper edge of the 90% pooled band reaches threshold {ctx.threshold:.1f})")
fig6

# %% [markdown]
# ### §6 self-check — forecast fire + live conformal coverage
# %%
from analysis import conformal_coverage  # noqa: E402  shared single source (same sweep as nb 05 B)
from styx.cohort import build_cohort_context  # noqa: E402

cctx = build_cohort_context(cohort)  # cohort-wide context — built once here, reused by §10 + §11
_cov = conformal_coverage(cctx)      # empirical cone coverage, swept over all patients/anchors
assert fire.forecast_min == 750.0, f"forecast fire moved off 750: {fire.forecast_min}"
assert round(_cov.mean, 3) == 0.915, f"conformal coverage moved off 0.915: {_cov.mean}"
print(f"✓ forecast fire at 750 sim-min · conformal coverage {_cov.mean:.3f} "
      f"(nominal {_cov.nominal:.2f}) — pooled/marginal, computed live, not per-patient")

# %% [markdown]
# ## §7 — Risk index (cascade stage 3)
#
# ### Plain
# This is STYX's own **"act now" line**. The risk index folds the trajectory into a single
# 0–1 number that rises through the silent window and crosses STYX's escalation line once
# the patient is genuinely breaching. It is **STYX's** threshold — not a NEWS2 trigger, not
# a clinical score — the trajectory index crossing its own absolute-risk line.
#
# ### Dev
# Reuses the risk builder: the series is the already-computed `ctx.risk`
# (`styx.risk.score.risk_series`) and the figure is `styx.viz.waterline.waterline_figure`,
# with the AEGIS flag at `ctx.aegis_idx`. The crossing is the served `fire.threshold_min`
# (`escalation_fire_index`). Nothing is recomputed; the crossing marker is read off the
# series at that fire-time.
#
# ### Tech
# `risk = clip(0.5 · proximity + 0.5 · exceedance, 0, 1)`. **Proximity** (state-space
# nearness to a crisis attractor) caps at 0.5 and rises *early*, through the silent window;
# **exceedance** (per-vital absolute range-overshoot) is **exactly 0 while every vital is
# in range** and only turns on at a breach. So the weighted sum can exceed the 0.5
# threshold *only once exceedance is non-zero* — i.e. the index crosses 0.5 only at an
# actual range breach, never on proximity alone. That is why it "rises early, crosses late."

# %%
fig7 = waterline_figure(p.t_min, ctx.risk, ctx.threshold, aegis_idx=ctx.aegis_idx)
_ti = int(np.searchsorted(p.t_min, fire.threshold_min))
fig7.add_trace(go.Scatter(
    x=[fire.threshold_min], y=[float(ctx.risk[_ti])], mode="markers", name="risk crosses threshold",
    marker=dict(size=15, symbol="x", color=pal.RISK, line=dict(color="white", width=1.4))))
fig7.add_annotation(x=fire.threshold_min, y=ctx.threshold + 0.07, showarrow=True, arrowhead=2,
                    ax=-30, ay=0, xanchor="right",
                    text=f"STYX escalation — risk crosses {ctx.threshold:.1f} at "
                         f"{fire.threshold_min:.0f} sim-min", font=dict(size=10.5, color=pal.RISK))
fig7.write_html(str(_root / "outputs" / "10_s7_risk_index.html"))
print(f"§7 risk index crosses its {ctx.threshold:.1f} escalation threshold at "
      f"{fire.threshold_min:.0f} sim-min")
fig7

# %% [markdown]
# ### §7 self-check
# %%
assert fire.threshold_min == 915.0, f"risk-threshold crossing moved off 915: {fire.threshold_min}"
print("✓ risk-threshold crossing at 915 sim-min (STYX escalation line, not a NEWS2 trigger)")

# %% [markdown]
# ## §8 — Assembled cascade (the temporal view)
#
# ### Plain
# §3 showed *where* the patient went; this shows *when* each stage fired, on a clock. Left
# to right: the coupling breaks down (decoupling), STYX's early warning fires (AEGIS), the
# forecast confirms, the risk index crosses STYX's line, and — last of all — NEWS2 finally
# reds. **On this clearest case, STYX's early warning fired about five hours (305 min)
# before NEWS2's red.** That gap is the whole point.
#
# ### Dev
# A complementary *temporal* view to §3's *spatial* one — same fires, different axis (time,
# not state). All times are read from objects already built: `dec.onset_min`,
# `fire.aegis_min` / `.forecast_min` / `.threshold_min`, `dec.breach_min`, and `news2_min`.
# New plotting: the app's `viz.timeline.timeline_figure` is a gantt of AEGIS / forecast /
# ETA-band / threshold / NEWS2 and carries **neither** the decoupling onset (590) **nor**
# the single-signal range excursion (790), so §8 uses a purpose-built linear timeline to
# carry the full five-stage sequence and the two-breach distinction below.
#
# ### Tech — the two meanings of "breach" (the subtle honesty point)
# "Breach" names **two different events**, and they must not be conflated:
# 1. **Single-signal range excursion (790)** — the first sim-min a *vital leaves its NEWS2
#    range* (`gates.breach_index` → `dec.breach_min`). The **decoupling→single-signal lead
#    of 200** (590 → 790, `dec.g1_lead_min`) is measured to *this*.
# 2. **F4 absolute-risk threshold (915)** — the first sim-min the *risk index crosses 0.5*
#    (`escalation_fire_index` → `fire.threshold_min`). The **AEGIS→threshold lead of 210**
#    (705 → 915, `fire.aegis_threshold_lead_min`) is measured to *this*.
# The headline AEGIS→NEWS2 lead of 305 (705 → 1010) is measured to the NEWS2 red, a third,
# later event again. Same word, three distinct clocks.

# %%
_LANE_STYX, _LANE_BREACH = 2.0, 1.0
_styx_stages = [
    (dec.onset_min, "1 · decoupling", pal.NEUTRAL, "triangle-up", "top center"),
    (fire.aegis_min, "2 · early warning", pal.EARLY_WARNING, "diamond", "bottom center"),
    (fire.forecast_min, "3a · forecast", pal.RISK, "diamond", "top center"),
    (fire.threshold_min, "3 · risk threshold (F4)", pal.RISK, "x", "top center"),
]
_breach_row = [
    (dec.breach_min, "single-signal range excursion", pal.ANNOTATION, "line-ns-open", "bottom center"),
    (news2_min, "NEWS2 single-param red", pal.THRESHOLD, "diamond", "bottom center"),
]

fig8 = go.Figure()
for x, label, col, sym, pos in _styx_stages:
    fig8.add_vline(x=x, line=dict(color="#DADADA", width=1))
    fig8.add_trace(go.Scatter(
        x=[x], y=[_LANE_STYX], mode="markers+text", text=[f"{label}<br>{x:.0f}"], textposition=pos,
        textfont=dict(size=10), marker=dict(size=14, symbol=sym, color=col,
                                            line=dict(color="white", width=1.4)), showlegend=False))
for x, label, col, sym, pos in _breach_row:
    fig8.add_vline(x=x, line=dict(color="#EDEDED", width=1))
    fig8.add_trace(go.Scatter(
        x=[x], y=[_LANE_BREACH], mode="markers+text", text=[f"{label}<br>{x:.0f}"], textposition=pos,
        textfont=dict(size=10), marker=dict(size=13, symbol=sym, color=col,
                                            line=dict(color="white", width=1.6)), showlegend=False))

# the headline lead bracket — AEGIS → NEWS2 (≈ 5 h), drawn above the cascade lane
_lead_news2 = news2_min - fire.aegis_min
fig8.add_shape(type="line", x0=fire.aegis_min, x1=news2_min, y0=2.7, y1=2.7,
               line=dict(color=pal.RISK, width=2))
fig8.add_annotation(x=(fire.aegis_min + news2_min) / 2, y=2.92, showarrow=False,
                    text=f"AEGIS → NEWS2 lead = {_lead_news2:.0f} min ≈ {_lead_news2 / 60:.0f} h",
                    font=dict(size=12, color=pal.RISK))
# the two component leads, on their correct breach meanings
fig8.add_annotation(x=(dec.onset_min + dec.breach_min) / 2, y=0.45, showarrow=False,
                    text=f"decoupling → single-signal breach = {dec.breach_min - dec.onset_min:.0f}",
                    font=dict(size=9.5, color=pal.ANNOTATION))
fig8.add_annotation(x=(fire.aegis_min + fire.threshold_min) / 2, y=1.55, showarrow=False,
                    text=f"AEGIS → threshold = {fire.threshold_min - fire.aegis_min:.0f}",
                    font=dict(size=9.5, color=pal.RISK))
fig8.update_layout(
    title="§8 — Assembled cascade (temporal view): when each stage fires",
    xaxis=dict(title="stay clock (sim-min)", range=[540, 1060]),
    yaxis=dict(range=[0.2, 3.2], tickvals=[_LANE_BREACH, _LANE_STYX],
               ticktext=["range excursion /<br>NEWS2 comparator", "STYX cascade"]),
    height=420, showlegend=False, plot_bgcolor="white")
fig8.write_html(str(_root / "outputs" / "10_s8_cascade_timeline.html"))
print(f"§8 cascade (sim-min): decoupling {dec.onset_min:.0f} → AEGIS {fire.aegis_min:.0f} → "
      f"forecast {fire.forecast_min:.0f} → risk-threshold {fire.threshold_min:.0f} → "
      f"NEWS2 {news2_min:.0f}")
fig8

# %% [markdown]
# ### §8 self-check — leads and breaches (fails loudly on drift)
# %%
assert news2_min == 1010.0, f"NEWS2 red moved off 1010: {news2_min}"
assert dec.breach_min == 790.0, f"single-signal breach moved off 790: {dec.breach_min}"
assert news2_min - fire.aegis_min == 305.0, "AEGIS→NEWS2 lead moved off 305"
assert fire.threshold_min - fire.aegis_min == 210.0, "AEGIS→threshold lead moved off 210"
assert fire.aegis_threshold_lead_min == 210.0, "AEGIS→threshold lead (property) moved off 210"
assert dec.breach_min - dec.onset_min == 200.0, "decoupling→single-signal lead moved off 200"
assert dec.g1_lead_min == 200.0, "decoupling→single-signal lead (detector) moved off 200"
print("✓ NEWS2 red 1010 · single-signal breach 790")
print("✓ leads — AEGIS→NEWS2 305 (≈5 h) · AEGIS→threshold 210 · decoupling→single-signal 200")
print("✓ two-breach distinction holds: 790 (range excursion) ≠ 915 (F4 risk threshold)")

# %% [markdown]
# ## §9 — CALLIOPE: why this patient
#
# ### Plain
# A flag a clinician can't interrogate is a flag they can't trust. CALLIOPE turns the
# risk score into **plain reasons**: it names, in words, the factors actually driving the
# number — here, falling oxygenation approaching the silent-hypoxia mode, with the
# early-warning context (how far the patient has drifted from their own baseline, and that
# breathing and oxygen have decoupled). One sentence, every word backed by the model.
#
# **And where it is wrong, we say so.** Checked against the textbook driver for each
# deterioration pattern, the named reason is right for **silent-hypoxia and coupled patients
# in every window**, but **wrong for the compensated pattern in every window** (0 of 13): there
# it names *oxygenation* when the textbook driver is *effort*. We surface that split rather
# than average it into a single reassuring score.
#
# ### Dev
# Reuses CALLIOPE unchanged: `styx.rationale.explain(patient, emb, basins, idx)` returns a
# `Rationale` with the `headline` (the rendered sentence), the additive `top_k` risk terms
# (the waterfall), and the `context` lines. Plain component labels come from
# `styx.explain.DISPLAY_NAMES` (`"calliope" → "Why this score"`). The attribution is **not**
# rebuilt here. Faithfulness reuses gate G4's **archetype oracle** (`_SIGNATURE` imported from
# `tests/test_g4.py`, single-sourced) over **every** pre-breach re-score window — a finer,
# per-sample sweep than `test_g4`'s cadence grid (which skips the fast-breaching compensated case).
#
# ### Tech
# The headline is a **strict template** over the model's real **top-3 additive risk terms**
# (`0.5·oxygenation-proximity`, `0.5·effort-proximity`, `0.5·worst-vital-exceedance`),
# regime-aware (post-breach the proximity clips, `additive` flips False and the contributor
# panel is suppressed). **What this metric measures.** CALLIOPE names the *model's* own top
# term — so it is faithful to the model **by construction** (exactly-additive split, no tie).
# The G4 "faithfulness" sweep tests something stricter: does that model-chosen top-1 match the
# **generating archetype's** true driver (`_SIGNATURE`)? It is a check on the *model's risk
# decomposition*, surfaced through CALLIOPE — not on CALLIOPE's narration of the model.
#
# **Result: 395 / 408 = 0.968** — silent-hypoxia 159/159, coupled 236/236, **compensated 0/13**.
# The 0/13 is systematic, not a tie: on compensated patients the decomposition is
# *oxygenation-led* (oxygenation-proximity ≈ 0.10) while effort-proximity sits at ≈ −0.001, so
# top-1 is never effort. Why: compensated breaches fast, so its *only* evaluable pre-breach
# windows are the earliest ones where risk has just cleared 0.1 — there the constructed effort
# axis has not yet separated, and the baseline oxygenation term dominates. So the gap is a
# **model construct-validity limit on one fast-breaching archetype**, flagged (not closed) here.
#
# **Basis — stated plainly.** This is a **per-sample** sweep (every index), a *deliberately finer
# basis than gate G4 uses*: `test_g4` sweeps the **cadence grid** and on the current cohort reads
# **115/115 = 1.000** — because compensated has *no* cadence-grid window at all, the gate's basis
# *hides* the one archetype that fails. The per-sample basis is reported here precisely because it
# does not. (Re-baseline: the previously-logged **137/138 = 0.993** is the pre-S7 cohort; the S7
# stream diversification moved both the window counts and the basis. `STYX_METHODOLOGY.md §6.4`
# is updated to match this figure and basis.)

# %%
from styx.explain import DISPLAY_NAMES  # noqa: E402
from styx.rationale import explain  # noqa: E402
from styx.risk import risk_series  # noqa: E402
from styx.synth import Archetype, Outcome  # noqa: E402
from styx.synth.gates import breach_index  # noqa: E402
from tests.test_g4 import _SIGNATURE  # noqa: E402  ground-truth driver per archetype — single source

# top-1 faithfulness over EVERY pre-breach re-score window (per-sample), using gate G4's archetype
# oracle — tracked PER ARCHETYPE, because the mean hides the story (the split is the headline).
_by_arch: dict[str, list[int]] = {}  # archetype.value -> [agree, total]
for _q in cohort.patients:
    if _q.archetype is Archetype.STABLE:
        continue
    _brk = breach_index(_q) or _q.t_min.size
    _risk = risk_series(_q, ctx.emb, ctx.basins)
    _slot = _by_arch.setdefault(_q.archetype.value, [0, 0])
    for _idx in range(_q.t_min.size):
        if _idx >= _brk or _risk[_idx] < 0.1:  # pre-breach, attribution meaningful
            continue
        _slot[1] += 1
        _slot[0] += int(explain(_q, ctx.emb, ctx.basins, _idx).top_k[0][0] in _SIGNATURE[_q.archetype])
_agree = sum(a for a, _ in _by_arch.values())
_total = sum(t for _, t in _by_arch.values())
faithfulness = _agree / _total
_split = " · ".join(f"{k} {a}/{t}" for k, (a, t) in sorted(_by_arch.items()))

# the index patient's rationale at the silent-window frame (the app's headline + contributors)
r = explain(p, ctx.emb, ctx.basins, ctx.default_idx)
_labels = [term for term, _ in r.top_k]
_vals = [val for _, val in r.top_k]

fig9 = go.Figure(go.Waterfall(
    orientation="v", measure=["relative"] * len(_vals) + ["total"],
    x=_labels + ["risk (sum)"], y=_vals + [0.0],
    text=[f"{v:+.3f}" for v in _vals] + [f"{sum(_vals):.3f}"], textposition="outside",
    connector=dict(line=dict(color=pal.NEUTRAL)),
    increasing=dict(marker=dict(color=pal.RISK)), decreasing=dict(marker=dict(color=pal.STABLE)),
    totals=dict(marker=dict(color=pal.ANNOTATION))))
fig9.add_annotation(xref="paper", yref="paper", x=0.0, y=1.13, showarrow=False, xanchor="left",
                    align="left", font=dict(size=12, color=pal.ANNOTATION),
                    text=f"<b>{r.headline}</b>")
_ctx_line = ("early-warning context — " + " · ".join(r.context)) if r.context else ""
fig9.add_annotation(xref="paper", yref="paper", x=0.0, y=-0.22, showarrow=False, xanchor="left",
                    align="left", font=dict(size=10, color="#444444"),
                    text=f"{_ctx_line}<br>top-1 faithfulness vs archetype oracle "
                         f"{_agree}/{_total} = {faithfulness:.3f}  ({_split}) — wrong on every "
                         f"compensated window, surfaced not averaged")
fig9.update_layout(title=f"§9 — {DISPLAY_NAMES['calliope']}: additive attribution (index patient)",
                   yaxis_title="risk contribution", height=460, showlegend=False,
                   margin=dict(t=90, b=140))
fig9.write_html(str(_root / "outputs" / "10_s9_calliope.html"))
print(f"§9 CALLIOPE headline: {r.headline}")
print(f"§9 top-1 faithfulness = {_agree}/{_total} = {faithfulness:.3f}  ({_split})")
fig9

# %% [markdown]
# ### §9 self-check
# %%
# assert the PER-ARCHETYPE split — the mean alone would hide the compensated failure
assert _by_arch["silent_hypoxia"] == [159, 159], f"silent_hypoxia split moved: {_by_arch}"
assert _by_arch["coupled"] == [236, 236], f"coupled split moved: {_by_arch}"
assert _by_arch["compensated"] == [0, 13], f"compensated split moved: {_by_arch}"
assert (_agree, _total) == (395, 408), f"faithfulness sweep moved off 395/408: {_agree}/{_total}"
assert round(faithfulness, 3) == 0.968, f"faithfulness moved off 0.968: {faithfulness}"
print("✓ CALLIOPE top-1 faithfulness 395/408 = 0.968 — silent_hypoxia 159/159 · coupled 236/236 · "
      "compensated 0/13 (faithful on two archetypes, wrong on every compensated window — a model "
      "construct-validity gap, surfaced not averaged)")

# %% [markdown]
# ## §10 — Cohort view (operational)
#
# ### Plain
# Across all 50 synthetic patients, STYX's early-signal **watchlist** is the set flagged as
# *silently rising* — the early warning has fired but the risk line hasn't been crossed yet,
# the "review first" list. Below: how many are on it, when each patient's early warning fired,
# and how the watchlist lines up with who actually deteriorated.
#
# ### Dev
# Reuses the **same classifier the ward board uses** — `styx.cohort.ward_frame(cctx, idx)` and
# the `WardRow.silent_but_rising` flag (`build_cohort_context`), the single source behind
# `app/pages/02_ward.py`. So the watchlist count here **matches the app**. AUC deliberately
# lives in §11, not here. New plotting: the fire-time strip (no cohort-strip builder exists).
#
# ### Tech
# `silent_but_rising` = AEGIS fired by the frame **and** risk still below the escalation
# threshold. Precision = caught / watchlist; recall = caught / escalators, at the silent-window
# frame. **Read precision as construct validity, not performance:** on synthetic data scored
# in-sample a precision of **1.0 is too-perfect** — the generator scripted who escalates and the
# detector recovers it. It is stated here, where it appears, not buried in a footnote.

# %%
from styx.cohort import ward_frame  # noqa: E402

# cctx (the ward's cohort fit, single source w/ 02_ward.py) was built once in §6 — reuse it
_di = cctx.default_idx
_rows = ward_frame(cctx, _di)
watch = [row for row in _rows if row.silent_but_rising]
_esc = {q.pid for q in cohort.patients if q.outcome is Outcome.ESCALATED}
_caught = {row.pid for row in watch} & _esc
_precision = len(_caught) / len(watch)
_recall = len(_caught) / len(_esc)

# fire-time strip — when each patient's AEGIS early warning fired, split by outcome
_esc_t, _rec_t = [], []
for q in cohort.patients:
    _ai = cctx.aegis_idx[q.pid]
    if _ai is None:
        continue
    (_esc_t if q.outcome is Outcome.ESCALATED else _rec_t).append(float(cctx.t_min[_ai]))


def _jitter(n: int) -> np.ndarray:  # deterministic spread (no RNG — DET-1)
    return (np.arange(n) % 5 - 2) * 0.05


fig10 = go.Figure()
fig10.add_trace(go.Scatter(x=_esc_t, y=1 + _jitter(len(_esc_t)), mode="markers", name="escalated",
                           marker=dict(size=9, color=pal.THRESHOLD, line=dict(color="white", width=1))))
fig10.add_trace(go.Scatter(x=_rec_t, y=0 + _jitter(len(_rec_t)), mode="markers", name="recovered",
                           marker=dict(size=9, color=pal.STABLE, line=dict(color="white", width=1))))
fig10.add_annotation(xref="paper", yref="paper", x=0.0, y=1.16, showarrow=False, xanchor="left",
                     align="left", font=dict(size=11, color=pal.ANNOTATION),
                     text=f"watchlist (silent-but-rising) = {len(watch)} · precision {_precision:.2f} "
                          f"· recall {_recall:.2f}  — precision 1.0 is a too-perfect in-sample/"
                          f"synthetic figure (construct validity, not ward performance)")
fig10.update_layout(title="§10 — Cohort: AEGIS early-warning fire times, by outcome",
                    xaxis_title="AEGIS fire (sim-min)",
                    yaxis=dict(tickvals=[0, 1], ticktext=["recovered", "escalated"], range=[-0.5, 1.6]),
                    height=320, showlegend=False, margin=dict(t=80))
fig10.write_html(str(_root / "outputs" / "10_s10_cohort.html"))
print(f"§10 watchlist={len(watch)} · escalators={len(_esc)} · caught={len(_caught)} · "
      f"precision={_precision:.2f} · recall={_recall:.2f}")
fig10

# %% [markdown]
# ### §10 self-check
# %%
assert len(watch) == 19, f"early-signal watchlist moved off 19: {len(watch)}"
print("✓ early-signal watchlist = 19 (matches the ward board's silent_but_rising count)")

# %% [markdown]
# ## §11 — Saturation: what these numbers are and are not  (the keystone honesty cell)
#
# ### Plain
# Here is the number that keeps the whole project honest. If you try to predict who
# deteriorates from a tiny telemetry panel, you score a **perfect AUC of 1.000** on this
# data — and that is **not a success, it is an artifact**. The patients were *generated* from
# a known process, so a detector that reads their telemetry recovers the answer perfectly
# *because we wrote the answer in*. Adding STYX's trajectory features on top of plain history
# changes the score by **−0.016** — essentially nothing. So STYX makes **no claim to predict
# better**; its trajectory machinery is offered as *descriptive context*, not predictive lift.
#
# ### Dev
# Reuses the **exact** computation behind notebook 06's saturation figures — lifted into the
# shared `saturation_analysis.saturation_aucs(cohort, cctx)` that *both* 06 and this cell
# import (06 was refactored to call it; it still reproduces the same numbers). No parallel
# computation here. Returns history / telemetry / combined AUCs and the marginal. New plotting:
# the three-bar AUC chart + the marginal call-out.
#
# ### Tech — construct artifact, not performance
# All AUCs are **in-sample logistic regression on one synthetic cohort**. Telemetry-only
# **1.000** is a **construct artifact**: by the silent-window frame the scripted escalators'
# risk has already separated, so the snapshot encodes the outcome — saturation, not skill.
# The **marginal of combined over telemetry is −0.016** (slightly *negative* — adding history
# can't help and the extra parameter mildly overfits), which is precisely why STYX's reaches
# are framed as **descriptive, not predictive lift**. Honest conclusion: **on synthetic data we
# cannot demonstrate that the trajectory machinery adds predictive value** — that is a real-data
# question, the planned subject of notebooks 11–12.

# %%
from analysis import saturation_aucs  # noqa: E402  shared single source w/ notebook 06

sat = saturation_aucs(cohort, cctx)  # reuse the ward cohort context built in §10
fig11 = go.Figure()
fig11.add_trace(go.Bar(
    x=["history-only", "telemetry-only", "combined"],
    y=[sat.history, sat.telemetry, sat.combined],
    marker_color=[pal.STABLE, pal.THRESHOLD, pal.RISK],
    text=[f"{sat.history:.3f}", f"{sat.telemetry:.3f}<br>(construct<br>artifact)",
          f"{sat.combined:.3f}"], textposition="outside"))
fig11.add_hline(y=0.5, line=dict(color=pal.NEUTRAL, width=1, dash="dot"),
                annotation_text="chance (0.5)", annotation_position="bottom right")
fig11.add_annotation(xref="paper", yref="paper", x=0.5, y=1.16, showarrow=False,
                     font=dict(size=12, color=pal.ANNOTATION),
                     text=f"marginal of trajectory/telemetry over history = "
                          f"{sat.marginal:+.3f}  →  no predictive lift (descriptive only)")
fig11.update_layout(title="§11 — Saturation: in-sample AUC (ESCALATED) — construct validity, "
                          "not performance",
                    yaxis=dict(title="in-sample AUC", range=[0, 1.12]),
                    height=420, showlegend=False, margin=dict(t=90))
fig11.write_html(str(_root / "outputs" / "10_s11_saturation.html"))
print(f"§11 saturation — history {sat.history:.3f} · telemetry {sat.telemetry:.3f} · "
      f"combined {sat.combined:.3f} · marginal {sat.marginal:+.3f}")
fig11

# %% [markdown]
# ### §11 self-check
# %%
_sat_tuple = (round(sat.history, 3), round(sat.telemetry, 3), round(sat.combined, 3),
              round(sat.marginal, 3))
assert _sat_tuple == (0.765, 1.000, 0.984, -0.016), f"saturation tuple moved: {_sat_tuple}"
print("✓ saturation (history 0.765 / telemetry 1.000 / combined 0.984 / marginal −0.016)")
print("✓ telemetry 1.000 is a CONSTRUCT ARTIFACT; marginal −0.016 → descriptive, no predictive lift")

# %% [markdown]
# ## §12 — Limits & "no alert ≠ safe"  (close)
#
# ### Plain
# What this notebook is, and is not. Everything here is a **replay of synthetic patients** —
# no real patient data, no live monitoring. The numbers describe how the method *behaves* on
# data built to a known recipe; they are **not** evidence of ward performance, and STYX makes
# **no claim to predict deterioration better** than existing tools. STYX **supports** a
# clinician's prioritisation — it never replaces clinical judgement, and it is **not a medical
# device**. And the rule that matters most at the bedside: **"no alert" means review as normal,
# never "safe."**
#
# ### Dev
# The rails, restated as the scope every figure above inherits: synthetic replay (seed 42);
# in-sample / construct validity, **not** ward performance; a **single condition** (acute
# respiratory infection) scored against **NEWS2 Scale 1 only** (the shading is wrong for a
# Scale-2 / COPD patient — §0); **no predictive-lift claim** (§11); STYX reads four wearable
# vitals (RR, SpO₂, HR, temp) and a history proxy — nothing else. Every honesty assertion in
# §0–§11 fails loudly if a canonical number drifts.
#
# ### Tech — the real-data path
# The open question §11 makes explicit — *does the trajectory machinery add predictive value
# on real data?* — cannot be answered in-sample on synthetic patients. It is the planned subject
# of **notebooks 11–12** (the real-data validation path): out-of-sample evaluation, calibration
# against observed outcomes, and conditional (not just marginal) conformal coverage. Until then,
# STYX's reaches stand as **descriptive context with an honest early-warning lead**, no more.

# %%
print("§0–§12 complete — mechanism walkthrough rendered; every canonical-number self-check passed.")
print("Reuse-only over styx/: synthetic replay, in-sample, no performance claim (see §11, §12).")
