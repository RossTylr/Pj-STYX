# EXPERIMENT_LOG.md — STYX

Append-only. One row per slice when its gate passes (BUILD_MVP.md). The
AEGIS→threshold lead-time is logged every time `synth/`, `forecast/`, or `risk/`
changes (Hard Rule 4).

| Slice | Gate | Result | Lead-time (min) | Date |
|-------|------|--------|-----------------|------|
| S0 — scaffold | none | repo skeleton runs; `pytest` collects; `streamlit run app/app.py` launches | — | 2026-06-06 |
| S1 — synth (F5) | **G1 ✅** | determinism (seed=42 ×2 identical); dissociable silent window; genuine RR–SpO₂ decoupling; ≥12-patient cohort, outcome-from-history AUC=1.000; `tests/test_g1.py` 9/9 green; `notebooks/01_synthetic_fidelity` renders 3 panels | **160** (decoupling onset → first sustained breach, seed=42) | 2026-06-06 |
| S1-refine — outcome realism | **G1 ✅ (re-check)** | outcome now *stochastic* (`P=sigmoid(5·(frailty−½))`, sampled); AUC scored on noisy observed `comorbidity_index` (not frailty); learnability is a **band** [0.60, 0.90] not a floor; cohort default 50. **AUC seed=42 = 0.782** (was 1.000); mix 21 ESCALATED / 29 RECOVERED; determinism intact; silent window + lead unchanged; `pytest` 9/9; `ruff` clean | **160** (unchanged; patient-0 stream bit-identical, verified n=12≡n=50) | 2026-06-06 |
| S2 — state + viz (F1) | **G2 ✅ (constructed)** | 2-D embedding of `VITALS` w/ named axes (oxygenation, effort), learned basin/attractor, pure `trajectory_figure`. PCA **fell back** to constructed: PC0 alone tracks *both* anti-correlated constructs (oxy r=−0.97 / effort r=+0.98), PC1 dominated by labs_proxy (loading 0.94, r≈0.10) → axis-1 illegible. Constructed axes: **oxygenation r=1.000, effort r=0.996** (both ≥0.60). Silent case drifts basin→attractor (**+1.378**). DET-1 identical coords; `tests/test_g2.py` 3/3; G1 re-run 6/6 (synth untouched); `ruff` clean; `notebooks/02_state_space` renders legibility panel + 3 trajectories | **160** (G1 re-check, unchanged — S2 reads cohort only) | 2026-06-09 |
| S1-enrich — archetypes + silent hypoxia | **G1 ✅ (re-check)** | deterioration **archetypes** (SILENT_HYPOXIA / COMPENSATED / COUPLED + STABLE) dissociate oxygenation from effort; patient 0 re-scripted as **silent hypoxia** (SpO₂ falls, RR/HR flat). `has_silent_window` **generalised** (locked decision): in-range + SpO₂-slope<0 + decoupling present; **dropped the RR-rising requirement** (silent hypoxia has effort flat). Labs (`labs_proxy`) given a later, independent onset (`T_LABS_MIN=660`) → semi-independent signal. Onset moved 600→**540** for lead headroom. **AUC seed=42 = 0.765** (in band, no creep); mix 21 ESCALATED / 29 RECOVERED (silent 6 / compensated 4 / coupled 11). DET-1 bit-identical; `tests/test_g1.py` 6/6; `ruff` clean | **200** (seed=42); **60-seed sweep min 130 / median 200 / max 245** — headroom restored (was min 90) | 2026-06-09 |
| S2-refit — state on enriched cohort | **G2 ✅ (constructed)** | re-fit `fit_embedding` on the enriched cohort; fork **re-run, PCA still falls back** (PC0 still absorbs both: oxy −0.82 / effort +0.89; PC1 a weak mix 0.34/0.45; expl-var 69/14/10) — **not forced** (constructed valid). Constructed axes **oxy r=1.000, effort r=0.995**. *Payoff:* the named plane is now genuinely 2-D — archetype now-centroids separate **off-diagonal**: silent (oxy −3.4, **effort −0.5**), compensated (oxy −0.8, **effort +7.8**), coupled (−3.5, +4.3), stable basin (+0.7, −0.7). Silent case drift **+0.69** (>0). `tests/test_g2.py` 3/3; full suite 12/12; `ruff` clean; notebooks 01 (archetype panel) + 02 (separation scatter + 3 distinct trajectories) render | **200** (G1 re-check; S2 reads cohort only) | 2026-06-09 |
| S3 — forecast, risk, AEGIS (F2, F4, F7) | **G3 ✅** | anticipation dissociated on patient 0, **in order and stable at cadence**. *Phase 0:* `learn_basins` now learns **one attractor per escalating archetype** (silent_hypoxia / compensated / coupled — no clustering RNG, DET-1 by construction); `trajectory_drift` measures travel toward the **nearest** mode → silent-case drift **+0.69 → +1.10** (selects the oxygenation-led mode); G2 re-run 3/3. *F2:* deterministic least-squares trend + **split-conformal** bands (fixed non-index calibration, empirical quantile, clipped [0,1], widens 0.09→0.24); "fires" = cone upper edge reaches threshold for 3 **consecutive** re-scores (sustain rejects the early transient that else fires before AEGIS). *F4:* continuous waterline `risk = 0.5·proximity + 0.5·exceedance` — proximity rises in the silent window (max 0.26 < 0.5) but the absolute NEWS2-style exceedance term gates the crossing, so 0.5 is crossed **only at breach** (fires last). *F7 AEGIS:* trend-smoothed **2-D state-position** departure from personal baseline (max-axis, generalises beyond hypoxia — fires on compensated too), sustained K=3σ. **Firing order (at-cadence 15 min): AEGIS 705 → forecast 750 → threshold 915**; raw 700 → 730 → 910. `tests/test_g3.py` 4/4 (determinism, order, lead≥floor, cadence preserves); G1 6/6 (synth untouched) + G2 3/3 + full suite 16/16; `ruff` clean; `notebooks/03_anticipation_lead` renders 3 panels. **⚠ labs_proxy is dead-weight in S3** (constructed embedding gives it 0 loading → no proximity; max 1.057 → never the worst-vital exceedance) — flagged per plan; SIG-1 slot to revisit at deployment, out of S3 scope (Hard Rule 4 forbids touching synth here) | **210** at-cadence (= raw; cadence preserves, floor `AEGIS_LEAD_FLOOR_MIN`=180). **Adequacy: clinically meaningful (~3.5 h)**, not thin | 2026-06-09 |

**S1-enrich / S2-refit notes.** The first S2 fell back to constructed because every escalator was the
*coupled* shape — oxygenation and effort moved together on one diagonal, so the state space was
effectively 1-D, `labs_proxy` was dead weight (PC1 nuisance), and the engine never produced silent
hypoxia (the AEGIS/F7 phenomenon). Fix in the **engine**: `generate_episode` now takes an `Archetype`
and splits the post-onset slopes — SILENT_HYPOXIA (SpO₂ full, RR/HR ≈0), COMPENSATED (RR/HR up, SpO₂
shallow), COUPLED (legacy). All keep the coupled pre-onset regime so the coherence collapse is still
detectable. `build_cohort` scripts patient 0 = silent hypoxia and draws each escalator's shape uniformly
from the seeded child stream (DET-1 preserved; patient-0 stream untouched, comorbidity draw still
trailing). `has_silent_window` generalised to a multivariate adverse-trend test (user-locked) since
silent hypoxia has RR flat. **Outcome path unchanged** (sigmoid of frailty over the observable
`comorbidity_index`) so AUC stayed in band (0.765) — the richer vitals don't leak into the label.
**G2 still ships constructed**: even with off-diagonal archetypes, the cohort's dominant variance is the
shared "severity" direction (oxy down + effort up), so PC0 keeps absorbing both — *not* worth over-tuning
the engine to flip the mode (per plan). The substantive win landed anyway: the named oxy×effort plane now
carries real 2-D structure (silent vs compensated separate **only** on effort), which is the differentiator
a single risk line can't show and the shape ECHO will later match. Labs given its own later onset so it
feeds S3 risk as semi-independent signal without hijacking the map. Re-run G1+G2 after any further
`synth/forecast/risk` change (Hard Rule 4). LOC (changed): `scenario` 107 / `cohort` 128 (+~25) /
`synth/gates` 146 (−4) / `synth/__init__` 27; Phase B = **zero** `styx/` change (auto-fork), notebooks only.

**S2 notes.** F1 = a deterministic linear map: standardise the 5-D `VITALS` vector, project onto
two axes. `fit_embedding` is PCA-first with an auto-fork — it builds the PCA candidate, labels/orients
each axis by its construct correlation, then asks the canonical gate helper (`axis_construct_corr` +
`is_legible`, deferred-imported to keep the `gates → embedding` layering) whether the axes are legible.
On seed=42 PCA **failed** the fork and fell back to the hand-built oxygenation × effort projection: the
synthetic deterioration drives SpO₂ down *and* RR/HR up together, so the two named constructs are
strongly anti-correlated and PC0 (75% var) captures both at once (oxy −0.97 / effort +0.98), leaving
PC1 (15% var) on the labs_proxy nuisance axis (r≈0.10) — two axes, one construct, illegible. The
constructed fallback is legible by construction (oxy r=1.000, effort r=0.996) — a valid G2 pass, and
exactly the scenario the fork exists for. Basin = mean/σ of in-range samples (any patient); attractor =
mean/σ of breach samples among escalators; `trajectory_drift` projects the silent case's onset→breach
travel onto the basin→attractor unit vector (+1.378, toward crisis — the G1↔G2 link). S2 reads the
cohort only, so Hard Rule 4's `synth/` invariant is untouched: G1 re-run 6/6, lead unchanged at 160.
LOC: `constructs` 30 / `embedding` 132 / `gates` 49 / `viz/trajectory` 45 / `state/__init__` 29 /
`test_g2` 35 (+config 6). The five-file set is what `BUILD_MVP.md` prescribes for S2; `embedding.py` is
the cohesive hub (mirrors S1's `gates.py` precedent). UMAP/VAE deferred (UMAP breaks DET-1; VAE = reach).

**S1-refine notes.** AUC=1.000 made history deterministic of outcome (clinically unreal; would
make telemetry + R1 redundant in-silico). Fix: outcome is *sampled* from a sigmoid of frailty
(`_OUTCOME_K=5.0`), so frailty raises the *odds* of escalation, not the certainty; the AUC is
scored against an observable `comorbidity_index` (= observed event density + measurement noise,
σ=3), never the latent frailty — so it reflects what a real model could see. Determinism held by
keeping patient 0 free of frailty/outcome draws and making the comorbidity draw *trailing*
(verified patient-0 vitals identical across n=12 and n=50 → lead invariant). 60-seed lead sweep:
all ≥90 (min 90, median 145). 60-seed AUC: 0.59–0.89 (informational; seed=42 contract = 0.782,
comfortably centred). Re-run G1 after any `synth/forecast/risk` change (Hard Rule 4).

**S1 notes.** COPD-exacerbation scenario: latent frailty → Theograph event density (Poisson)
→ conditioned physiology + crisis propensity → labelled outcome (causal chain, so history is
learnable). Decoupling = loss of the fast homeostatic RR–SpO₂ co-fluctuation; measured by
*detrended* windowed coherence so the slow opposite trends don't masquerade as coupling. Lead
= onset (sustained coherence collapse) → first *sustained* single-signal breach (SpO₂<94);
silent window = onset → first instantaneous excursion (strictly in-range, trend adverse). Robust
≥90-min lead across 60 seeds (min 110), not just seed=42 — the index case is scripted, not gambled.
LOC: `scenario` 86 / `cohort` 87 / `gates` 143 / `__init__` 25 lines; `gates.py` exceeds the
~80-line target as the cohesive gate-helper hub (split would fragment the G1 measurement logic).
G1 sub-conditions must be re-checked after any `synth/forecast/risk` change (Hard Rule 4).
