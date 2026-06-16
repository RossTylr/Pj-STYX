# STYX — proposed explorer notebooks

*Companion to `STYX_ds_notebook_proposals.md`. Ideation only, no code. Four **explorers** — open research questions, not deliverables. Each is hypothesis-driven and ends in a decision; each may legitimately return a "no," which is a valuable result. They feed direction, not the demo.*

---

## What an explorer is, and the honesty gate

The first three notebooks (10–12) demonstrate and rehearse. These four **investigate things that could change STYX's direction or invalidate part of it.** They carry a sharper honesty obligation than the demo notebooks, because each sits at a different distance from what synthetic data can actually settle:

| Explorer | Can synthetic data answer it? |
|---|---|
| E3 · Time-to-event | **Yes** — self-contained; the usual in-sample caveat only |
| E1 · PCA / state space | **Partly** — synth shows the *sensitivity*; only real data confirms |
| E2 · Signal-set expansion | **No, circularly** — you inject the signal you're testing; synth proves only the pipeline |
| E4 · Fairer comparator | **No** — there is no nurse in synthetic data; the real test is a human study |

Every explorer therefore opens with a **"what synth can / cannot tell us here"** block before any method. Conventions from the companion doc carry over unchanged: the three-register explainer (plain / dev / tech) on methodologically heavy steps; synthetic data is **method, not performance**; and the determinism guard — explorers may **extend or reseed** the synth, but only on *derived, branched, clearly-labelled experimental* cohorts. The canonical seed-42 cohort and its digest stay the untouched reference; every experimental cohort is seeded locally.

Structure of each explorer: **Question → Why it matters → What synth can/can't tell us → Method → Decision rule.**

Suggested home: an `explorers/` subfolder, to signal lower polish and investigative status, kept apart from the production/demo notebooks.

---

## E1 — `explorers/E1_state_space_on_real_data.ipynb`
### "Does PCA earn the axes?"

**Question.** On richer, more variable data, does PCA recover meaningful data-driven oxygenation/effort axes — dissolving the constructed-axes fallback and the G2 "by-construction" caveat?

**Why it matters.** G2 currently passes *partly by construction*: the axes are hand-built (oxygenation = SpO₂; effort = RR & HR), so the |r|≈1.0 fidelity is half-tautology, and a hostile reviewer will say so. If PCA recovers those axes on realistic data, the state space becomes genuinely data-earned and the caveat disappears.

**What synth can / can't tell us.** The *current* cohort is too low-variance for PCA to work — that is precisely why it falls back to constructed axes. Synth can show the **sensitivity**: at what level of physiological diversity PCA starts recovering the constructed axes. It cannot confirm PCA works in the wild — that needs real data.

**Method.**
1. **Diagnose the failure** — characterise the current cohort's covariance and rank; show why the leading components don't align to oxygenation/effort (low effective rank, dominated by the scripted index signal). *Visual:* scree plot + PC loadings overlaid on the constructed axes; the degeneracy made explicit.
2. **Variance sweep** — generate a family of branched synthetic cohorts with rising diversity (more archetypes, more conditions, graded noise); run PCA on each; measure convergence of the data-driven components to the hand-built axes (cosine similarity of loadings). *Visual:* convergence curve (similarity vs diversity); constructed-vs-PCA state spaces side by side at low / mid / high diversity.
3. **Robustness** — sensitivity to scaling, missingness, outliers, vital count. *Visual:* loading-stability bands.
4. **Real-data test spec** — exactly what to run on a real cohort to settle it: sample size, the convergence metric, the pass criterion that would justify dropping the fallback.

**Decision rule.** If PCA converges to the constructed axes above a realistic diversity threshold → strong evidence the real-data state space is data-earned; plan the switch. If not → keep constructed axes and own the caveat permanently and openly. (This explorer overlaps your existing cohort-diversity slices — reuse that machinery for the sweep.)

---

## E2 — `explorers/E2_signal_set_expansion.ipynb`
### "What do richer wearable signals add?"

**Question.** Do continuous-wearable signals beyond the core four — HRV, activity/posture, skin temperature, cuffless BP — add early-deterioration signal and lead time?

**Why it matters.** STYX reads four vitals; modern wearables stream more, and HRV and activity are literature-backed early markers of decompensation. If they extend the lead, the thesis strengthens; if not, the tight scope is vindicated.

**What synth can / can't tell us — the load-bearing caveat.** To explore these you must **extend the generator to produce them**, so "do they help?" is *circular* on synth — you injected the signal. Synth can show only (a) that the pipeline ingests and handles more channels cleanly, and (b) *if* deterioration physiology is encoded into the new signals per the literature, whether the trajectory machinery picks it up. **Whether real HRV adds real lift is strictly a real-data question.** This caveat is annotated directly on every results chart in the notebook.

**Method.**
1. **Literature-grounded signal rationale** — for each candidate, what the evidence says it does pre-deterioration (HRV falls ahead of sepsis/decompensation; activity and mobility drop; skin–core temperature gradient shifts), with the dynamics to encode. *Visual:* signal-rationale table; assumed pre-event behaviour per signal.
2. **Branched generator extension** — add the signals to a derived experimental cohort with literature-grounded pre-event dynamics; canonical cohort untouched. *Visual:* example traces of the new channels through a deterioration.
3. **Incremental-value ablation** — core-4 vs +HRV vs +activity vs all; does each added channel extend lead time / improve detection on the extended synth? *Visual:* lead-time and detection deltas per signal, with the circularity caveat printed on the axes.
4. **Honest output** — a *prioritised "test on real data first" ranking*, not a performance claim. The deliverable is a sequenced real-data experiment.

**Decision rule.** Produces the ranked list of which signals to instrument and test first once real wearable data is available — and an honest statement that synth cannot rank them on merit, only on plausibility.

---

## E3 — `explorers/E3_time_to_event.ipynb`
### "When, not whether"

**Question.** Reframe the model from a binary outcome (escalated y/n) to **time-to-escalation** (survival analysis) — does it fit the lead-time story better and give a more useful clinical readout?

**Why it matters.** Binary throws away information. *"Likely to cross in ~3.5 h (2–6 h)"* is more clinically actionable than a flag, and it matches STYX's lead-time pitch directly. This is the explorer most likely to produce a concrete product change.

**What synth can / can't tell us.** The most self-contained of the four — every synthetic patient already has an escalation time, so survival analysis is legitimate here; the only caveat is the usual in-sample one.

**Method.**
1. **Reframe the target** — define time-to-escalation, censoring (patients who never escalate), and the risk set. *Visual:* Kaplan–Meier curves by archetype.
2. **Transparent survival models** — Cox proportional hazards, accelerated failure time, and/or a discrete-time hazard model on the trajectory features; compare against the binary baseline. *Visual:* per-patient predicted survival curves; hazard over the trajectory.
3. **Calibrate the *time* estimate** — does predicted time-to-escalation match observed? *Visual:* predicted-vs-actual time calibration; concordance. *Tech:* C-index, integrated Brier score, censoring-aware calibration.
4. **UI implication** — how a calibrated time-to-escalation estimate with an uncertainty band changes the patient card and the cascade readout versus the binary flag. *Visual:* mock card — *"likely to cross in ~3.5 h (2–6 h)."*

**Decision rule.** Whether to move STYX's headline readout from binary risk to a calibrated time-to-escalation estimate. Build this one first — it stands on its own and carries genuine product upside.

---

## E4 — `explorers/E4_fairer_comparator.ipynb`
### "Beating the nurse, not just the score"

**Question.** Benchmark STYX against **"NEWS2 + nurse clinical judgment"** — the real standard of care — not NEWS2 alone.

**Why it matters.** Beating a fixed score is easy, and a hostile clinician knows it. The honest, demanded test is whether STYX adds value over an experienced nurse's gestalt. The current A/B (STYX vs NEWS2) flatters STYX, and a clinical reviewer will press exactly here.

**What synth can / can't tell us — the hardest caveat.** **There is no nurse in synthetic data.** Any modelled "nurse judgment" is a strawman: too weak and STYX wins trivially; too strong and STYX loses by construction. Synth *cannot* answer this — the real test is a clinician reader study. So this explorer is mostly (a) defining the comparator rigorously and (b) showing, by sensitivity analysis, that the answer is assumption-driven and therefore unanswerable on synth, plus (c) the spec for the human study that does settle it.

**Method.**
1. **Anatomy of "nurse judgment"** — decompose what the nurse adds over the score: the nurse obs already in the comparator (BP, ACVPU), trend awareness, context and gestalt — and what the nurse misses (fatigue, night shift, caseload). *Visual:* a "what the nurse adds / misses" map.
2. **Nurse-proxy sensitivity** — model a spectrum of synthetic reviewers from weak to expert (varying trend access, gestalt, and miss-rate) and plot STYX's apparent advantage as a function of assumed nurse skill. *Visual:* STYX-edge vs nurse-skill curve, with the strawman zones shaded — the *point* is to demonstrate the result moves with the assumption.
3. **Reader-study spec** — design the real test: clinicians reviewing matched cases with and without STYX; endpoints (decision accuracy, time-to-decision, inter-rater agreement, missed-deterioration rate); powering; blinding; governance. This is the real deliverable.

**Decision rule.** Commit to a clinician reader study as the only honest answer. In the interim, stop presenting the NEWS2-alone A/B as the hard test — caveat it explicitly as *"vs the score, not vs the nurse."*

---

## Sequencing & what they buy you

- **Build order:** **E3 first** (self-contained, product upside), then **E1** (settles the G2 caveat; reuses the cohort-diversity machinery), then **E2** (needs the generator extension), then **E4** (mostly a study spec, lowest code).
- **Status:** research, not roadmap deliverables — lower polish, hypothesis-driven, and a clean "no" is a result worth having. None of them feed the demo; they feed decisions.
- **The strategic payoff:** these are the *"we know our open questions and exactly how we'd resolve them"* artifacts. Between them they pre-empt the four hardest questions a data scientist or clinician can ask — *is the state space real, is four vitals enough, why binary, and does it beat a nurse* — by showing the experiments already designed and, where synth can't answer, saying so plainly. That candour is the same edge the rest of the project runs on.
