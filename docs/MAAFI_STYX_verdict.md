# MAAFI verdict — STYX feature set

**Multi-Agent Adversarial Feature Integration, applied to STYX PRD v0.2.**

| | |
|---|---|
| **Date** | 3 June 2026 |
| **Candidates** | 15 — F1–F11 (core) + R1–R4 (reach). Appendix-A items out of scope (already deferred). |
| **Protocol** | 5 agents (Forward · Backward · Cross · Red Team · Arbiter); intrinsic/surface split; 5-axis arbiter rubric. |
| **Feeds** | `BUILD_MVP.md` (wire order, §7) and the three go/no-go gates (§9). |

This run *stress-tests* the PRD's feature decisions rather than restating them. Where it confirms the PRD it says so; where it revises, see the **Δ-from-PRD** notes.

---

## 0. Rubric

Arbiter scores each feature on five axes. The value axis is split so a mechanism (intrinsic) outranks an analysis tool (surface) when they compete — a beautiful view over a wrong model is precisely wrong.

| Axis | Weight | Scored on |
|---|---|---|
| Mechanistic fidelity | 0.25 | intrinsic features only (surface = 0) |
| Analytical utility | 0.15 | surface features only (intrinsic = 0) |
| Parsimony | 0.20 | all — does it earn its complexity / LOC? |
| Robustness | 0.20 | all — does it survive failure / edge cases / degrade gracefully? |
| Readiness | 0.20 | all — buildable now, dependencies met? |

Intrinsic ceiling = 0.85; surface ceiling = 0.75. The asymmetry is the point.

---

## 1. Intrinsic / surface classification

| Feature | Layer | Why |
|---|---|---|
| F5 synthetic engine | **Intrinsic** | The generative model of the patient. Its fidelity propagates everywhere — the root. |
| F1 latent trajectory | **Intrinsic** | The state representation. The hero computation; everything hangs off it. |
| F2 forecast cone | **Intrinsic** | The forecaster — a computed prediction. (Cone *rendering* is surface; the forecast is not.) |
| F4 risk + escalation | **Intrinsic** | A computed risk score + escalation decision. |
| F7 AEGIS | **Intrinsic** | A detection mechanism (personal baseline + change-point) producing a new signal. |
| R1 history-as-prior | **Intrinsic** | Conditions the model's prior / hazard. Definitionally intrinsic. |
| R2 CHARON | **Intrinsic** | A generative point-process forecast model. |
| R3 CADUCEUS | **Intrinsic** | A model that learns the dependency graph and predicts. |
| F3 Theograph overlay | Surface | Observes existing outputs (events on the trajectory). Engine runs identically without it. |
| F6 ward board | Surface | Organises/observes per-patient outputs across a cohort. |
| F8 CALLIOPE | Surface | Translates existing risk drivers into text. Changes presentation, not computation. |
| F9 ghost trail | Surface | A derived overlay (re-runs F2 from an earlier anchor). As specced, not a new model. |
| F10 ECHO | Surface | Retrieves + overlays similar past cases for grounding. |
| F11 workflow touches | Surface | Pure UX (since-last-review, review-ack). |
| R4 HERMES | Surface | Re-presents the same state model for carers (built on F8). |

**Δ-from-PRD.** CALLIOPE (F8) was tagged P0 as if foundational. It is **surface** — P0 only on cheap-high-leverage grounds, never on mechanistic priority. Consequence in §6 (conflict 5) and §9 (gate 3).

Spine is intrinsic (F5, F1, F2, F4, F7); reaches split (R1/R2/R3 intrinsic, R4 surface); the cheap promote-now wins are mostly surface — exactly what the rubric will keep in their place.

---

## 2. Forward agent — greedy addition

Start empty; add the highest marginal-value feature whose dependencies are met.

Root → spine → cheap multipliers:
`F5 → F1 → F2 → F4 → F7 → F3 → F8 → F6 → F9 → F10`

The greedy sweep halts naturally at **10 features** — the canonical MAAFI MVP size. F11 and the reaches are the next greedy adds but each costs more per marginal point. Forward's read: the first eight (`F5 … F6`) are the value core; F9/F10 are cheap top-ups.

---

## 3. Backward agent — ablation

Start from all 15; remove whatever costs least to lose.

- **Prune first (near-zero demo cost):** F11 (invisible in a 3-min demo) → defer to pilot.
- **Prunable (low cost, cheap to keep):** F9, F10 — wow/trust top-ups, not load-bearing. The MVP's contingency cuts.
- **Prunable-with-cost:** R4 (loses the only Challenge-2 bridge), R2 (loses novelty), R3 (loses the highest-ceiling line but it has a fallback).
- **Near-essential surface:** F3 (losing it kills the *integration* thesis), F6 (losing it kills the *dashboard* framing the brief stresses).
- **Irreducible — removal breaks the value:** F5, F1, F2, F4, F7. Remove any one and there is no defensible demo.

Backward's read: the irreducible set is `{F5, F1, F2, F4, F7}`; `{F3, F6}` are near-essential; everything else is reach or contingency.

---

## 4. Cross agent — synergy / redundancy

**Synergies (1 + 1 > 2):**
- **F1 × F3** — trajectory + events-on-trajectory = the STYX × Theograph hero. The core thesis.
- **F2 × F4** — forecast feeds the risk waterline; the anticipation pair.
- **F1 × R3** — *where* (trajectory) + *why* (graph). The headline combo.
- **F1 × F6** — patient and ward on one shared embedding ("one embedding, two scales").
- **F8 × {why-this-alert, R4}** — build CALLIOPE once, serve clinician + carer + handover. Highest surface-side leverage.
- **F5 × {R1, F7, R3}** — F5's coherence is what gives the prior, the silent-deterioration detector, and the graph real signal. A multiplier on three intrinsics.
- **R1 × {F2, F4, F7}** — history personalises the anticipation.

**Redundancies (overlap — watch for double-counting):**
- **F2 ↔ R2** — two "forecasts." Complementary *only if* framed continuous-physiology (cone) vs discrete-care-events (CHARON). Otherwise the demo reads as one thing twice.
- **F2 ↔ F4 ↔ F7** — three "this patient is deteriorating" signals. The redundancy is real unless each is a distinct lens (see §6, conflict 1).
- **F9 ↔ R2 ↔ JANUS** — the counterfactual recurs. F9 (yesterday's-trend) is a degenerate counterfactual; unify under CHARON if R2 is built.
- **F10 ↔ MORPHEUS (deferred)** — instance-based vs cluster-based "patients like this." ECHO covers the MVP need.

---

## 5. Red Team — adversarial challenge

- **F5 is the single point of failure.** Six features' value is gated on what F5 *scripts*: F7 needs a dissociable silent-deterioration case; R3 (learned *and* fallback) needs a genuine inter-signal decoupling to detect — script no decoupling and the "saw it first" line is fake; F6 needs a coherent multi-patient cohort; F10 needs past patients *with outcomes*; R1 needs Theograph histories that actually predict; the deterioration-triple dissociation (below) needs the silent case. **F5's scenario design is the spec the MVP depends on, not merely slice 1.**
- **Deterioration triple-count.** If F2, F4, F7 all fire together, judges ask "which one caught it?" Without dissociation the anticipation story muddles and AEGIS loses its distinct reason to exist.
- **F1 legibility.** PCA/UMAP axes can be an unreadable blob; the hero then fails. Mitigation must be live (label/disentangle, or fall back to a clinical two-axis).
- **CALLIOPE faithfulness.** An NLG that narrates drivers can state a plausible-but-wrong cause — worse than silence. Must be a strict template over the model's *actual* top contributors, not free-form generation.
- **R3 feasibility (known).** GNN may not train in window → fallback; but the fallback is itself gated on F5 scripting the decoupling.
- **R2 defensibility.** The MC event-probabilities have the thinnest validation; decorative without calibration. Keep firmly reach.
- **Scope.** 15 features in two days is not the real MVP. The arbiter must tier ruthlessly.

---

## 6. Arbiter — scores, tiers, rulings

Composite = Σ(axis × weight). Surface features carry MF = 0; intrinsic carry AU = 0.

| Feature | Layer | MF | AU | Pars | Rob | Read | **Composite** | Tier |
|---|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| F5 synthetic engine | I | 0.95 | — | 0.70 | 0.60 | 0.85 | **0.67** | 0 |
| F1 latent trajectory | I | 0.90 | — | 0.75 | 0.55 | 0.85 | **0.66** | 0 |
| F4 risk + escalation | I | 0.75 | — | 0.80 | 0.70 | 0.85 | **0.66** | 0 |
| F2 forecast cone | I | 0.80 | — | 0.75 | 0.65 | 0.80 | **0.64** | 0 |
| F3 Theograph overlay | S | — | 0.90 | 0.85 | 0.80 | 0.80 | **0.63** | 1 |
| R1 history-as-prior | I | 0.80 | — | 0.70 | 0.65 | 0.75 | **0.62** | 2 |
| F7 AEGIS | I | 0.78 | — | 0.75 | 0.60 | 0.75 | **0.62** | 1 |
| F11 workflow touches | S | — | 0.50 | 0.85 | 0.80 | 0.80 | **0.57**\* | 3\* |
| F8 CALLIOPE | S | — | 0.80 | 0.85 | 0.55 | 0.80 | **0.56** | 1 |
| F9 ghost trail | S | — | 0.60 | 0.85 | 0.70 | 0.75 | **0.55** | 1 |
| F6 ward board | S | — | 0.80 | 0.70 | 0.75 | 0.70 | **0.55** | 1 |
| R4 HERMES | S | — | 0.70 | 0.80 | 0.70 | 0.70 | **0.55** | 2 |
| F10 ECHO | S | — | 0.65 | 0.75 | 0.65 | 0.65 | **0.51** | 1 |
| R3 CADUCEUS | I | 0.90 | — | 0.40 | 0.55 | 0.40 | **0.50** | 2 |
| R2 CHARON | I | 0.75 | — | 0.45 | 0.45 | 0.50 | **0.47** | 2 |

\* **Arbiter override.** F11's composite is inflated by the parsimony/robustness/readiness axes rewarding "cheap and safe"; its analytical utility (0.50) is the truth for MVP purposes — invisible in the demo, non-load-bearing. Tiered **3 (defer to pilot)** on value, against its arithmetic. (A standing weakness of the rubric: trivial-but-safe features over-score; the arbiter weights MF/AU for MVP inclusion.)

**Tiers.**
- **Tier 0 — irreducible spine:** F5, F1, F2, F4.
- **Tier 1 — MVP completers:** F7, F3, F8, F6, F9, F10. (F9, F10 are the *prune-first* pair if time-pressed — Backward's flag.)
- **Tier 2 — reaches (additive, droppable):** R1, R3, R4, R2.
- **Tier 3 — defer:** F11.

**Conflict rulings.**
1. **Deterioration triple (F2/F4/F7) → keep all three, assign distinct roles.** F4 = the absolute-risk actionable threshold; F2 = the forecast-based early warning (threshold crossed in N hours); F7/AEGIS = the personal-baseline *silent* case (fires while F4 looks fine). **Gating condition on F5:** the demo scenario must dissociate them — absolute numbers OK → AEGIS fires → forecast confirms → F4 would have fired hours later. If F5 can't produce a dissociable silent case, F7 collapses into F4 and loses its tier.
2. **F2 cone vs R2 CHARON → not redundant iff continuous-physiology vs discrete-care-events.** Dormant for the MVP (R2 is Tier 2). If R2 is built, show them answering different questions or cut one.
3. **F9 vs R2/JANUS counterfactual → F9 is the cheap MVP version.** If R2 is built, unify the true counterfactual under CHARON's machinery; F9 stays the visual. No duplicated modelling.
4. **F10 ECHO vs MORPHEUS → ECHO covers the MVP;** MORPHEUS stays deferred (redundant).
5. **CALLIOPE (F8) is surface → never build it before the signals it narrates (F2/F4/F7) are correct,** and gate it on faithfulness (§9, gate 3). Re-tagged Tier-1 enabler, built *after* F7.

---

## 7. Integration order (wire order → `BUILD_MVP.md`)

Dependency-respecting, intrinsic-first, Red-Team-gated.

1. **F5** — synthetic engine, *to the scenario spec*: a dissociable silent-deterioration case, a genuine inter-signal decoupling, a coherent cohort with outcomes. `seed=42`. → **gate 1**.
2. **F1** — latent trajectory, labelled/clinical axes. → **gate 2**.
3. **F2 → F4** — forecast cone, then risk waterline + escalation.
4. **F7** — AEGIS, dissociated from F4 (conflict ruling 1).
5. **F3** — Theograph event overlay.
6. **F8** — CALLIOPE, strict template over real attributions. → **gate 3**.
7. **F6** — ward board (needs F5 cohort).
8. **F9, F10** — ghost trail, ECHO. *First to cut if behind schedule.*
   — **MVP gate: 10 features `{F5, F1, F2, F4, F7, F3, F8, F6, F9, F10}`** —
9. **R1 → R4 → R3 → R2** — reaches by risk-adjusted value.
10. **F11** — deferred to clinical pilot.

**Δ-from-PRD.** The PRD's slice 6 ordered reaches `R1 → R3 → R4 → R2`. MAAFI swaps to **`R1 → R4 → R3 → R2`**: R4 (HERMES) is cheap, sits on F8, and is the only Challenge-2 bridge (weight 4), so it banks a rubric point before the high-risk GNN. Keep R3 ahead of R4 *only* if the team has GNN comfort and is optimising for demo wow over the C2 score.

---

## 8. Confirmed MVP

`{F5, F1, F2, F4, F7, F3, F8, F6, F9, F10}` — **10 features**, matching both the Forward greedy halt and the canonical MAAFI MVP size. Tier-0 + Tier-1.

**Contingency, in cut order:** F10 → F9 (Backward's prune-first pair) → F8 reverts to a hard-coded one-liner → F6 reduces to a 3-patient board. The irreducible `{F5, F1, F2, F4, F7}` is never cut.

---

## 9. Go/no-go gates

Set in advance; the build does not advance past a red gate.

1. **F5 fidelity (before everything).** Does the synthetic patient exhibit (a) a dissociable silent-deterioration case, (b) a genuine inter-signal decoupling, (c) a coherent multi-patient cohort with outcomes — reproducibly at `seed=42`? If no, no downstream feature is meaningful.
2. **F1 legibility (before F2 onward).** Are the latent axes interpretable enough that a clinician reads the path as physiology? If the embedding is an unreadable blob, fall back to a labelled clinical two-axis (e.g. oxygenation × perfusion) before proceeding.
3. **CALLIOPE faithfulness (before shipping F8/R4).** Does every generated rationale match the model's actual top contributors? If it can drift, lock it to a strict template over the real attribution — never free-form.

---

*Run complete. The one finding to carry forward above all others: **F5's scenario spec is the contract the MVP depends on** — write it to contain the phenomena the features claim to detect, and gate on it.*
