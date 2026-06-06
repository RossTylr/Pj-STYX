# STYX — architecture red-team verdict

**Applying the Virtual-Ward red-team architecture protocol to STYX.**

| | |
|---|---|
| **Date** | 3 June 2026 |
| **Axis** | Deployment / serving architecture (A1–A5). *Orthogonal to MAAFI* — that chose the features (what); this chooses the serving model (how). |
| **Inputs** | The uploaded protocol; STYX PRD v0.3; `MAAFI_STYX_verdict.md`. |
| **Pairs with** | `MAAFI_STYX_verdict.md` (feature axis) and the §14.1 go/no-go gates (build horizon). |

Two facts about STYX change the protocol's generic answer, so read this before the rubric:

1. **The MVP runs on synthetic replay, not a live ward** (PRD non-goal: no real device integration). So most of the rubric — concurrency, latency SLA, Kafka, prospective pilot — is a *deployment-horizon* question, not an MVP one. For the hackathon there is no infrastructure to choose; there is only a replay re-score cadence.
2. **STYX detects trend and trajectory, not acute spikes.** AEGIS is explicitly the *silent, trend-adverse* case; the forecast cone is about trajectory shape. A1's whole advantage — per-event latency on acute inflections — is therefore low value for STYX's value proposition, while A1's costs (alert storms, drift churn, SHAP-per-event latency) land in full.

---

## 1. Two dissolutions (before scoring)

The protocol presents five competitors. For STYX, two of them aren't competitors:

- **A5 (uncertainty-first) is not an architecture — it's a cross-cutting requirement STYX already meets.** F2 (conformal forecast cone) and SENTINEL (confidence-gating) already bake calibrated uncertainty into every output. So "A5" doesn't compete with A1/A2/A3; it's a property *all* of them must carry. Decision: **conformal + quality-gated outputs everywhere**, regardless of serving model. A5 dissolves into a requirement, removing a false choice.
- **A4 (edge / per-ward models) is out of scope.** One ward, synthetic data, no data-residency driver, n≈30–50 per ward kills statistical power (the protocol flags this itself). Dropped.

That leaves a clean three-way contest: **A1 vs A2 vs A3.**

---

## 2. STYX-adjusted rubric (deployment horizon)

A4 dropped, A5 folded in. Scores follow the protocol's directional findings, adjusted for STYX's trend-based detection. *Most criteria are deployment-horizon* (marked ◇); only one is MVP-relevant (marked ★).

| Criterion | Wt | A1 Stream | A2 Batch/windowed | A3 Hybrid | STYX note |
|---|--:|:--:|:--:|:--:|---|
| ★ Surfaces the *scripted* deterioration in time | 25% | over-serves | **yes, if cadence set by G3** | yes | Trend signal tolerates windowed refresh; cadence is the only knob that matters for the demo. |
| ◇ False-alert ratio | 20% | 18% | **2%** | 8% | A1's storms are pure cost for a trend monitor. |
| ◇ Explainability latency | 15% | 800ms | **12ms** | 180ms | STYX uses CALLIOPE (template over attributions), not SHAP-per-event — A1's killer cost is self-inflicted. |
| ◇ Operational complexity (1 simple–5 nightmare) | 15% | 4 | **2** | 5 | No infra to run for the MVP; A3's Redis/staleness is deployment debt. |
| ◇ Iterations to parity (50–100 LOC slices) | 10% | 20 | **12** | 28 | A2 is one slice over replay. |
| ◇ Cohort-shift robustness | 10% | 0.5h (churny) | 4h | **1h** | Real only at deployment; on replay it's a non-issue. |
| ◇ Pilot feasibility | 5% | 3w | **2w** | 4w | Deployment horizon. |

A2 wins on every criterion except raw latency-to-alert, and for STYX that one exception is neutralised: a trend/trajectory signal does not need per-event latency, and the cadence that *does* matter is bounded by gate G3, not by the protocol's 4 h handoff figure.

---

## 3. Cross-attacks resolved

- **Stream → Batch ("you miss mid-shift sepsis at 4h"):** the protocol's 4 h is a clinical-handoff cadence and is the wrong number for STYX. STYX re-scores on a *continuous windowed* cadence — minutes, not hours — bounded below by gate G3 (the window must surface AEGIS before the F4 threshold). With the cadence set that way, A2 does not miss the deterioration. The "batch is too slow" attack only lands against a 4 h cadence STYX never adopts.
- **Batch → Stream ("your alert storm burns out the team"):** decisive for a trend monitor. A1's per-event firing on HR/SpO₂ wobble is noise; AEGIS exists precisely to fire once, on the trend. A1's debouncing-by-embedding-similarity fix re-introduces the latency it was chosen for. Stream loses this exchange.
- **Hybrid → both ("I do both, use me"):** true at deployment, premature for the MVP. A3's two failure modes (stream broken? batch broken? both?) and cache-invalidation logic are operational debt with no demo payoff on synthetic replay. A3 is the *target*, not the MVP.

---

## 4. Verdict

- **MVP (hackathon): A2-simple over replay.** Re-score the synthetic cohort on a windowed cadence, with conformal + quality-gated outputs (A5 folded in). No Kafka, no serving infra — one slice. The cadence is a tunable on the F5 replay engine, set so the demo clears gate G3. This is the architecture *implementation* for the demo.
- **Deployment target / Phase 2: A3 (hybrid).** Streaming feature aggregation → frequent re-score, conformal + SENTINEL throughout. This is the honest "what we'd do next" — and the data contract should be shaped for it now (FHIR-shaped events, §AppendixA), even though the MVP doesn't run it.
- **A1: not for STYX** unless acute-event detection becomes an explicit goal — its latency advantage is orthogonal to a trend/trajectory monitor and its costs are real.
- **A4: dropped.** **A5: dissolved into a requirement** (conformal everywhere).

**The pitch honesty point:** say plainly that the demo is *replay, not live*. Claiming a live-streaming architecture you didn't build is the kind of thing clinical/technical judges catch — and SENTINEL's whole story is honesty. "Replay of a synthetic ward, designed to deploy as A3 against FHIR" is the credible framing.

---

## 5. Gate reconciliation (two horizons, no conflict)

| Gate set | Horizon | Governs |
|---|---|---|
| **PRD §14.1 — G1 fidelity · G2 legibility · G3 dissociation · G4 faithfulness** | Build (hackathon, synthetic) | What we ship at the hackathon. |
| **Protocol Gates 1–4 — rank/drop · latency SLA @100 pts · retrospective coverage ≥95% · prospective clinician feedback** | Deployment (real pilot) | What a real rollout must clear after the hackathon. |

These are sequential, not competing. The only new MVP-horizon requirement this red-team adds is already inside G3: **the replay re-score cadence must keep the AEGIS→threshold lead intact** — i.e., the architecture cadence is *constrained by* G3, not chosen freely. Add the cadence as an explicit parameter and let G3 test it.

---

## 6. Darlings killed (mapped to STYX)

1. **"Real-time (A1) is always better." → KILLED.** STYX is trend/trajectory; windowed refresh suffices, and A1's latency is low-value while its storm/drift/SHAP costs are high. The strongest darling, and it dies cleanly here.
2. **"Explainability needs SHAP-per-prediction." → KILLED for STYX.** Explainability is CALLIOPE (strict template over the real top-_k_ attribution, gated by G4) plus the trajectory and CADUCEUS visuals — not 340 ms SHAP on every event. This removes A1's single largest cost.
3. **"All 10 vitals are needed." → TRIM.** The protocol's ten (HR, SpO₂, BP, temp, lactate, creatinine, urine, WBC, CRP, RR) are more than the demo needs. Build F5 around the *tight* set that drives the scripted decoupling (e.g. RR, SpO₂, HR, temp + one labs proxy) — fewer vitals means a simpler generator (G1), a clearer decoupling for CADUCEUS, and a cleaner state space (G2). Add the rest only at deployment.
4. **"Edge models per ward avoid global overfitting." → N/A.** Single-ward synthetic; A4 dropped.
5. **"4 h batch cadence is right." → KILLED.** STYX's cadence is set by G3 (must beat the threshold) — minutes, not hours — and at deployment it's the FHIR delivery rate (5–30 min), still windowed, never per-event.

---

## 7. What this changes in the spec

- **PRD §9 (data model & architecture):** add a one-paragraph deployment note — *A2-simple windowed re-score over replay for the MVP (cadence bounded by G3); A3 hybrid as the deployment target; conformal + SENTINEL outputs throughout (A5 as a requirement, not a mode); demo is replay, stated plainly.*
- **F5 (synthetic engine):** expose the **re-score cadence** as an explicit parameter; gate G3 tests it.
- **F5 vitals set:** trim to the tight set that carries the decoupling (darling #3); expand only at deployment.
- **Appendix A (data contract):** the FHIR/SNOMED event shaping is now load-bearing for the A3 *target*, not just credibility — keep it on the deferred list but tag it "Phase-2 enabler."

---

*Verdict in one line: STYX is a trend monitor, so it serves as **A2-simple windowed batch over replay** for the MVP and **A3 hybrid** at deployment, with conformal/uncertainty as a standing requirement rather than a competing mode — and the cadence is owned by gate G3, not chosen freely.*
