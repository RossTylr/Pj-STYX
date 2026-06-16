# STYX — Methodology & Validation (model explainer report)

**Version:** rev2, 2026-06-14 · seed = 42 · A2 re-score cadence = 15 sim-min
**Changelog:** rev2 — added §3.1 (state-space embedding, the F1 substrate); added the "breach"
disambiguation note to §5; renumbered §3.2–§3.6 accordingly.
**Status:** grounded in source. Every formula, threshold and window below is transcribed
from the cited file; every result number is reproduced from a live `seed=42` run (see
[§7 Reproducing the numbers](#7-reproducing-the-numbers)), not from memory. Where a logged
figure in `EXPERIMENT_LOG.md` has since drifted, the **current measured value** is given and
the drift is flagged.

> **Honesty preamble (CLAUDE.md Rules 6–8).** STYX is a **replay of synthetic data** — no real
> patient data, no live or streaming deployment. The clinical condition modelled is **acute
> respiratory infection** (pneumonia / COVID-style *happy hypoxia*), scored against **NEWS2
> Scale 1** — deliberately *not* COPD. Two of the headline claims below — the AEGIS→threshold
> lead and the early-warning→NEWS2 lead — are properties of one scripted scenario at one seed.
> The cohort-outcome AUC and the "saturation" finding are **in-sample** measurements on one
> synthetic cohort: construct validity (does the detector recover what the generator scripted?),
> never ward performance.

---

## 1. The headline, and the one caveat

| Claim | Value (seed=42) | Where it comes from |
|---|---|---|
| **Early-warning lead over NEWS2** | **305 sim-min** (AEGIS 705 → NEWS2 red 1010) | §5, `readouts.news2_complete_crossing` |
| **AEGIS → absolute-risk-threshold lead** | **210 sim-min** (AEGIS 705 → F4 threshold 915) | §5, gate G3 |
| **Decoupling → first breach lead** | **200 sim-min** (onset 590 → breach 790) | §5, gate G1 |
| **Cohort outcome AUC (history → escalation)** | **0.765**, in band [0.60, 0.90] | §6.5 |
| **CALLIOPE top-1 faithfulness** | **0.968** (395/408, per-sample), floor 0.90 | §6.4 |
| **Conformal cone coverage** | **0.915** empirical (nominal 0.90) | §6.6 |
| **Determinism digest** | `c9380e9c…860b1d9` (build ×2 identical) | §6.7 |

**The caveat, stated up front (§6.6):** at the silent-window demo frame the telemetry panel
already **saturates** the in-sample outcome AUC at **1.000**. Care history adds **no positive
predictive lift** on top of it. This is a construct artifact of the synthetic engine (frailty
was baked in when the outcome was sampled), and it is *why* the history reach (R1) is framed as
**descriptive**, not predictive.

---

## 2. Data — the synthetic engine (`styx/synth/`)

A single seed tree drives the whole cohort. `build_cohort(seed=42)` spawns one independent child
`np.random.Generator` per patient (`styx/synth/cohort.py:118`), so the cohort is reproducible
bit-for-bit (DET-1) and `Cohort.equals` is exact array equality.

### 2.1 Replay grid, baselines, noise

- **Grid:** `DT_MIN = 5` sim-min, `N_SAMPLES = 288` → a 24 h stay (last sample 1435 sim-min).
  `styx/synth/scenario.py:26-27`.
- **Personal baselines** (`scenario.py:35`): RR 16, SpO₂ 97, HR 78, temp 36.8, labs_proxy 0.3.
- **Measurement noise:** every sample carries `N(0, 0.12)` (`NOISE`, `scenario.py:53`) — small by
  design, so it cannot trip a spurious early breach.
- **Sampled vital set (SIG-1):** STYX's *model* reads four wearable streams,
  `VITALS = (RR, SpO2, HR, temp)` (`styx/config.py:52`). `labs_proxy` is still generated but was
  **dropped from `VITALS` at the MVP milestone** (zero embedding loading, never the worst-vital
  exceedance — `EXPERIMENT_LOG.md` S5).

### 2.2 The physics: coupling, then decoupling

In the **stable regime** RR and SpO₂ share a fast homeostatic anti-phase co-oscillation on a
60-min cycle (`scenario.py:38-40, 93, 97-98`):

```
d    = sin(2π·t / 60)
SpO2 = 97 − 1.5·d + ε          # A_SPO2 = 1.5
RR   = 16 + 1.2·d + ε          # B_RR   = 1.2
```

so windowed RR–SpO₂ coherence is high (`r → −1`). At **decoupling onset** that shared drive is
replaced by *independent* fast fluctuation (`DECOUP_FAST_SPO2 = 0.4`, `DECOUP_FAST_RR = 0.35`,
`scenario.py:43-44, 109-110`) plus each signal's own slow trend — coherence collapses while both
signals are **still in range** (the silent window).

### 2.3 Archetypes — dissociating oxygenation from effort

Post-onset slopes are scaled per archetype by `_ARCHETYPE_SLOPES` — a `(SpO₂, RR, HR)` multiplier
triple (`scenario.py:66-70`):

| Archetype | (SpO₂, RR, HR) mult. | Shape |
|---|---|---|
| `COUPLED` | (1.0, 1.0, 1.0) | both deteriorate — the diagonal |
| `SILENT_HYPOXIA` | (1.0, **0.0**, 0.0) | SpO₂ falls, **effort flat** (the AEGIS phenomenon) |
| `COMPENSATED` | (0.3, 2.0, 1.5) | effort climbs, SpO₂ holds |

The post-onset trajectory (`scenario.py:106-117`):

```
dec_t      = max(0, t − onset_min)
SpO2_post  = 97 + severity · f_spo2 · SLOPE_SPO2 · dec_t + indep_spo2
RR_post    = 16 + severity · f_rr   · SLOPE_RR   · dec_t + indep_rr
SLOPE_SPO2 = −3.0 / 240 = −0.0125 %/sim-min      (scenario.py:47)
SLOPE_RR   = +3.0 / 240 = +0.0125 /sim-min        (scenario.py:48)
```

For **silent hypoxia**, `f_rr = 0` makes RR flat (baseline + independent noise only), while SpO₂
declines linearly ~97 → 94 over the 240-min lead window. This is the construction the whole demo
rests on: **oxygen falling with breathing effort flat**, every vital still inside its NEWS2 band.

### 2.4 Severity, onset, and per-patient diversity

`generate_episode(rng, *, archetype, severity=1.0, onset_min=540)` (`scenario.py:78-84`):

- **`severity`** scales *all* post-onset slope rates. Drawn per escalating patient from
  `U[0.85, 1.35]` (`cohort.py:36, 140`).
- **`onset_min`** is the decoupling onset; the labs clock keeps a fixed offset from it. Drawn from
  `U[480, 660]` (`cohort.py:37, 141`) — floored ≫ the 120-min AEGIS baseline and capped so SpO₂
  still breaches in-stay.
- Diversity is drawn from an **independent vector-seeded** generator `(seed, pid, 7)`
  (`cohort.py:139`) so theograph / comorbidity / nurse-obs draws stay bit-identical to the
  pre-diversity cohort — the outcome AUC is provably unaffected.

### 2.5 Cohort assembly and the outcome label

`build_cohort(seed=42, n_patients=50)` (`cohort.py:111`). Per patient (`cohort.py:120-148`):

- **Patient 0 is the scripted index case:** frailty 0.85, `SILENT_HYPOXIA`, severity 1.0,
  onset 540 — its draw order is preserved so its silent window and leads are bit-identical to the
  validated baseline (`cohort.py:121-124`).
- **Every other patient:** `frailty ~ U(0.1, 0.9)`; the outcome is **sampled, not thresholded** —
  `P(adverse) = sigmoid(5·(frailty − 0.5))` (`_OUTCOME_K = 5`, `cohort.py:127`). If adverse, the
  archetype is drawn uniformly from `{SILENT_HYPOXIA, COMPENSATED, COUPLED}`; else `STABLE`
  (recovered). So frailty raises the *odds* of escalation — history predicts outcome better than
  chance but never perfectly (the G1 band).
- **Theograph history:** per channel, `count ~ Poisson(1 + 8·frailty)` over 6 channels
  (`cohort.py:108`). The **observable** proxy a model actually sees is
  `comorbidity_index = Σ(theograph) + N(0, 3)` (`cohort.py:144`) — event density plus noise,
  *not* latent frailty.

### 2.6 Nurse observations (comparator-only)

`generate_nurse_obs` (`styx/synth/observations.py:48-60`) produces systolic BP and ACVPU —
the two NEWS2 parameters a wearable cannot stream. BP baseline `U[112, 138]`, jitter `σ=3`,
floored at 114 (so it stays in NEWS2 band 0), recorded 4-hourly (`NURSE_OBS_CADENCE_MIN = 240`)
and step-held; ACVPU is 0 (Alert) throughout. **These feed only the NEWS2 comparator, never
STYX's model** — they are deliberately not in `VITALS`, and a *trailing* draw so they cannot shift
any vital stream (DET-1).

---

## 3. Model — the five mechanisms

Each subsection gives the plain-language idea, then the exact computation.

### 3.1 State-space embedding — the 2-D substrate (F1)

*The plane AEGIS, the cone and F4 risk all read: a deterministic linear map from the four
wearable vitals to a named oxygenation × effort plane, with a learned stability basin and one
crisis attractor per archetype.*

`styx/state/embedding.py`, constructs in `styx/state/constructs.py`:

- **Standardise, then project.** The map standardises each of the four `VITALS` channels —
  `(x − mean) / std` over every sample of every patient (`embedding.py:87-90`) — then applies a
  2×4 loading matrix to reach 2-D coordinates (`Embedding.transform`, `embedding.py:50-52`).
  Standardisation is load-bearing: SpO₂ (94–100), RR (12–20) and HR (60–100) live on different
  raw scales, so an un-standardised axis would just track the largest-variance vital.
- **PCA-first, with a legibility fork.** `fit_embedding` fits a full-SVD PCA (sklearn, no RNG →
  DET-1), labels each axis by the construct it best correlates with, orients it to +corr, and
  **keeps PCA only if both axes clear the G2 bar**; otherwise it falls back to hand-built
  constructed axes (`embedding.py:84-110`). **On this cohort PCA is illegible and the fork falls
  back to the constructed map** (`EXPERIMENT_LOG.md` S2-refit/S5).
- **The constructed axes** (`_constructed`, `embedding.py:75-81`), in standardised space:
  - **oxygenation** (axis 0) = SpO₂, loading 1.0;
  - **effort** (axis 1) = RR and HR, each loading 1/√2.
- **The named constructs** these axes are scored against (`constructs.py:16-30`): oxygenation =
  SpO₂ centred on its normal band (0 at mid-range, ±1 at the edges); effort =
  `norm(RR) + norm(HR)` — deterministic, config-derived from `NORMAL_RANGES`, no fitted
  parameters. That the latent axes track these two *distinct* constructs at `|r| ≥ 0.60` is what
  **gate G2 (§6.2)** proves; this report does not restate it.
- **Basin and attractors** (`learn_basins`, `embedding.py:123-157`) — the geometry §3.4's
  proximity measures toward:
  - **basin centre** = the mean latent position of all **in-range** samples across the cohort
    (radius = per-axis std);
  - **one crisis attractor per escalating archetype** (`SILENT_HYPOXIA`, `COMPENSATED`,
    `COUPLED`) — each the empirical mean of that archetype's **breach samples** (out-of-range
    *and* outcome `ESCALATED`). Grouping by archetype (a fixed-order tuple, no clustering RNG)
    keeps it deterministic. One mode per archetype is deliberate: a single averaged attractor
    would sit in the effort-led region, and the silent-hypoxia case — which drifts on
    oxygenation — would never register risk.
  - `nearest_attractor(point)` picks the closest mode by Euclidean distance
    (`embedding.py:70-72`) — the mode F4 proximity (§3.4) travels toward.

### 3.2 AEGIS — personal-baseline silent-deterioration flag (F7)

*The earliest of the three signals: it learns each patient's own normal, then fires on a sustained
departure from it — while the patient still looks fine to a population threshold.*

`styx/risk/aegis.py`, constants in `styx/config.py:40-43`:

1. **Trend-smooth** the 2-D state position with a causal trailing mean over
   `AEGIS_SMOOTH_SAMPLES = 12` (60 sim-min) — strips the fast homeostatic swing so it doesn't
   inflate the baseline σ (`aegis.py:25-32, 42`).
2. **Learn the baseline** μ, σ over the first `AEGIS_BASELINE_SAMPLES = 24` smoothed samples
   (120 sim-min, well before onset) per axis (`aegis.py:43-46`).
3. **Departure signal** = `|(smooth − μ) / σ|` per axis, then the **max over both named axes**
   (`aegis.py:47, 53`) — so AEGIS generalises to the effort-led deteriorator, not just hypoxia.
4. **Fire** when the signal exceeds `AEGIS_K = 3.0` σ for `AEGIS_SUSTAIN = 3` consecutive samples
   (15 sim-min) (`aegis.py:75`); serving reports the first re-score index at/after that confirm
   point (`aegis.py:80-83`).

### 3.3 Forecast cone — short-horizon risk projection with conformal bands (F2)

*A least-squares trend on the recent risk, projected forward, widened by an honest empirical band.*

`styx/forecast/__init__.py`, constants `styx/config.py:28-36`:

- **Point path:** degree-1 least-squares fit on the trailing `FORECAST_WINDOW = 12` samples
  (60 sim-min), projected `FORECAST_HORIZON = 24` steps (120 sim-min) ahead, clipped to [0, 1]
  (`forecast.py:47-68`).
- **Conformal band half-width** at each horizon `k` = the `(1 − α)` quantile of pooled
  `|actual − predicted|` residuals from trailing fits across the calibration cohort
  (split-conformal, leave-the-index-patient-out; `forecast.py:71-96`). With
  `CONFORMAL_ALPHA = 0.1` this is the **90th percentile** of residuals — coverage is *marginal*,
  not per-patient (stated honestly in the module docstring).
- **"Forecast fires"** when the cone's **upper edge** reaches the escalation threshold for
  `FORECAST_SUSTAIN = 3` consecutive re-scores (`forecast.py:99-125`); re-scores before a full
  window exists are skipped. The sustain requirement is what stops the wide early cone from firing
  before AEGIS on noise.

### 3.4 F4 risk — continuous waterline + absolute trigger

*Risk is a gradient on [0, 1] that rises during the silent window but crosses the line only at breach.*

`styx/risk/score.py:54-56`:

```
risk = clip( 0.5 · proximity + 0.5 · exceedance , 0, 1 )
```

- **Proximity** (`score.py:27-39`): the fraction of the basin→nearest-attractor distance the
  patient has travelled in the 2-D state space —
  `proximity = dot(pos − b, d̂) / ‖d‖`, where `d = (nearest attractor − basin centre)`, clipped to
  [0, 1]. It rises *early* as the trajectory drifts toward a crisis mode. Because it is weighted
  0.5, **proximity alone caps the risk at 0.5**.
- **Exceedance** (`score.py:42-51`): the worst-vital absolute range-exceedance, normalised by band
  width — `max(0, (low − x)/w, (x − high)/w)` over `VITALS`, clipped to [0, 1]. It is **strictly
  zero while every vital is in range**.
- **Therefore** risk can only exceed the `risk_escalation = 0.5` threshold (`config.py:107`) once a
  vital actually leaves its range — i.e. **at the breach**. The trigger fires *last* and cannot
  collapse onto AEGIS. Normal ranges: RR 12–20, SpO₂ 94–100, HR 60–100, temp 36–37.8
  (`config.py:95-100`).

### 3.5 Decoupling — RR–SpO₂ coherence collapse

*Homeostatic coupling lives in the fast anti-phase co-fluctuation; when it fails the residuals go
independent and coherence drops — before any single signal breaches.*

`styx/synth/gates.py:19-59`:

- **Coherence** = trailing rolling **Pearson r of *detrended* RR vs SpO₂** over
  `COHERENCE_WINDOW = 12` (60 sim-min) (`gates.py:30-45`). Detrending each window removes the slow
  drift so coherence reflects fast co-fluctuation, not opposite deterioration trends
  (`gates.py:24-27`).
- **Onset rule** (`gates.py:48-59`): the first sample where `|coherence|` falls below
  `(baseline − 0.4)` for `_SUSTAIN = 2` consecutive windows, where `baseline` is the median
  coherence over the first third of the stay (`_DROP_K = 0.4`).
- **Lead** (`gates.py:91-96`) = `(breach − onset) · 5 sim-min`, where breach is the first
  *sustained* (≥2-sample) single-signal range excursion (`gates.py:62-77`).

### 3.6 CALLIOPE — strict-template rationale over the real top-k (F8)

*Never free text, never a signal outside a closed vocabulary, never a phenomenon the model didn't
attribute (CLAUDE.md Rule 5).*

`styx/rationale/calliope.py:110-139`. The "model's real top-k" is the ranking of **exactly three
risk terms**, each one a real summand of the F4 risk (`calliope.py:116-121`):

```
risk_terms = [
  ("oxygenation proximity", 0.5 · proximity_component_oxy[idx]),
  ("effort proximity",      0.5 · proximity_component_effort[idx]),
  ("per-vital exceedance",  0.5 · worst_vital_exceedance[idx]),
]
top_k = sort by (−value, vocabulary order)
```

The proximity term splits **exactly additively** per named axis (the two components sum to
`_proximity`, `score.py:65-77`), so the top-1 driver is unambiguous and the contributions
reconstruct the displayed risk (gate G4 additive completeness). The headline names the top-1
driver; the expand surfaces AEGIS context (departure direction ≥ 1σ, breathing–oxygen decoupling
≥ 0.05) drawn from the same real signals. The vocabulary is a **closed 5-term set**
(`calliope.py:28-34`); the rationale is **regime-aware** — once `risk ≥ 0.5` it switches to
"threshold crossed", suppresses the (now non-summing) contributor split, and clamps the σ to words.

---

## 4. Comparator — NEWS2 Scale 1 (`styx/readouts.py`)

A read-only, named-standard baseline. STYX wins no frequency advantage: NEWS2 scores the wearable
vitals on the **same telemetry grid** STYX sees (`readouts.py:60-63`).

**Scale-1 band → score** (`readouts.py:74-87, 138-145`):

| Param | Bands (score) |
|---|---|
| RR | ≤8 (3) · ≤11 (1) · ≤20 (0) · ≤24 (2) · >24 (3) |
| SpO₂ (Scale 1) | ≤91 (3) · ≤93 (2) · ≤95 (1) · >95 (0) |
| HR | ≤40 (3) · ≤50 (1) · ≤90 (0) · ≤110 (1) · ≤130 (2) · >130 (3) |
| Temp °C | ≤35 (3) · ≤36 (1) · ≤38 (0) · ≤39 (1) · >39 (2) |
| Systolic BP (nurse) | ≤90 (3) · ≤100 (2) · ≤110 (1) · ≤219 (0) · >219 (3) |
| ACVPU (nurse) | Alert=0 (0) · any other level (3) |

**Escalation rule** (`_news2_escalates`, `readouts.py:103-110`): the protocol's *earliest-of* —
fires where the **aggregate ≥ `NEWS2_TRIGGER` (5)** OR **any single parameter ≥ `NEWS2_RED` (3)**.
`_first_crossing_min` (`readouts.py:113-116`) returns the first sim-minute that rule fires.

**Why the single-param red is load-bearing here:** through the silent window the aggregate
**peaks at 3 and never reaches 5**, so an aggregate-only trigger would never fire and the
comparison would be vacuous. The binding prompt is the **SpO₂ ≤ 91 red at 1010 sim-min**
(`test_observations.py:65-84`). Because the nurse params are preserved (BP band 0, ACVPU Alert),
the **complete (6-of-7) NEWS2 equals the partial (4-param)** in this scenario — both fire at 1010.

---

## 5. The cascade, on the silent case (seed=42)

Re-scoring patient 0 on the A2 cadence (15 sim-min) produces four events, in order, with
clear separation (live values, `styx/anticipation.py::fire_times`):

| Marker | sim-min | Mechanism |
|---|---|---|
| **Decoupling onset** | **590** | RR–SpO₂ coherence collapse (§3.5) |
| **AEGIS fires** | **705** | personal-baseline departure > 3σ sustained (§3.2) |
| **Forecast fires** | **750** | conformal cone upper edge reaches 0.5 (§3.3) |
| **F4 threshold** | **915** | absolute risk ≥ 0.5 — the breach (§3.4) |
| **NEWS2 red** | **1010** | SpO₂ ≤ 91 single-param red (§4) |

- **AEGIS → threshold lead = 210 sim-min** (915 − 705) — the G3 headline, regression-guarded at
  floor 180.
- **AEGIS → NEWS2 lead = 305 sim-min** (1010 − 705) — the early-warning-vs-standard-of-care number.
- **Decoupling → breach lead = 200 sim-min** (onset 590 → first sustained single-signal breach 790)
  — the G1 number.
- **Cadence preserves the lead:** raw per-sample re-score gives 700 / 730 / 910 → lead still 210
  (gate G3 requires `|at-cadence − raw| ≤ 15`).

**A note on "breach."** Two precise events share the word and must not be conflated:
the **single-signal range excursion** — the first sim-minute one vital sustains a move
outside its NEWS2 range (**790**, the reference for the G1 decoupling lead, §3.5) — and
the **F4 absolute-risk threshold** — risk ≥ 0.5 (**915**, the cascade breach, §3.4). The
gap is real and ordered: a single vital (SpO₂) nudges out of its tighter STYX range at 790
before the *combined* risk crosses the line at 915, and well before NEWS2's deeper red
(SpO₂ ≤ 91) at 1010.

---

## 6. Validation — the credibility core

Gate thresholds live in `styx/config.py`; the tests assert against them so the doc and the code
cannot drift. All gate tests pass at `seed=42` (27/27 across G1–G4 + baseline + observations,
verified — §7).

### 6.1 G1 — synthetic fidelity (`tests/test_g1.py`, helpers `styx/synth/gates.py`)

No fallback: this is the root gate. One assertion per sub-condition:

- determinism — `build_cohort(42).equals(build_cohort(42))`;
- cohort ≥ 12 (actual 50);
- `has_silent_window(silent_case)` — a window from decoupling onset to first excursion where every
  vital is in range yet SpO₂ slope < 0 (`gates.py:102-124`);
- `decoupling_lead_min ≥ DECOUPLING_LEAD_MIN (90)` — **actual 200**;
- `cohort_outcome_auc ∈ OUTCOME_AUC_BAND [0.60, 0.90]` — **actual 0.765**.

### 6.2 G2 — state legibility (`tests/test_g2.py`, helpers `styx/state/gates.py`)

- deterministic coordinates;
- both latent axes track distinct constructs at `|r| ≥ LEGIBILITY_THRESHOLD (0.60)` — logged
  oxygenation r = 1.000, effort r = 0.995 (`EXPERIMENT_LOG.md` S2-refit/S5);
- the silent case drifts basin → attractor (`trajectory_drift > 0`; logged +0.69, +1.10 after the
  per-archetype attractor refit).

### 6.3 G3 — anticipation dissociation (`tests/test_g3.py`, `styx/anticipation.py`)

- deterministic fire times;
- `FireTimes.ordered` — AEGIS < forecast < threshold;
- `aegis_threshold_lead_min ≥ AEGIS_LEAD_FLOOR_MIN (180)` — **actual 210** (the floor is a
  regression guard set just below the measured lead, *not* an adequacy claim);
- cadence preserves the lead within one re-score interval.

### 6.4 G4 — rationale faithfulness (`tests/test_g4.py`, `styx/rationale/calliope.py`)

- vocabulary closed (no rationale names an out-of-set signal);
- **additive completeness** — `top_k` sums to the displayed risk to within 1e-9 over the silent
  window;
- **top-1 faithfulness ≥ `G4_FAITHFULNESS_FLOOR` (0.90)** against an archetype oracle independent
  of the attribution. CALLIOPE names the *model's* own top term by construction; this metric tests
  whether that model-chosen driver matches the **generating archetype** — i.e. it checks the model's
  risk *decomposition*, surfaced through CALLIOPE, not the narration. **Per-sample basis: 0.968
  (395/408)** — silent_hypoxia 159/159, coupled 236/236, **compensated 0/13**. The 0/13 is
  systematic, not a tie: compensated breaches fast, so its only evaluable pre-breach windows are the
  earliest (risk just past 0.1), where the constructed effort axis has not separated and the
  oxygenation-proximity term dominates — a model construct-validity limit on one archetype, flagged
  not closed. **Basis + re-baseline:** the earlier **137/138 = 0.993** was the S4.5 cohort; the S7
  diversification moved the window counts, and on the current cohort `test_g4`'s **cadence-grid** sweep
  reads **115/115 = 1.000** — because compensated has *no* cadence window, the gate's basis hides the
  one failing archetype, so the **per-sample** figure is reported as the honest one;
- template-only headline, and a post-breach regime switch.

### 6.5 Cohort outcome AUC (`styx/synth/gates.py:127-136`)

In-sample ROC-AUC predicting `ESCALATED` from the **observable** `comorbidity_index` (event-density
proxy + noise) via logistic regression — **never the latent frailty that set the outcome**, so the
AUC is what a real model could see, not a tautology. **Actual 0.765** (mix 21 escalated / 29
recovered). The synthetic engine tunes `_OUTCOME_K` precisely so this lands in the band rather than
at a giveaway 1.0.

### 6.6 The saturation finding (`notebooks/06_cohort_signal.py`) — the caveat

At the silent-window demo frame (`di`, t = 750 sim-min) we compare in-sample outcome AUC from three
feature sets (live `seed=42`):

| Feature set | AUC |
|---|---|
| History only (`comorbidity_index`) | **0.765** |
| Telemetry only (risk snapshot + AEGIS-fired flag + risk slope) | **1.000** (saturates) |
| Combined | **0.984** |
| **Marginal value (combined − telemetry)** | **−0.016** |

The telemetry panel already **saturates** the in-sample AUC — by the silent-window frame the
scripted escalators' risk has begun separating, so the snapshot already encodes who escalates.
History adds **no positive marginal predictive value**; the combined number even dips slightly
(an in-sample logistic-regression artifact of adding a weaker feature). **This is why the history
reach (R1) is descriptive, not predictive** — history *explains* baseline / basin / hazard, it does
not improve the prediction.

> ⚠ **Drift flagged:** `EXPERIMENT_LOG.md` S5.5 records this marginal as `+0.000`. The 2026-06-14
> demo-data enrichment (per-escalator severity/onset jitter) shifted the escalator risk streams, so
> the **current** measured marginal is **−0.016**. The conclusion is unchanged (telemetry saturates;
> history adds no lift); only the exact number moved.

### 6.7 Determinism digest (`tests/test_baseline.py`)

`pipeline_digest` is a SHA-256 over the whole cohort in pid order — for each patient: the `pid`,
then each `VITALS` array's bytes, then the sorted `"channel:count"` theograph pairs, then the risk
waterline `cctx.risk[pid]` bytes (`test_baseline.py:17-28`). Building twice at `seed=42` yields an
identical digest.

- **Current digest:** `c9380e9cf7c134a82f2a45dd15c9769129540eee3c7d5db5aa54dc587860b1d9`
  (recorded `test_observations.py:30`, verified live).
- ⚠ **Drift flagged:** most `EXPERIMENT_LOG.md` rows show `9ea38949…336a5347`. That was the baseline
  through S7; the **2026-06-14** enrichment intentionally changed the escalator vital streams (and
  hence their risk), moving the digest to `c9380e9c…`. Patient 0's stream and all theograph counts
  are unchanged — the nurse-obs routing proof (comparator-only) still holds because nurse obs are
  not in the digest.

---

## 7. Reproducing the numbers

All values in this report were produced at `seed=42` and can be regenerated:

```bash
# Gates + determinism + comparator (27 tests; ~2 min)
.venv/bin/python -m pytest tests/test_g1.py tests/test_g2.py tests/test_g3.py \
    tests/test_g4.py tests/test_baseline.py tests/test_observations.py -q

# The cascade / leads / AUC / digest, printed directly
.venv/bin/python -c "
from styx.synth import build_cohort, cohort_outcome_auc, decoupling_lead_min
from styx.anticipation import fire_times
from styx.readouts import news2_complete_crossing
c = build_cohort(seed=42); p = c.silent_case(); ft = fire_times(c, p)
print('AUC', round(cohort_outcome_auc(c),4), '| decoupling lead', decoupling_lead_min(p))
print('AEGIS/forecast/threshold', ft.aegis_min, ft.forecast_min, ft.threshold_min)
print('AEGIS->threshold', ft.aegis_threshold_lead_min, '| AEGIS->NEWS2', news2_complete_crossing(p)-ft.aegis_min)
"

# The saturation finding
.venv/bin/python notebooks/06_cohort_signal.py
```

Values are seed=42, A2 re-score cadence 15 sim-min. Coverage (0.915, `:.3f` of 0.91489) is computed
live in `notebooks/05_methods_story` and `notebooks/10_how_styx_predicts` §6 (the earlier 0.914 was
a truncation of the same figure).

---

## 8. Limits (read these before quoting any number)

- **Replay of synthetic data.** No real patient data; not a live or streaming deployment.
- **In-sample AUC.** The 0.765 and the saturation AUCs are scored in-sample on one synthetic
  cohort — construct validity, not held-out ward performance.
- **Saturation is a construct artifact.** Telemetry separates escalators in-sample because the
  engine scripted them; it bounds R1's *framing*, it is not a real-ward result.
- **Scale 1 only.** Modelled condition is acute respiratory infection (happy hypoxia), scored on
  NEWS2 Scale 1. STYX's Scale-1 shading is clinically wrong for a Scale-2 (e.g. COPD) patient.
- **No oxygen-uplift flag.** The binary +2 O₂-supplementation score is not modelled — the basis of
  the silent-hypoxia gap, but also a NEWS2 parameter the comparator here does not carry.
- **Marginal conformal coverage.** The cone's 0.915 coverage is pooled across the calibration
  cohort, not a per-patient guarantee.
- **One scenario, one seed.** The 210 / 305 sim-min leads are properties of the scripted silent
  case at seed=42, not a general performance claim.

---

*Cross-references: `BUILD_MVP.md` (slice/gate order), `docs/STYX_PRD.md` (requirements),
`docs/MAAFI_STYX_verdict.md` (feature tiers / gates), `docs/ARCH_REDTEAM_STYX.md` (serving
architecture), `EXPERIMENT_LOG.md` (per-slice log), `app/pages/04_clinical_basis.py` (the
clinician-facing scope/limits surface).*
