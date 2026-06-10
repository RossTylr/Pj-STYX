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
| S4 — Theograph, CALLIOPE, ghost + patient page (F3, F9, F8) | **G4 ✅** | the integrated single-patient demo. *F3 Theograph:* `styx/theograph` materialises the per-channel event **counts** (`Patient.theograph`) into a dated, **recency-biased** timeline, seeded from `pid` (DET-1, **no `synth` touch** → G1 intact); dual-scale pure builders (lifelong **ribbon** in years + recent-days **detail strip**) + events threaded onto the trajectory (additive `events=` arg). *F8 CALLIOPE:* `styx/rationale` strict template over **read-only** risk accessors — `proximity_components` splits the proximity dot-product **exactly additively** per named axis (Σ = `_proximity`), plus `exceedance_per_vital`, `decoupling_drop`, `aegis_axis_departures`; headline names the **top-1 additive risk driver** (unambiguous, no tie-wobble), expand adds the AEGIS context; **closed 5-term vocabulary** `[oxygenation proximity, effort proximity, per-vital exceedance, breathing–oxygen decoupling, departure direction]` — never free text, never out-of-set. *F9 ghost:* the **stale-forecast** ghost = `project()` re-run at the AEGIS fire-index, faint dashed overlay on the realised path (additive `ghost=` arg; counterfactual ghost deferred — would touch `synth`). *Page:* `app/pages/01_patient.py` is **logic-free** (LYR-1) — all per-frame state from `styx/frame.py` (`PatientContext` built once + cheap `patient_frame` per scrub); map + waterline + cone + ghost + dual Theograph + raw-vitals + CALLIOPE + **SENTINEL** confidence (from conformal band width) under a scrub clock; `02_ward` stub for nav. **`tests/test_g4.py` 5/5** (determinism, vocab-closed, additive completeness, top-1 faithfulness, template-only). **Top-1 faithfulness 137/138 = 0.993** (floor 0.90) against the **archetype** oracle (the generating mechanism, blind to the attribution): coupled 93/93, silent_hypoxia 44/44, compensated 0/1 (its lone evaluable pre-breach point — compensated breaches fast, so almost no silent window; a near-tie at onset). Risk accessors touched `styx/risk` → **re-ran G1 6/6 + G2 3/3 + G3 4/4, full suite 21/21**; `ruff` clean; notebooks `04_rationale_faithfulness` + `05_walkthrough` (started) render; AppTest runs all pages no-exception | **210** (G3 re-check — risk accessors are read-only, score unchanged) | 2026-06-09 |
| S4.5 — patient-page polish (correctness · honesty · explainer · re-layout) | **G4 ✅ (6/6)** | a *rendering*-only pass (risk math untouched → **G1/G3 unaffected**), closing the post-breach landmine the 1425-min capture exposed. *Correctness:* `explain()` is now **regime-aware** — `Rationale` gains `regime` ("silent"|"crossed") + `additive` (top_k sums to risk). Post-breach the proximity overshoots the attractor and clips, so `additive` goes False and the renderer **suppresses the contributor panel** (it was showing 1.30 against a 1.00 risk); the headline verb switches to "**threshold crossed — in the {mode} mode**" (never "approaching" a mode already crashed through); the departure **σ clamps to words** above 8σ ("far beyond personal baseline", not "26.7σ"). *Default frame:* the clock lands on the **silent window** (`default_idx` ≈ nearest re-score to the forecast fire → risk 0.26, "approaching" — the money shot a threshold alarm can't show), not the post-crash end. *Honesty:* hid the Streamlit **Deploy** button (`.streamlit/config.toml` `[client] toolbarMode="minimal"`) that contradicted the "not a live deployment" banner. *Explainer layer:* new **pure-data** `styx/explain.py` (`Explainer` what/how/why per component; precedent — `styx/viz` already holds streamlit-free presentation) consumed by ⓘ `st.popover`s + an "Explain this page" toggle; `tests/test_explainer.py` 3/3 — **completeness** (registry == 9 COMPONENTS) + **honesty lint** (no "predicts the patient"/"diagnoses"/"learns the patient"/"real-time"; synthetic/replay/constructed anchors present). *Re-layout:* hero-first — slim banner → human title (enum demoted to a tag) → **status row** (Risk+verb · SENTINEL · **AEGIS lead promoted** "3.5 h before threshold") → **large trajectory hero** → waterline‖cone (ghost toggle moved under) → CALLIOPE (headline always; contributors collapsed, shown only when `additive`) → Theograph + raw-vitals collapsed. *Scrub:* signal **ticks** (AEGIS/forecast/breach, from `ctx.ticks`) + **jump buttons** + **step ▶** (no auto-play timer); all positions computed in `styx/frame.py` (LYR-1 — page computes nothing). **Verified via AppTest** at the breach boundary: final frame → "threshold crossed (risk 1.00)", contributor expander **absent**, σ shows "far beyond". Faithfulness **137/138 = 0.993** unchanged; full suite **25/25** (G1 6 · G2 3 · G3 4 · G4 6 · explainer 3 + smoke); `ruff` clean; notebooks 04/05 updated to v2 fields and render | **210** (unchanged — no risk-math touch; G1/G3 hold by construction) | 2026-06-09 |

| S5 — ward board + ECHO (F6, F10) | **Milestone ✅** | the 10-feature MVP runs end-to-end on the pre-baked scenario. *Surface-only* — new `styx/cohort` organises existing per-patient outputs and changes no maths, so **G1–G4 hold untouched** (re-run below). *F6 ward triage:* `build_cohort_context` fits embedding/basins/conformal-band **once** (vs `frame.build_context`'s per-patient refit — avoids O(N²)), then a cheap per-clock `ward_frame` → frozen `WardRow`s. **Time-to-escalation is banded** off the cone (upper-edge → point crossing = (soonest, central); `eta_confident` False when only the band edge crosses) — never a hard minute (UQ-1). Explicit **trichotomy** {escalated / escalating / no-forecast} as the primary sort bucket (no NaN sort); stable sort, pid tiebreak (DET-1). Flags: **silent-but-rising** (AEGIS fired by now ∧ risk<thr), **quietest** (lowest absolute exceedance), **new-low-history** (bottom-quartile Theograph density ∧ at-risk). *F10 ECHO:* deterministic **shape-aware** k-NN (k=3, self-excluded, pid tiebreak) over a fixed-length (32) index-resample of the 2-D state path — grounding, not prediction; archetype-share **63/63 = 1.000**. *Pages:* `02_ward.py` promoted (triage board + watchlist + **focus mode**), thin client on the **shared `scrub_pos` clock**; click→drill carries pid+t into `01_patient.py` (pre-set `patient_pick`+`scrub_pid` so its reset branch is skipped — verified). 3 new explainer entries (ward_board/watchlist/echo) + COMPONENTS, `test_explainer` 3/3 still green. *Milestone:* `tests/test_milestone.py` **4/4** (AppTest: ward+patient render no-exception, drill carries the clock, 10-feature presence; compute-side: patient-0 on the watchlist at the silent window, climbs rank 7→0 escalating→escalated under scrub, AEGIS<forecast<threshold ordered). **Labs decision — dropped** `labs_proxy` for a clean tight set (config `VITALS`/`NORMAL_RANGES` + `test_smoke` len 5→4 only; `scenario.py`/`cohort.py` untouched so the RNG draw order and the trailing comorbidity draw are preserved → bit-identical active streams). **Provably inert: G1/G2/G3 re-run identical** — `emb.mode` stays `constructed` (oxy r=1.000, effort r=0.995), decoupling lead 200, AUC 0.765, lead 210; the labs fork-flip contingency did **not** trigger. `notebooks/05_methods_story` renders: embedding legibility, **conformal coverage empirical mean 0.914 / min 0.900 (nominal 0.90)**, forecast reliability, lead distribution (cohort median 270, min 195), ECHO sanity. Full suite **29/29** (G1 6 · G2 3 · G3 4 · G4 6 · explainer 3 · smoke 3 · milestone 4); `ruff` clean (styx/app/tests/notebooks); all pages via AppTest no-exception. **Tag this commit as the 10-feature MVP.** | **210** (Milestone re-check — surface-only + inert labs drop; G1/G3 bit-identical) | 2026-06-09 |

**S5 notes.** *Surface, not maths — by construction.* F6/F10 only read the cohort's existing risk /
forecast / AEGIS / embedding outputs, so the Hard-Rule-4 invariants are untouched and the re-run is
identical, not merely "in band." The one move that *did* touch a shared file (the labs drop) was kept
deliberately surgical — config-only, leaving `generate_episode` still drawing (and returning) labs so
every RNG draw downstream lands in the same place; `VITALS`-keyed consumers (`_vital_matrix`,
`exceedance_per_vital`, `ward_frame`'s `max_exc`) simply stop iterating over it. The decisive check was
`emb.mode`: labs was PC1's nuisance axis, so removing it *could* have flipped the PCA fork legible and
moved the basins — it didn't (still `constructed`), and G2/G3 prove it. *ETA as a band, on purpose:* the
cone's point forecast often never reaches the line within the horizon even when the upper edge does
(patient 0 at the silent window: soonest ~70 min, central None → "~70+ min, low confidence") — reporting
a single minute there would manufacture confidence the model doesn't have, so the trichotomy + `eta_confident`
carry the honesty. *The default frame is intentionally escalated-free:* at the silent-window money shot
nobody is over the line (15 escalating + 35 stable, 21 on the watchlist); the escalated bucket appears
only as you scrub forward (idx 183: 9 escalated / 12 escalating / 29 stable) — which is the whole point,
the watchlist surfaces deterioration a threshold board still shows green. *Conformal band choice:* the
ward pools the band over the **whole** cohort (one band, marginal coverage) where `frame.py` uses
leave-one-out per patient — a deliberate cost/consistency trade; the methods notebook validates the
pooled band hits 0.914 empirical vs 0.90 nominal. *Promote-to-occult-archetype* (labs as a second hero)
is synth-touching and gate-cascading → correctly deferred past the tag, not part of this slice.

**S4.5 notes.** *The bug was rendering, not maths.* G4's 138 points were all sound — the additive
identity holds pre-breach (idx 150: 0.23+0.03+0 = 0.26 ✓); the captured frame was simply out-of-
distribution for the tested invariant (post-breach the proximity overshoots the attractor and the
per-axis term clips, so Σcontrib 1.30 ≠ risk 1.00). Fix is a `additive` flag gating the panel +
a regime-aware verb + a σ word-clamp — zero change to `risk_series`/accessors, so G1/G3 are
untouched by construction. *`regime` vs `additive` correctly decouple:* the verb flips at the
escalation threshold (risk ≥ 0.5, idx 183), but `additive` only goes False later, once the proximity
actually overshoots (idx ~285) — so contributions still render in the 183–~280 band where they
genuinely sum, and suppress only where they don't. *Explainer location (LYR-1 call):* landed in
`styx/explain.py` as pure, testable content (the text analogue of `styx/viz`), not `app/` — it
imports no streamlit and holds no behaviour, and the gate-style honesty lint mirrors
`test_vocabulary_is_closed`. *Scrub:* shipped jump+ticks+step (robust, demos predictably); the
`st.fragment` auto-play timer was declined to avoid rerun flakiness in a live room.

**S4 notes.** *Faithfulness oracle (the load-bearing choice).* A naïve vital-perturbation ablation
scored only 0.50 — it can't separate the two **co-driven** additive terms (perturbing RR removes
both its effort-*proximity* and its *exceedance*), so it's an unsound oracle. The right independent
ground truth is the synthetic **archetype** (the generating mechanism, which the attribution never
sees): silent-hypoxia→oxygenation, compensated→effort, coupled→either. Against it the named top-1
agrees 0.993 on the held-out silent window. The decomposition is **exactly additive** (the per-axis
proximity terms provably sum to `_proximity`), which is what makes top-1 unambiguous — the property
that keeps the rate off the tie-wobble cliff the plan flagged. *Compensated wrinkle:* its effort
trend breaches fast, so it has almost no pre-breach silent window — only one evaluable re-score in
the whole cohort, a near-tie at onset (oxygenation momentarily edges effort). Honest, immaterial to
the headline. *Ghost decision:* shipped the **stale-forecast** ghost (re-run from the AEGIS anchor),
not the PRD's no-intervention counterfactual — the latter needs a counterfactual stream from `synth`
(Hard Rule 4/6), deferred. *Completeness scope:* contributions reconstruct risk on the silent window
(risk ≥ 0.1, pre-breach); post-breach the proximity **overshoots** the attractor and the term clips,
so the additive identity is asserted only where neither term saturates — the regime CALLIOPE exists
to explain.

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
