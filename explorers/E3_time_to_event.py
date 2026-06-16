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
# # E3 — Time-to-event: "when, not whether"
#
# An **explorer** (see `docs/STYX_explorer_notebooks.md` §E3): reframe STYX's readout from a
# binary risk flag to a **calibrated time-to-escalation** estimate — *"likely to cross in ~Xh
# (Y–Z)"* — and decide whether that should become the headline readout.
#
# It is a **thin client over `styx/`** (LYR-1): the cohort, the survival table, the forecast-cone
# ETA, and the Cox model are the package's own; this notebook reuses them and reimplements no
# scoring or survival logic. **Read-only over the untouched seed-42 cohort** — no `styx/`,
# `synth`, or cascade changes, and the determinism digest is never re-baselined.
#
# Built **phased**. §0 is implemented now; §1–§6 are stubbed headers, filled in later phases. The
# notebook is designed to restart-run-all clean at every phase.

# %% [markdown]
# ## §0 — Setup & honesty preamble
#
# ### Plain
# Everything here runs on **synthetic patients** that we replay — **no real patient data**, no
# live deployment. The point of this explorer is to ask a *design* question: would a clinician be
# better served by a calibrated **time** estimate ("likely to cross in about 3–4 hours") than by a
# yes/no flag? The numbers describe how the method *behaves* on data built to a known recipe — they
# are **not** evidence of ward performance, and nothing here claims STYX predicts deterioration
# better than existing tools.
#
# **The rails this explorer holds** (the honesty spine, true of every figure below):
# - synthetic data is **method, not performance**;
# - everything is **in-sample / construct validity**, not held-out ward performance;
# - a **single condition** (acute respiratory infection), scored against **NEWS2 Scale 1** only;
# - **no predictive-lift claim** — the time reframe re-expresses the *same* scored trajectory;
# - **"no alert" ≠ safe** — absence of a flag means review as normal, never reassurance;
# - STYX **supports**, does not replace, the clinician; it is **not a medical device**;
# - **per-archetype behaviour is surfaced, never averaged away** — a subgroup that calibrates
#   badly is reported as such, not hidden in a cohort mean.
#
# **Explorer honesty hierarchy — what synth can settle here.** E3 is the most self-contained of the
# four explorers: **synth CAN answer this question.** Every synthetic patient already carries an
# escalation time (or is right-censored at stay end), so survival analysis is *legitimate* on this
# data — the reframe is the **same scored trajectory expressed as time**, not a new predictive
# claim. The only caveat is the usual in-sample one (a real-data study is still the arbiter of
# whether the calibration transfers).
#
# ### Dev
# We load the canonical cohort once with `build_cohort(seed=42)` and pin two invariants before
# anything else runs: (1) **DET-1** — building twice at the same seed is bit-identical
# (`Cohort.equals`); (2) the **pipeline digest** — a SHA-256 over every patient's vitals streams,
# Theograph counts and risk waterline — matches the recorded baseline. The digest helper is the
# existing single source `tests.test_baseline.pipeline_digest` (reused, not deepened). Because the
# file lives in `explorers/`, §0 puts the **repo root on `sys.path`** so the cross-directory
# imports resolve when the kernel cwd is `explorers/` (`styx` is editable; `tests` and — in later
# phases — `notebooks.analysis` resolve as namespace packages off the repo root). Figures are
# written to `<repo_root>/outputs/E3_*.html` via an absolute path.
#
# ### Tech
# `pipeline_digest` traverses `cohort.patients` (an ordered tuple) in pid order, hashing the vital
# streams, Theograph counts (sorted-key), and the per-patient risk series — the regression
# sentinel. If any modelling change moved the streams/events/scores the assertion below would fire;
# that is the intended tripwire, not a number to edit here. The survival **event** used from §1 on
# is the risk waterline crossing its escalation threshold (`reach.history._crossing_min`: first
# sample `risk ≥ threshold` → event=1, else right-censored at episode end → event=0) — defined
# precisely in §1; §0 only reports the scripted-outcome escalator count as the hook.
#
# **Three-register convention** — every numbered section (§1–§6) carries three labelled markdown
# blocks before its code:
# - **Plain** — for clinicians/stakeholders; no maths.
# - **Dev** — for engineers; inputs/outputs, shapes, where it lives in `styx/`.
# - **Tech** — for data scientists; the maths, parameters, assumptions, failure modes.

# %%
import sys
from pathlib import Path

# Repo-root bootstrap so the cross-dir single sources import when the kernel cwd is `explorers/`
# (no root conftest; `tests` / `notebooks` are not declared packages — resolved as namespace pkgs).
_root = next(d for d in [Path.cwd(), *Path.cwd().parents] if (d / "pyproject.toml").is_file())
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from styx.config import SEED  # noqa: E402
from styx.synth import Outcome, build_cohort  # noqa: E402
from tests.test_baseline import pipeline_digest  # noqa: E402  reuse the existing digest oracle

# Pinned regression sentinel — must reproduce exactly (tests/test_observations.py:30).
CANONICAL_DIGEST = "c9380e9cf7c134a82f2a45dd15c9769129540eee3c7d5db5aa54dc587860b1d9"

cohort = build_cohort(seed=SEED)
assert cohort.equals(build_cohort(seed=SEED)), "DET-1: seed 42 ×2 must be bit-identical"

digest = pipeline_digest(cohort)
assert digest == CANONICAL_DIGEST, f"DIGEST MOVED — a read leaked into core: {digest}"

n = len(cohort.patients)
n_esc = sum(1 for q in cohort.patients if q.outcome is Outcome.ESCALATED)
print(f"seed={SEED}  digest={digest[:8]}…{digest[-7:]}  (matches recorded baseline)")
print(f"cohort n={n}  ·  escalators (scripted outcome) = {n_esc}  ·  recovered = {n - n_esc}")
print("every patient carries a survival row in §1: escalation time (event=1) or right-censored "
      "at stay end (event=0)")
print("framing: synthetic replay · in-sample · time reframe of the same trajectory, no new claim")

# %% [markdown]
# ## §1 — Reframe the target: time-to-escalation
#
# ### Plain
# Instead of a yes/no flag, ask **when**: how long until this patient escalates? On synthetic data
# every patient has an answer — the 21 escalators reach an escalation event at a known time; the 29
# who recover never do, so they are **right-censored** (we only know they hadn't escalated by the end
# of the stay). Plotting survival curves by deterioration pattern shows the *shape* of the wait —
# and the compensated pattern is kept as its **own** group, not blended into a cohort average.
#
# ### Dev
# Builds the `CohortContext` **once** (`build_cohort_context(cohort)`) and reuses it across the whole
# notebook (the NB1 shared-`cctx` pattern). Durations/events come from
# `styx.reach.history.survival_table(cctx)` (right-censored rows: `pid, duration_min, event,
# density`) — not reinvented. KM-by-archetype is fit with the same estimator `stratify` uses
# internally (`lifelines.KaplanMeierFitter`) over those reused rows, grouped by `archetype` rather
# than by history density. New plotting only: the archetype step-curves (no archetype-KM builder
# exists; `stratify`/`hazard_figure` stratify by density).
#
# ### Tech — the event clock, named (the load-bearing definition)
# `survival_table` keys the event off `reach.history._crossing_min`: the first sample where the
# **F4 risk waterline reaches its escalation threshold** (`risk ≥ cctx.threshold = 0.5`) → event=1,
# else right-censored at episode end → event=0. So the "escalation time" here is the **F4
# absolute-risk threshold crossing**, measured **per-sample**: pid 0 = **910 sim-min** (pinned
# below). That is the per-sample form of the served-cadence cascade number **915** (the cadence grid
# lands one 15-min step later) — *same clock, finer grid* — and it is distinct from the other two
# breach clocks (single-signal range excursion 790, NEWS2-red 1010).
#
# **⚠ This clock is STYX-INTERNAL.** F4 is *STYX's own* escalation line ("STYX's escalation line, not
# a NEWS2 trigger" — NB1 §7), not an independent clinical event. A clinically-meaningful
# "time to escalation" — the event a clinician actually wants predicted — is the **NEWS2-red
# crossing (1010)**, the standard-of-care escalation trigger (and the very event the ≈5 h lead pitch
# measures to). Calibrating the F4-derived ETA (§2) against F4-derived events (§1) in §4 would
# validate STYX **against its own line** — internally consistent but circular as a clinical claim.
# **This is a stop-and-decide for §3** (re-key the survival/calibration target to NEWS2-red 1010?):
# the whole notebook through §5's card inherits the answer, so it is named here, not assumed. §1/§2
# are built on the current F4 clock (the spec'd reuse + the ward's actual surface); the re-target
# question is reported below for resolution before any survival model is fit in §3.

# %%
import numpy as np  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
from lifelines import KaplanMeierFitter  # noqa: E402

from styx.cohort import build_cohort_context  # noqa: E402
from styx.reach.history import survival_table  # noqa: E402
from styx.viz import palette as pal  # noqa: E402

cctx = build_cohort_context(cohort)  # built ONCE here — reused by §2 and every later section
st = survival_table(cctx)            # right-censored rows: pid, duration_min, event, density
st["arch"] = st["pid"].map({q.pid: q.archetype.value for q in cohort.patients})

# pin the event clock: pid 0's survival event == the F4 risk-threshold crossing, per-sample (910)
F4_EVENT_PID0_MIN = 910.0
_p0 = st[st.pid == 0].iloc[0]
assert float(_p0.duration_min) == F4_EVENT_PID0_MIN and int(_p0.event) == 1, (
    f"event clock drifted: pid0 duration={_p0.duration_min} event={_p0.event} (expected 910/1)"
)
n_event, n_cens = int(st.event.sum()), int((st.event == 0).sum())
assert (n_event, n_cens) == (21, 29), f"escalators/censored moved off 21/29: {n_event}/{n_cens}"

# KM by archetype — compensated as its OWN stratum (never folded into a cohort curve)
_ARCH_COL = {"silent_hypoxia": pal.RISK, "coupled": pal.EARLY_WARNING, "compensated": pal.THRESHOLD}
fig1 = go.Figure()
_median_event = {}
for a, col in _ARCH_COL.items():
    sub = st[st.arch == a]
    km = KaplanMeierFitter().fit(sub.duration_min, sub.event)
    sf = km.survival_function_
    fig1.add_trace(go.Scatter(x=sf.index.to_numpy(dtype=float), y=sf.iloc[:, 0].to_numpy(dtype=float),
                              mode="lines", line_shape="hv", name=f"{a} (n={len(sub)})",
                              line=dict(color=col, width=2)))
    _median_event[a] = float(np.median(sub[sub.event == 1].duration_min))
fig1.update_layout(title="§1 — Time-to-escalation by archetype (F4 risk-threshold event; KM, "
                         "right-censored)",
                   xaxis_title="time to F4 escalation (sim-min)", yaxis_title="S(t) — not yet escalated",
                   height=420, legend=dict(orientation="h", yanchor="top", y=-0.18, x=0))
fig1.write_html(str(_root / "outputs" / "E3_s1_km_by_archetype.html"))
print(f"§1 event clock = F4 risk-threshold (risk≥{cctx.threshold}), per-sample · pid0 = "
      f"{F4_EVENT_PID0_MIN:.0f} sim-min (served-cadence form 915)")
print(f"§1 escalators (event=1) = {n_event} · right-censored (event=0) = {n_cens}")
print("§1 median F4-event by archetype (sim-min): " +
      " · ".join(f"{a} {m:.0f}" for a, m in _median_event.items()))
print("   cross-check vs lead audit: compensated reaches F4 EARLIEST (890) but only modestly "
      "(coupled 910, silent 928) — consistent with 'escalates somewhat faster, still usable lead "
      "(AEGIS 4/4, ~95 min)', NOT without warning. Agrees; no divergence.")
fig1

# %% [markdown]
# ## §2 — The current readout to beat
#
# ### Plain
# The ward card already shows a rough **time** band, not just a flag — "this patient is likely to
# escalate in about 1–2 hours." It is a **per-patient** estimate (about *this* patient), **not** a
# cohort-wide average lead. The honest gap: that band is **uncalibrated** — nobody has checked the
# "~1–2 h" ranges against when patients actually escalate. Closing that gap is §4's job; §2 just
# shows what's there to beat.
#
# ### Dev
# Reuses the ward's own ETA, unchanged: `eta_band(cone, now_min, risk_now, threshold)`
# (`styx.cohort.ranking`) off the forecast cone, banded to an ordinal label via
# `styx.readouts.eta_ordinal` + `styx.explain.ETA_BANDS`. The index-patient cone is
# `styx.forecast.project(cctx.risk[0], …, default_idx, cctx.band)`; the figure is the app's
# `styx.viz.cone.cone_figure`. Single-sourced against the board: the §2 self-check asserts the band
# equals the `ward_frame` row for the same patient/frame.
#
# ### Tech
# The band is read off the cone at the silent-window frame (`cctx.default_idx`, t=750): **soonest**
# = where the cone's *upper* edge crosses the threshold (the optimistic earliest, +70 min here →
# ordinal "1–2 h"); **central** = where the *point* forecast crosses (None here → the point never
# crosses within the horizon, so the band is open-ended and `confident=False`). It is per-patient
# and **uncalibrated**: the band derives geometrically from the cone, never validated against the
# observed F4-event times (pid 0's soonest +70 → ~820 vs the actual F4 event at 910 — optimistic by
# ~90 min). That validation is exactly §4. NB: this ETA targets the **same F4 clock** as §1 — see
# the §1 stop-and-decide on whether §3 should re-target to the clinical NEWS2-red event.

# %%
from styx.cohort import eta_band, ward_frame  # noqa: E402
from styx.explain import ETA_BANDS  # noqa: E402
from styx.forecast import project  # noqa: E402
from styx.readouts import eta_ordinal  # noqa: E402
from styx.viz.cone import cone_figure  # noqa: E402

_di = cctx.default_idx
_cone = project(cctx.risk[0], cctx.t_min, _di, cctx.band)
_status, _soon, _cen, _conf = eta_band(_cone, float(cctx.t_min[_di]), float(cctx.risk[0][_di]),
                                       cctx.threshold)
_band_label = ETA_BANDS[eta_ordinal(_soon)]

# single-source against the ward board (same eta_band the cohort triage reads)
_row0 = next(r for r in ward_frame(cctx, _di) if r.pid == 0)
assert _row0.eta_soonest_min == _soon and _row0.eta_central_min == _cen, (
    f"§2 ETA band must match the ward (single source): {_row0.eta_soonest_min}/{_soon}"
)

fig2 = cone_figure(cctx.t_min, cctx.risk[0], _cone, cctx.threshold, now_idx=_di)
fig2.add_annotation(xref="paper", yref="paper", x=0.0, y=1.10, showarrow=False, xanchor="left",
                    font=dict(size=11, color=pal.ANNOTATION),
                    text=f"this patient — current ward ETA: escalating, ~{_band_label} "
                         f"(soonest +{_soon:.0f} min; point unconfirmed → open-ended). UNCALIBRATED.")
fig2.write_html(str(_root / "outputs" / "E3_s2_current_eta.html"))
print(f"§2 index-patient ETA (per-patient, NOT cohort-lead): status={_status} · "
      f"soonest=+{_soon:.0f} min · ordinal '{_band_label}' · confident={_conf}")
print("✓ ETA band reproduces from eta_band == ward_frame (single source); uncalibrated today → §4")
fig2

# %% [markdown]
# ## §3 — Survival analysis on the trajectory  (clinical target = time-to-NEWS2-red)
#
# ### Plain
# Now learn the **time**: from STYX's early signal, how long until the *standard* (NEWS2) would
# escalate this patient? This re-keys the target to the **clinical** escalation event — the
# NEWS2-red trigger, the same clock the ≈5 h lead is measured to — rather than STYX's own internal
# line (§1's F4 clock, which would have us grading STYX against itself). A neat, honest result falls
# out: telling *whether* a patient escalates is trivial on this data (a perfect in-sample score),
# but telling *when* is genuinely harder — the time model is good, **not** perfect, even in-sample.
#
# ### Dev
# Builds a **notebook-local** survival frame keyed to the clinical clock: `duration =
# styx.readouts.news2_complete_crossing(p)` if it fires, else right-censored at the stay-end horizon
# (1435 sim-min); `event = 1/0`. The package's `reach.history.survival_table`/`stratify` are left
# **F4-keyed** (their R1 use is untouched) — consumer-only. Features are the shared single-source
# panel `notebooks.analysis.trajectory_features` (history + the silent-window telemetry panel
# `risk_snap`/`aegis_fired`/`risk_slope`) — the *same* panel the saturation AUC uses, so the
# binary-vs-survival contrast is like-for-like. Model: `lifelines.CoxPHFitter` (the estimator
# `stratify` uses) on standardised covariates; concordance via `.concordance_index_`.
#
# ### Tech
# Cox PH on z-scored covariates, `penalizer=0.1`. The ridge penalty is **load-bearing and
# diagnostic**: the telemetry panel near-perfectly separates the *binary* outcome (NB1 §11's
# construct artifact), so an unregularised Cox sends coefficients toward ±∞ — the same saturation,
# resurfacing as a fitting pathology. Event = NEWS2-red crossing; right-censored at 1435. **C-index
# = 0.9154** (telemetry+history) vs **0.9105** telemetry-only (history marginal +0.005 — the
# saturation "no marginal lift" story again). Crucially this is **not** the binary AUC's 1.000: the
# *timing* concordance does not saturate, so it is informative that predicting *when* is the harder
# target. Still **in-sample / construct validity, not performance** — no predictive-lift claim.
# Failure modes: proportional-hazards assumption (unchecked here); near-zero-variance covariates
# (`risk_slope`) need the standardisation above; one synthetic cohort, in-sample.

# %%
import warnings  # noqa: E402

from lifelines import CoxPHFitter  # noqa: E402

from notebooks.analysis import TELEMETRY_FEATURES, saturation_aucs, trajectory_features  # noqa: E402
from styx.readouts import news2_complete_crossing  # noqa: E402

_arch = {q.pid: q.archetype.value for q in cohort.patients}
_END = float(cohort.t_min[-1] if hasattr(cohort, "t_min") else cohort.patients[0].t_min[-1])
_news2 = {q.pid: news2_complete_crossing(q) for q in cohort.patients}

# --- coverage gate (decision-B precondition): does the CLINICAL event fire across the escalators? ---
_esc_pids = [q.pid for q in cohort.patients if q.outcome is Outcome.ESCALATED]
_rec_pids = [q.pid for q in cohort.patients if q.outcome is Outcome.RECOVERED]
_esc_fired = [pid for pid in _esc_pids if _news2[pid] is not None]
_rec_fired = [pid for pid in _rec_pids if _news2[pid] is not None]
_event_times = np.array([_news2[pid] for pid in _esc_fired])
assert len(_esc_fired) == 21 and len(_esc_pids) == 21, f"NEWS2-red fires {len(_esc_fired)}/21 esc"
assert len(_rec_fired) == 0, f"NEWS2-red leaked into {len(_rec_fired)} recovered patients"
assert float(np.median(_event_times)) == 945.0, f"NEWS2-red median moved off 945: {np.median(_event_times)}"
print(f"§3 coverage gate: NEWS2-red fires {len(_esc_fired)}/21 escalators · {len(_rec_fired)}/29 "
      f"recovered · event median {np.median(_event_times):.0f} (censor horizon {_END:.0f})")

# --- notebook-local survival frame keyed to the CLINICAL clock (package survival_table left F4) ---
surv = trajectory_features(cohort, cctx)  # the shared single-source feature panel
surv["duration"] = [(_news2[pid] if _news2[pid] is not None else _END) for pid in surv.pid]
surv["event"] = [(1 if _news2[pid] is not None else 0) for pid in surv.pid]
surv["arch"] = surv.pid.map(_arch)
assert int(surv.event.sum()) == 21 and int((surv.event == 0).sum()) == 29

# standardise covariates (z-score) — risk_slope is near-zero-variance; deterministic
_COVS = [*TELEMETRY_FEATURES, "history"]
_Z = surv.copy()
for _c in _COVS:
    _sd = _Z[_c].std(ddof=0)
    _Z[_c] = (_Z[_c] - _Z[_c].mean()) / (_sd if _sd > 0 else 1.0)

# Cox PH predicting time-to-NEWS2-red; penalizer stabilises the near-separating telemetry panel
with warnings.catch_warnings():
    warnings.simplefilter("ignore")  # the low-variance/separation warnings are the point, narrated above
    _cph = CoxPHFitter(penalizer=0.1).fit(_Z[[*_COVS, "duration", "event"]], "duration", "event")
    _cph_tele = CoxPHFitter(penalizer=0.1).fit(
        _Z[[*TELEMETRY_FEATURES, "duration", "event"]], "duration", "event")
c_index = float(_cph.concordance_index_)
c_index_tele = float(_cph_tele.concordance_index_)
auc_binary = saturation_aucs(cohort, cctx).telemetry  # the binary baseline E3 reframes (telemetry)

print(f"§3 Cox C-index (time-to-NEWS2-red): telemetry+history {c_index:.4f} · "
      f"telemetry-only {c_index_tele:.4f} (history marginal {c_index - c_index_tele:+.4f})")
print(f"§3 binary baseline (telemetry → escalate y/n): AUC {auc_binary:.3f} — saturates "
      f"(construct artifact); the TIME concordance {c_index:.3f} does NOT — 'when' is the harder target")
print("§3 NEWS2-red event median by archetype (sim-min): " + " · ".join(
    f"{a} {np.median([_news2[pid] for pid in _esc_pids if _arch[pid] == a]):.0f}"
    for a in ("silent_hypoxia", "coupled", "compensated")) +
    "  — compensated escalates earliest (920), surfaced not averaged")

# --- per-patient predicted survival curves, coloured by archetype (escalators) ---
_ARCH_COL = {"silent_hypoxia": pal.RISK, "coupled": pal.EARLY_WARNING, "compensated": pal.THRESHOLD}
_sf = _cph.predict_survival_function(_Z[_COVS])  # index=times, columns=row order (pid order)
fig3 = go.Figure()
_seen = set()
for _i, pid in enumerate(surv.pid):
    if _news2[pid] is None:
        continue  # show the escalators' predicted curves (censored recoverers omitted for legibility)
    a = _arch[pid]
    fig3.add_trace(go.Scatter(
        x=_sf.index.to_numpy(dtype=float), y=_sf.iloc[:, _i].to_numpy(dtype=float), mode="lines",
        line=dict(color=_ARCH_COL[a], width=3 if pid == 0 else 1),
        opacity=1.0 if pid == 0 else 0.45, name=a if a not in _seen else None,
        showlegend=a not in _seen, legendgroup=a,
        hovertemplate=f"pid {pid} ({a})<br>%{{x:.0f}} min · S=%{{y:.2f}}<extra></extra>"))
    _seen.add(a)
fig3.update_layout(
    title="§3 — Cox predicted survival to NEWS2-red, by archetype (index pid 0 bold)",
    xaxis_title="time to NEWS2-red escalation (sim-min)", yaxis_title="predicted S(t) — not yet escalated",
    height=440, legend=dict(orientation="h", yanchor="top", y=-0.18, x=0))
fig3.write_html(str(_root / "outputs" / "E3_s3_survival.html"))
fig3

# %% [markdown]
# ### §3 self-check
# %%
assert (len(_esc_fired), len(_rec_fired)) == (21, 0), "coverage gate drifted"
assert (int(surv.event.sum()), int((surv.event == 0).sum())) == (21, 29), "events/censored drifted"
assert float(np.median(_event_times)) == 945.0, "NEWS2-red event median drifted off 945"
assert abs(c_index - 0.9154) < 5e-4, f"Cox C-index drifted off 0.9154: {c_index}"
assert auc_binary == 1.0, f"binary baseline AUC moved off 1.000: {auc_binary}"
print("✓ NEWS2-red 21/21 escalators · 0/29 recovered · event median 945 · 21 events / 29 censored")
print(f"✓ Cox C-index {c_index:.4f} (timing, in-sample construct validity — NOT performance); "
      f"binary AUC {auc_binary:.3f} saturates → 'when' is the harder, richer target than 'whether'")

# %% [markdown]
# ## §4 — Calibrate the time estimate (the deliverable)
#
# ### Plain
# The point of §3 was that *when* is the harder target — telling who escalates is trivial here, but
# telling **when** is not. So the question that matters for a time readout: when STYX says "likely
# in ~3 hours," does it actually happen around 3 hours? **On average, yes** — the predicted times
# track the observed ones closely. **But for the compensated pattern it is badly off**: the model
# predicts those patients escalating *later* than they really do. A single confident "~Xh" would
# mislead for them — so §5's card must not over-promise for that group. We surface the subgroup
# miss rather than hide it inside a reassuring cohort average.
#
# ### Dev
# `notebooks.analysis.survival_calibration` reuses the **already-fitted §3 Cox** (no refit — the
# C-index is re-asserted as proof) and compares mean Cox-predicted S(t) to Kaplan–Meier observed
# S(t) at fixed horizons spanning the observed NEWS2-red events, **overall and per archetype**.
# Censoring-aware (KM). New plotting: a plotly calibration scatter (predicted vs observed; the
# diagonal is perfect). scikit-survival's integrated Brier is **skipped** — not essential for an
# in-sample explorer and it would add a dependency; the lifelines-native predicted-vs-observed view
# suffices (per the STOP-and-surface rule, no silent dep add).
#
# ### Tech
# Discrepancy = sup-norm |predicted − observed| over the horizon grid. **Overall gap 0.035** —
# calibration-in-the-large is tight, but *necessarily* so in-sample (the Cox baseline hazard is fit
# to this cohort's events, so mean-predicted ≈ KM by construction). **Per-archetype it is poor:
# compensated 0.710, silent-hypoxia 0.252, coupled 0.201** — the cohort mean MASKS a severe
# compensated miscalibration (predicted survival far above observed → the model under-warns on
# compensated timing). Same averaging-hides-subgroup pattern as NB1's faithfulness 0/13, and the
# same root: compensated's silent-window-frame features understate its fast late escalation.
# (lifelines' ICI corroborates a heavy-tailed individual miss; reported here as the transparent
# per-archetype gaps.) Caveat: compensated n=4 → coarse KM, so 0.71 is a coarse *magnitude*, but the
# *direction* is robust and consistent with the known compensated signal gap. **Why in-sample
# calibration is optimistic:** calibration is exactly what degrades out-of-sample — here predicted≈
# observed partly by construction — so real-data calibration (the NB2/NB3 path) is the actual test;
# in-sample is necessary, not sufficient. Relationship to §2 is **two-axis, not head-to-head**: §2's
# cone ETA predicts the internal F4 clock, §4's model predicts the clinical NEWS2-red clock —
# different events, never calibrated against each other; E3 improves the readout on both axes
# (internal→clinical target AND uncalibrated→calibrated, where the calibration holds).

# %%
from notebooks.analysis import survival_calibration  # noqa: E402

# SAME fitted Cox from §3 — re-assert discrimination to prove no refit (a refit would drift the pin)
assert abs(_cph.concordance_index_ - 0.9154) < 5e-4, "§4 must reuse §3's fitted Cox — C-index drifted"

_cal = survival_calibration(_cph, _Z, _COVS, group_col="arch")
_GROUPS = ("overall", "silent_hypoxia", "coupled", "compensated")
print(f"§4 C-index (same fitted Cox, no refit) = {_cal.c_index:.4f}")
print("§4 calibration gap (predicted vs observed S, sup-norm): " +
      " · ".join(f"{g} {_cal.max_gap[g]:.3f}" for g in _GROUPS))

# the §4 → §5 hinge: the calibration verdict the card band must be faithful to
_bad = sorted(g for g in ("silent_hypoxia", "coupled", "compensated") if _cal.max_gap[g] > 0.20)
verdict = (
    f"calibration-in-the-large GOOD (overall gap {_cal.max_gap['overall']:.3f}) but MISLEADING — "
    f"per-subgroup POOR for {_bad}; compensated severely over-predicted (gap "
    f"{_cal.max_gap['compensated']:.3f} → model says they escalate later than they do). IN-SAMPLE, "
    f"so optimistic; real-data calibration (NB2/NB3) is the actual test. §5 card: do NOT show a "
    f"confident time for compensated — widen/flag low-confidence for that archetype."
)
print("§4 VERDICT (for §5):", verdict)

# calibration scatter — predicted vs observed S at each horizon, per group; on the diagonal = calibrated
_GRP_COL = {"overall": pal.ANNOTATION, "silent_hypoxia": pal.RISK,
            "coupled": pal.EARLY_WARNING, "compensated": pal.THRESHOLD}
fig4 = go.Figure()
fig4.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="perfectly calibrated",
                          line=dict(color=pal.NEUTRAL, dash="dot")))
for g, col in _GRP_COL.items():
    fig4.add_trace(go.Scatter(
        x=_cal.predicted[g], y=_cal.observed[g], mode="markers", name=f"{g} (gap {_cal.max_gap[g]:.2f})",
        marker=dict(color=col, size=5 if g == "overall" else 8,
                    symbol="x" if g == "overall" else "circle", opacity=0.8)))
fig4.update_layout(title="§4 — Calibration: Cox-predicted vs observed survival at fixed horizons "
                         "(on the diagonal = calibrated)",
                   xaxis=dict(title="Cox-predicted S(t)", range=[-0.02, 1.02]),
                   yaxis=dict(title="KM observed S(t)", range=[-0.02, 1.02]),
                   height=460, legend=dict(orientation="h", yanchor="top", y=-0.18, x=0))
fig4.write_html(str(_root / "outputs" / "E3_s4_calibration.html"))
fig4

# %% [markdown]
# ### §4 self-check
# %%
assert abs(_cal.c_index - 0.9154) < 5e-4, "C-index pin (same Cox) drifted — a refit happened"
assert abs(_cal.max_gap["overall"] - 0.035) < 5e-3, f"overall calibration gap drifted: {_cal.max_gap['overall']}"
assert abs(_cal.max_gap["compensated"] - 0.710) < 5e-3, f"compensated gap drifted: {_cal.max_gap['compensated']}"
print("✓ same fitted Cox (C-index 0.9154, no refit)")
print("✓ calibration-in-the-large GOOD (overall gap 0.035) but compensated 0.710 — subgroup "
      "miscalibration SURFACED, not averaged; in-sample → optimistic, real-data is the test (§5 hinge)")

# %% [markdown]
# ## §5 — The calibrated readout card (an illustration, not a deployable readout)
#
# ### Plain
# Here is what a time-to-escalation card *could* look like: "likely to reach NEWS2 escalation in
# ~X h." But §4 showed the estimate is **not trustworthy per-patient for any pattern**, so every
# card carries the caveat *"calibrated in the mean, not per-patient — illustration only."* And the
# **compensated** card deliberately reads **"timing uncertain"** instead of a number: for that
# pattern the model predicts escalation *later* than it really happens (the exemplar: predicted
# ~4.9 h, actual ~2.9 h) — the **dangerous** error, a nurse told "~5 h" would stand down on someone
# about to breach in under 3. silent/coupled err the other way (predict earlier than observed) —
# still wrong, but conservative.
#
# ### Dev
# Reuses §3's **fitted** `_cph` (no refit) and §4's `survival_calibration` verdict (`_cal`). The
# per-patient time is read off the predicted survival curve as quantile crossings (median = S↓0.5;
# band = S↓0.75 … S↓0.25), presented in the app's ordinal idiom (`styx.readouts.eta_ordinal` +
# `styx.explain.ETA_BANDS`) but **driven by the NEWS2-red survival estimate, not the F4 cone**. The
# per-archetype confidence flag is derived from `_cal.max_gap` (the *same* computed verdict, not
# re-narrated). New rendering only: the app's card is F4/cone-driven, so a survival-quantile card
# has no existing builder.
#
# ### Tech
# Median time = the horizon where predicted `S(t)` falls through 0.5 (from "now" = the silent-window
# frame, t=750); the band spans the 0.75 and 0.25 crossings — wide, because it carries the full
# survival spread, not a tight point. Per subgroup the estimate is untrustworthy (§4 gaps 0.20–0.71),
# so **no archetype is flagged high-confidence**; compensated is flagged **low** (it under-warns).
# This is an **in-sample illustration of the idiom**, not a deployable readout — it shows what a
# calibrated card would claim and, given §4, what it honestly cannot.

# %%
_NOW = float(cctx.t_min[cctx.default_idx])  # the silent-window frame "now" (t=750), as §2
_grid = np.linspace(_NOW, _END, 300)


def _q_cross(pid: int, q: float) -> float | None:
    """Horizon (sim-min) where this patient's predicted survival first falls through ``q``."""
    s = _cph.predict_survival_function(_Z[_Z.pid == pid][_COVS], times=_grid).iloc[:, 0].to_numpy()
    hit = np.flatnonzero(s <= q)
    return float(_grid[hit[0]]) if hit.size else None


# confidence flag per archetype, DERIVED from §4's verdict (same computed max_gap) — none "high"
_card_conf = {a: ("low" if _cal.max_gap[a] > 0.5 else "moderate")
              for a in ("silent_hypoxia", "coupled", "compensated")}

_exemplars = []  # (archetype, pid, median, soon, late, observed, confidence)
for a in ("silent_hypoxia", "coupled", "compensated"):
    pid = next(q.pid for q in cohort.patients if _arch[q.pid] == a and _news2[q.pid] is not None)
    _exemplars.append((a, pid, _q_cross(pid, 0.5), _q_cross(pid, 0.75), _q_cross(pid, 0.25),
                       _news2[pid], _card_conf[a]))

_GRP_COL = {"silent_hypoxia": pal.RISK, "coupled": pal.EARLY_WARNING, "compensated": pal.THRESHOLD}
fig5 = go.Figure()
for _y, (a, pid, med, soon, late, obs, conf) in enumerate(_exemplars):
    _h = lambda t: None if t is None else (t - _NOW) / 60.0  # noqa: E731 — sim-min → hours-from-now
    _x0, _x1, _xm, _xo = _h(soon), _h(late if late else _END), _h(med), _h(obs)
    if conf != "low":  # estimate + wide band (silent/coupled) — still caveated as mean-only
        fig5.add_trace(go.Scatter(x=[_x0, _x1], y=[_y, _y], mode="lines",
                                  line=dict(color=_GRP_COL[a], width=12), opacity=0.30, showlegend=False))
        fig5.add_trace(go.Scatter(x=[_xm], y=[_y], mode="markers", showlegend=False,
                                  marker=dict(color=_GRP_COL[a], size=16, symbol="line-ns",
                                              line=dict(width=3))))
    else:  # compensated — NO crisp band; flagged low-confidence "timing uncertain"
        fig5.add_trace(go.Scatter(x=[_x0, _x1], y=[_y, _y], mode="lines",
                                  line=dict(color=pal.NEUTRAL, width=12, dash="dot"), opacity=0.25,
                                  showlegend=False))
        fig5.add_annotation(x=_x0, y=_y + 0.22, xanchor="left", showarrow=False,
                            text="⚠ LOW CONFIDENCE — timing uncertain (model under-warns)",
                            font=dict(size=10, color=pal.THRESHOLD))
    fig5.add_trace(go.Scatter(x=[_xo], y=[_y], mode="markers", showlegend=False,
                              marker=dict(color=pal.ANNOTATION, size=13, symbol="x",
                                          line=dict(width=2)),
                              hovertemplate=f"{a} pid{pid} — observed NEWS2-red<extra></extra>"))
fig5.add_annotation(xref="paper", yref="paper", x=0.0, y=1.10, showarrow=False, xanchor="left",
                    font=dict(size=11, color=pal.ANNOTATION),
                    text="Illustration only — calibrated in the mean, NOT per-patient (§4); not a "
                         "deployable readout.  bar = predicted band · ✕ = observed escalation")
fig5.update_layout(title="§5 — Calibrated time-to-NEWS2-red card (per-archetype exemplars)",
                   xaxis_title="hours from now (t=750) to NEWS2 escalation",
                   yaxis=dict(tickvals=list(range(len(_exemplars))),
                              ticktext=[f"{a}<br>pid{pid} · conf={conf}"
                                        for a, pid, *_rest, conf in _exemplars], range=[-0.5, 2.7]),
                   height=380, margin=dict(t=80, l=120))
fig5.write_html(str(_root / "outputs" / "E3_s5_card.html"))
for a, pid, med, soon, late, obs, conf in _exemplars:
    _hm = (obs - _NOW) / 60.0
    if conf == "low":
        print(f"§5 card — {a} pid{pid}: TIMING UNCERTAIN (low confidence — under-warns; "
              f"predicted ~{(med - _NOW) / 60:.1f} h but observed {_hm:.1f} h) [no crisp time shown]")
    else:
        _band = f"{(soon - _NOW) / 60:.1f}–{((late - _NOW) / 60) if late else float('inf'):.1f} h"
        print(f"§5 card — {a} pid{pid}: ~{(med - _NOW) / 60:.1f} h ({_band}) · conf={conf} · "
              f"observed {_hm:.1f} h  [caveat: calibrated in the mean, not per-patient]")
fig5

# %% [markdown]
# ### §5 self-check
# %%
assert abs(_cph.concordance_index_ - 0.9154) < 5e-4, "§5 must reuse §3's fitted Cox — C-index drifted"
assert _card_conf["compensated"] == "low", "the §4→§5 hinge: compensated must be the low-confidence card"
assert "high" not in _card_conf.values(), "no archetype may read as per-patient calibrated (§4 verdict)"
print(f"✓ same fitted Cox (C-index {_cph.concordance_index_:.4f}); card flags compensated LOW-confidence; "
      "no archetype high — band honestly wide across the board, illustration not deployable")

# %% [markdown]
# ## §6 — Decision & honesty close (go/no-go)
#
# ### Plain
# Should STYX show nurses a "time to escalation" instead of a flag? **The idea is right; the current
# estimate is not ready.** A time is more useful than a yes/no, and — unlike "will they escalate?",
# which is trivially perfect on this data — telling *when* is a genuine, harder problem the model does
# meaningfully (not perfectly) well. But §4 showed the per-patient times aren't yet trustworthy, and
# nothing here has been tested on real patients. So: **pursue the reframe; don't ship the card yet.**
#
# ### Dev
# What would have to be true to adopt the calibrated card: (a) **per-subgroup calibration** brought
# into line (today it is off for every archetype, worst — and most dangerously — for compensated),
# and (b) **out-of-sample / real-data calibration** demonstrated (the NB2/NB3 path). The reframe
# itself — a time-to-event target on the **clinical NEWS2-red clock** — is sound and reusable; it is
# the *estimate's trustworthiness* that is blocked, not the framing.
#
# ### Tech — both halves
# **The win (the reframe is sound).** Timing is the real, non-circular, non-saturating target: §3's
# C-index ≈ 0.915 where the binary AUC saturates at 1.000 — predicting *when* is harder than
# *whether* and does not saturate. NEWS2-red is clinically meaningful and **independent of STYX**
# (decision B — we predict the standard's trigger, not STYX grading itself against its own F4 line).
# **The bound (the estimate is not deployable).** Per-subgroup calibration is poor in-sample: anchor
# on **coupled (sup-norm 0.20 at n=11 — the robust result)**, with silent-hypoxia 0.252 at n=6;
# compensated is clearly miscalibrated in the **under-warning** (dangerous) direction, but its 0.710
# magnitude is **uninterpretable at n=4** and must not carry the verdict. Calibration-in-the-large
# (0.035) is a by-construction tautology (the baseline hazard is fit to these events), not evidence.
# And all of it is in-sample-optimistic. **The call:** **conditional adopt** — pursue time-to-event
# over binary as the right direction; the calibrated card is **blocked on per-subgroup calibration
# AND real-data validation**, never an unqualified "ship it."

# %%
# the verdict, built from the SAME computed numbers (not re-narrated) so it cannot drift
_win = (f"reframe sound: timing C-index {c_index:.3f} (non-saturating) vs binary AUC "
        f"{auc_binary:.3f} (saturates); clinical NEWS2-red target, independent of STYX")
_bound = (f"estimate not deployable: per-subgroup calibration poor — coupled {_cal.max_gap['coupled']:.2f} "
          f"@n=11 (robust anchor), silent {_cal.max_gap['silent_hypoxia']:.2f} @n=6; compensated "
          f"under-warns (magnitude {_cal.max_gap['compensated']:.2f} uninterpretable @n=4); "
          f"overall {_cal.max_gap['overall']:.3f} is a by-construction tautology; all in-sample")
print("§6 WIN  —", _win)
print("§6 BOUND —", _bound)
print("§6 CALL  — CONDITIONAL ADOPT: pursue time-to-event (right direction); calibrated card BLOCKED "
      "on (a) per-subgroup calibration and (b) real-data validation (NB2/NB3). Not 'ship it'; not 'E3 failed'.")

# %% [markdown]
# ### §6 self-check
# %%
assert abs(c_index - 0.9154) < 5e-4 and auc_binary == 1.0, "the win's numbers drifted"
assert abs(_cal.max_gap["coupled"] - 0.201) < 5e-3, "coupled robust anchor (0.20 @n=11) drifted"
assert abs(_cal.max_gap["silent_hypoxia"] - 0.252) < 5e-3, "silent calibration gap drifted"
print("✓ verdict holds both halves on the SAME computed numbers: WIN (timing 0.915 non-saturating vs "
      "binary 1.000) + BOUND (coupled-anchored 0.20 @n=11, compensated under-warns, in-sample) → "
      "conditional adopt, pending per-subgroup calibration + real-data validation")
