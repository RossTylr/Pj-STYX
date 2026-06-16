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
# ## §1 — Reframe the target: time-to-escalation  (filled in Phase 1)
#
# Define the outcome (time-to-escalation), right-censoring (never-escalate patients), and the risk
# set. **Reuse** `styx.reach.history.survival_table(cctx)` for durations/event/density and
# `stratify(cctx)` for Kaplan–Meier curves by archetype — do not reinvent the table.

# %% [markdown]
# ## §2 — The current readout to beat  (filled in Phase 1)
#
# Show the banded ETA the ward already renders — `eta_band` / `eta_ordinal` / `ETA_BANDS` off the
# forecast cone (UQ-1 ranges, `styx.cohort.ranking` + `styx.readouts` + `styx.explain`). This is
# today's operational time-to-escalation surface; E3's job is to **calibrate** it, not invent one.

# %% [markdown]
# ## §3 — Survival analysis on the trajectory  (filled in Phase 2)
#
# Fit the **existing** Cox PH (`styx.reach.history.stratify`) on the trajectory/history features;
# optional discrete-time hazard as a cross-check only; contrast with the binary-outcome baseline.
# The exploration is **calibration**, not model-selection from scratch.

# %% [markdown]
# ## §4 — Calibrate the time estimate (the new work)  (filled in Phase 3)
#
# Make the cone/survival estimates calibrated and quantify it: predicted-vs-observed at fixed
# horizons, concordance (C-index), censoring-aware integrated Brier. **Factor a calibration helper
# into `notebooks/analysis.py`** (single source). If a metric needs a library beyond the current
# deps (lifelines/sklearn), STOP and surface it — do not silently add.

# %% [markdown]
# ## §5 — The calibrated readout (deliverable)  (filled in Phase 4)
#
# How a calibrated time-to-escalation estimate with an uncertainty band changes the patient card
# vs the binary flag. A mock card: *"likely to cross in ~Xh (Y–Z), calibrated."*

# %% [markdown]
# ## §6 — Decision & honesty close  (filled in Phase 4)
#
# The go/no-go: adopt a calibrated time-to-escalation readout or not; what the calibration showed
# (well-calibrated? over/under-confident?); the in-sample caveat; pointer to the real-data path.
