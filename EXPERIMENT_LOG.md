# EXPERIMENT_LOG.md — STYX

Append-only. One row per slice when its gate passes (BUILD_MVP.md). The
AEGIS→threshold lead-time is logged every time `synth/`, `forecast/`, or `risk/`
changes (Hard Rule 4).

| Slice | Gate | Result | Lead-time (min) | Date |
|-------|------|--------|-----------------|------|
| S0 — scaffold | none | repo skeleton runs; `pytest` collects; `streamlit run app/app.py` launches | — | 2026-06-06 |
| S1 — synth (F5) | **G1 ✅** | determinism (seed=42 ×2 identical); dissociable silent window; genuine RR–SpO₂ decoupling; ≥12-patient cohort, outcome-from-history AUC=1.000; `tests/test_g1.py` 9/9 green; `notebooks/01_synthetic_fidelity` renders 3 panels | **160** (decoupling onset → first sustained breach, seed=42) | 2026-06-06 |
| S1-refine — outcome realism | **G1 ✅ (re-check)** | outcome now *stochastic* (`P=sigmoid(5·(frailty−½))`, sampled); AUC scored on noisy observed `comorbidity_index` (not frailty); learnability is a **band** [0.60, 0.90] not a floor; cohort default 50. **AUC seed=42 = 0.782** (was 1.000); mix 21 ESCALATED / 29 RECOVERED; determinism intact; silent window + lead unchanged; `pytest` 9/9; `ruff` clean | **160** (unchanged; patient-0 stream bit-identical, verified n=12≡n=50) | 2026-06-06 |

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
