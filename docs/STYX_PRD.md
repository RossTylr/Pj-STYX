# STYX — Product Requirements Document

**Virtual ward physiological-trajectory monitor, with care-history (Theograph) integration and a Monte Carlo forecasting layer.**

| | |
|---|---|
| **Version** | 0.5 (draft) — front-end decided (Streamlit + Plotly; React = deployment rebuild); repo layout added; evidence-notebook layer added (§14.2) |
| **Date** | 3 June 2026 |
| **Status** | Hackathon scoping — pre-build |
| **Challenge** | Challenge 3 (primary) · Challenge 2 (secondary, via HERMES) |
| **Engineering discipline** | RAIE v3 — 50–100 LOC vertical slices, `seed=42`, append-only `EXPERIMENT_LOG.md`, phase-boundary gates |

---

## TL;DR

STYX renders a virtual-ward patient's continuous physiological telemetry as a **trajectory through a learned latent state space**, shaded with a stability basin and a crisis attractor, with a short-horizon **forecast cone**. The patient's **Theograph** — their discrete, cross-service care history — is integrated as three layers: events overlaid on the trajectory (display), the lifelong history as context (a ribbon), and history-derived features conditioning the forecast (model). A **Monte Carlo forecasting engine (CHARON)** extends the Theograph forward as a distribution of likely care-event futures. The **reach goal is CADUCEUS** — a patient-as-graph GNN that explains *why* the patient is moving in state space by learning the dependencies between physiological signals. A thin **carer-facing view (HERMES)** reads the same state model in plain language, honouring Challenge 2.

The build is a RAIE vertical slice: **synthetic data first** (a coherent history-→-physiology patient generator, derived from SEKHMET), one condition, one killer view, then additive reaches.

---

## 1. Problem & context

Virtual wards discharge patients early with remote sensors and monitor them at a distance. This produces a flood of continuous, multi-stream physiological telemetry that a clinician cannot watch in raw form across a caseload. The Challenge-3 brief asks for new ways to **present** this telemetry and to **automate its analysis** — explicitly suggesting recovery modelled as a trajectory through a multi-dimensional state space, and advanced ML (e.g. graph neural networks) mapping the interactions between physiological streams.

Three gaps in current remote-monitoring dashboards:

1. **No trajectory.** Vitals are shown as separate line charts or a single composite score (NEWS2). Neither shows *where the patient is heading* — the shape of the recovery or the drift toward instability.
2. **No forecast.** Alerts fire on threshold breach — after deterioration has happened. There is little anticipation and little honest uncertainty.
3. **No history.** The live episode is read in isolation. The same desaturation event means something different in a robust patient than in a frail one with three prior non-elective admissions — but that context (the **Theograph**) is not in view.

STYX addresses all three, and the Theograph integration is what closes the third.

---

## 2. Goals & non-goals

**Goals**
- Make a single patient's physiological state and near-term direction legible at a glance.
- Anticipate deterioration before threshold breach, with calibrated uncertainty.
- Bring the patient's cross-service care history into the same view as context and as model signal.
- Triage a caseload by predicted time-to-escalation, not headcount.
- Honour Challenge 2 with a plain-language carer view built on the same model.
- Demonstrate a credible path to high-ceiling data science (the CADUCEUS GNN) without depending on it.

**Non-goals (for the hackathon)**
- Real device integration or live data ingestion (we use a synthetic engine).
- Regulatory-grade validation or clinical sign-off.
- A production multi-tenant deployment.
- Full EHR/FHIR interoperability (we stub the data contract, not the integration).
- A trained, converged GNN as a *requirement* — it is a reach, with a non-learned fallback (see §8).

---

## 3. Users & jobs-to-be-done

| User | Primary job | Surface |
|---|---|---|
| **Virtual-ward clinician** (primary) | "Which of my patients is deteriorating, and why?" | Ward board → patient view |
| **Duty / ward manager** (secondary) | "Where is my capacity risk and who can step down?" | Ward board (capacity lens) |
| **Carer / family member** (Challenge 2) | "Is Mum OK today, and what do I do if not?" | HERMES card |
| **Analyst / service planner** (wider applications) | "What pathways does this cohort follow, and where do they break?" | Prospective Theograph (intensity surface) |

---

## 4. Product overview — the integrated model

STYX, the Theograph, and the forecast are three views of one underlying object: a patient as a **stochastic process** with a continuous physiological state and a discrete care-event log.

- **STYX (the present, continuous).** Telemetry projected into a latent state space; the stay rendered as a path between a stability basin and a crisis attractor; a forecast cone ahead.
- **Theograph (the past, discrete).** Cross-service care events as service swimlanes over years — the "who is this person" context.
- **The join is time and events.** Care events annotate the trajectory; history conditions the forecast; and — critically — **the completed virtual-ward episode appends to the Theograph as new events.** The two are a pipeline, not just neighbours: the Theograph is the *prior* for STYX upstream, and STYX is an *event source* for the Theograph downstream.

Three integration layers, in increasing depth (mapped to feature priority below):

1. **Display — events as annotations** (zero model change). Care events threaded onto the trajectory and onto a time-aligned strip.
2. **Context — lifelong history as a ribbon** (linked, multi-scale). Brush the ribbon ↔ highlight the trajectory.
3. **Model — history as prior** (covariates). Theograph-derived features (frailty proxy from event density, comorbidity count, prior non-elective admissions, social-care dependency) condition the personalised baseline, the basin geometry/reserve, and the forecast hazard.

Module naming (mythological, consistent with the wider portfolio): **STYX** (the threshold river — the trajectory monitor) · **CHARON** (the ferryman — carries the patient forward; the Monte Carlo forecast) · **CADUCEUS** (the medical graph — the GNN explanatory layer) · **HERMES** (the messenger — the carer view) · **SENTINEL** (the guard — the trust/quality layer) · **AEGIS** (the shield — silent-deterioration detection) · **CALLIOPE** (the muse of eloquence — the shared rationale / NLG service) · **ECHO** (the case-based echoes of similar past patients).

---

## 5. Core features — MVP (P0)

Feature priority reflects the **MAAFI verdict** (`MAAFI_STYX_verdict.md`), which tiered all 15 candidates and confirmed a **10-feature MVP**: `{F5, F1, F2, F4, F7, F3, F8, F6, F9, F10}`.

- **Tier 0 — irreducible spine:** F5, F1, F2, F4. Remove any one and there is no defensible demo.
- **Tier 1 — MVP completers:** F7, F3, F8, F6, F9, F10. F9 and F10 are the *prune-first* pair if the build falls behind.
- **Deferred (Tier 3):** F11 — invisible in a three-minute demo; build only for a clinical pilot.

The reaches (R1–R4) are Tier 2 (§6). Each gate that governs the build is in §14.1. Source-concept and corpus references (§n) point back to `virtual_wards_ideation.md`.

| ID | Feature | Description | Source concept |
|---|---|---|---|
| **F1** | **Latent state-space trajectory** | Project the physiological vector (HR, SpO₂, RR, temp, BP) into a 2-D latent space; render the stay as a path with a pulsing *now* marker. Shade a stability basin (recovery corridor) and a crisis attractor learned from the cohort. | STYX |
| **F2** | **Forecast cone** | Short-horizon (≈12 h) physiological forecast as a cone widening with uncertainty (conformal residual bands as the simple version). | STYX / ORACLE |
| **F3** | **Theograph event overlay** (Layer 1) | Care events as glyphs dropped at the path position they occurred, and as a time-aligned swimlane strip beneath the risk curve. | Theograph integration |
| **F4** | **Risk waterline + escalation logic** | Risk over the episode as a filled curve with an escalation threshold; a continuous deterioration gradient rather than a hard traffic light. | TIDE / CHIRON |
| **F5** | **Synthetic data engine** | Generate a coherent patient: a Theograph history whose frailty *causally shapes* the physiological trajectory and crisis propensity; scripted, replayable, speed-controllable deterioration over a *tight vital set* that carries the decoupling (e.g. RR, SpO₂, HR, temp + one labs proxy — not all ten). Exposes a **re-score cadence** parameter (the serving window, §9), bounded by G3. `seed=42`. | SEKHMET-derived |
| **F6** | **Ward board (triage)** | Multi-patient roster sorted by predicted time-to-escalation; heat-strip risk over time; a *silent-but-rising* watchlist separate from active alarms (§82); "quietest patient" and "newly admitted / low-history" flags; a focus mode hiding stable patients (§168). | ARGUS |
| **F7** | **AEGIS — silent-deterioration detector** *(P0)* | Learn each patient's personal "normal" in the first hours; flag departures from *their* baseline plus change-points — catching the patient whose absolute numbers look fine but whose *trend* is adverse, before population thresholds would. This is the flag the demo turns on. | AEGIS (§41, §47, §234, §236, §382) |
| **F8** | **CALLIOPE — rationale generator (NLG)** *(P0)* | One component turning the current risk drivers into a sentence ("rising RR and falling SpO₂ over 3 h"). Built once, consumed four ways: the *why-this-alert* one-liner (§77), the HERMES plain-language translation (§412), the handover digest (§58), and the one-sentence admission→now trajectory diff (§510). | §128 |
| **F9** | **Counterfactual ghost trail** *(P1, low-cost)* | A faint "where you'd be on no-intervention / yesterday's trend" path beside the actual trajectory on the STYX hero — visceral, cheap, and it sharpens the intervention story (the ghost of *not* treating). The synthetic engine supplies the counterfactual (§362). | §13, §271 |
| **F10** | **ECHO — trajectory echo** *(P1, low-cost)* | Overlay the three most-similar past trajectories with their outcomes ("two recovered, one escalated"), free from the synthetic cohort — case-based grounding for the forecast that clinicians instinctively trust. | ECHO (§17, §91, §98) |
| **F11** | **Clinician-workflow touches** *(deferred — Tier 3)* | "Since last review" shading so a clinician sees exactly what changed while away (§56); one-click "I've reviewed this" that timestamps and quiets the patient (§164). Real clinical value but invisible in the demo — MAAFI defers it to a pilot. | §56, §164 |

**Note on F5.** The synthetic engine is not a convenience — it is the de-risking spine of the whole demo and the only honest way to show the model's value (a deterioration we control). It must come first. Coherence (history → physiology) is the hard, valuable part and is squarely in the SEKHMET / FAER casualty-generator lineage.

**Note on SENTINEL.** A thin trust layer is folded into F1–F4 rather than built separately: outputs are quality-gated (sensor dropout/missingness reduces confidence rather than producing a confident wrong answer), and confidence is encoded honestly (e.g. saturation of the risk colour, thickness of the forecast cone). This pre-empts the judges' "but can you trust it?" for very little cost.

**Design note.** A colour-blind-safe palette is the default across every surface (§148) — non-negotiable for a clinical tool that colour-encodes risk.

**Note on CALLIOPE (F8) — MAAFI reclassification.** CALLIOPE is a *surface* feature: it narrates outputs, it does not compute them. So it is built *after* the signals it explains (F2/F4/F7) are correct — narrating a wrong model is worse than silence — and it is gated on faithfulness (G4, §14.1). It is a Tier-1 surface enabler, not a foundational P0; its P0-ness was only ever cheap-high-leverage, never mechanistic priority.

**Note on the deterioration triple (F2/F4/F7).** Three distinct lenses, not three copies: F4 is the absolute-risk actionable threshold; F2 is the forecast-based early warning; F7/AEGIS is the personal-baseline *silent* case that fires while F4 still looks fine. The demo scenario must dissociate them (gate G3) — if it cannot, AEGIS loses its reason to exist and collapses into F4.

---

## 6. Reach features (P1 / "if time")

Additive on top of the MVP core. Each degrades gracefully — if a reach is cut, the core is unaffected. **MAAFI build order: R1 → R4 → R3 → R2** — R4 (HERMES) is cheap, sits on F8, and is the only Challenge-2 bridge, so it banks a rubric point before the high-risk GNN; keep R3 ahead of R4 only with GNN confidence and a wow-over-Challenge-2 priority.

| ID | Feature | Description | Risk |
|---|---|---|---|
| **R1** | **History-as-prior** (Layer 3) | Theograph features as Cox / survival covariates; the live telemetry as the time-varying covariate. Conditions baseline, basin geometry, and forecast hazard. | Low–med. Uses existing survival stack. |
| **R2** | **CHARON — prospective Theograph (Monte Carlo)** | Extend the Theograph *past now* as a distribution of likely care-event futures. Three render modes: exemplar (median / P90 / crisis draws), intensity surface (per-cell event-rate heat-ribbons), prospective-with-bands (modal pathway + timing CIs + "occurs in X% of futures"). The discrete twin of the F2 cone. | Med. Generative point-process model + MC. |
| **R3** | **CADUCEUS — patient-as-graph GNN** *(headline reach goal)* | Model the patient as a graph: physiological signals as nodes, learned dynamic dependencies as edges. A GNN (GAT) predicts deterioration and surfaces *which couplings are driving the movement*. Explains the **why** beneath STYX's **where**. See §8. | High. GNN training in a hackathon window. Has a non-learned fallback. |
| **R4** | **HERMES — carer view** (Challenge 2) | One carer-facing screen reading the same state model in plain language: a simplified journey, a stable/attention status, one action. The Theograph's "no analytical training needed" virtue makes it the ideal carer artefact. | Low. Thin slice, high narrative value. |

---

## 7. Monte Carlo forecasting (CHARON) — design note

A care history is a **multivariate marked point process**: stochastic event arrivals per channel, with marks (type, duration) and cross-channel excitation (an A&E attendance lifts the near-term hazard of a non-elective admission). A *retrospective* Theograph shows one realised path. The moment we point it forward it becomes a forecast of a point process — inherently distributional — which is exactly what Monte Carlo delivers. So MC is not merely compatible with the Theograph format; it is what makes a *prospective* Theograph honest.

- **Generator:** a Hawkes process (self- and cross-exciting) as the natural cross-exciting model, or sampling the existing discrete-event engine; copulas for mark dependence if not using a full generative model.
- **Conditioning on partial history:** a particle filter / PDAF to propagate the patient's state and resample forward event trajectories — the forward extension is a particle cloud of futures.
- **Rare pathways:** importance sampling to harvest enough tail (ICU / death) draws to render a meaningful crisis-pathway Theograph without astronomically many runs.
- **Do not** overlay N raw Theographs — that is ink-soup (the spaghetti-plot failure). Aggregate to an intensity surface or select exemplars.
- **Audience split:** distributional encoding erodes the format's glance-legibility, so the intensity surface goes to the analyst/planning view; the clinician sees expected-path-plus-bands.

This sub-system maps directly onto the existing STOCHASM toolkit (Hawkes, PDAF, importance sampling, copulas, Sobol for parameter sensitivity).

---

## 8. CADUCEUS reach goal — deep dive

**What it is.** Model the patient as a graph where **nodes are physiological signals** (HR, SpO₂, RR, BP, temp, plus derived features such as variability or shock index) and **edges are the dynamic dependencies between them**, learned over sliding windows. A graph attention network (GAT) does message-passing over this graph to predict deterioration and, by inspecting its attention/edge weights, surfaces which couplings matter at any moment.

**Why it is the right reach goal.** The brief explicitly invites GNNs for mapping interactions between continuous physiological streams. CADUCEUS is the highest data-science ceiling in the corpus and gives STYX an **explanatory** layer: STYX shows *where* the patient is going in state space; CADUCEUS shows *why* — which physiological systems are decoupling. The demo line writes itself: *"the graph shows the RR–SpO₂ coupling broke at T+16 h, two hours before the trajectory crossed into the crisis basin — the model saw the systems come apart before any single signal breached threshold."*

**How it bolts onto STYX.**
- **Minimum coupling:** CADUCEUS is a side panel — the "why" beside STYX's "where." The current edge graph renders next to the trajectory; a decoupling event is highlighted and time-stamped against the trajectory's movement.
- **Deeper coupling (stretch-of-stretch):** the learned graph regularises or informs the latent embedding (graph-regularised state space), so STYX's geometry is *derived from* the physiological dependency structure rather than a generic projection.

**Graceful degradation (the hedge).** If the GNN does not train to anything convincing within the window, fall back to a **non-learned dynamic dependency graph** — windowed partial correlation or Granger causality between channels. This produces the *same coupling-map visual* and tells essentially the same "systems decoupled first" story, so the **mockup and narrative are achievable even if the model slips**. The reach is the *learned* version; the fallback protects the demo.

**Data.** Needs only the multivariate physiological streams already produced by F5; edges are computed from windowed inter-channel dependence. No new data source.

**Out of scope (note for future).** A GNN over the Theograph's cross-service *events* (care events as a graph) is conceptually adjacent but too far for the hackathon — flag as future work.

---

## 9. Data model & architecture

**The synthetic patient (F5).** One synthetic record carries two coherent strata:
- **Theograph history** — a multi-year event log across channels: primary care, A&E, non-elective admissions, outpatient, mental health, social care. Event density and channel mix encode a latent frailty.
- **Physiological episode** — continuous multi-stream telemetry for the virtual-ward stay, whose baseline, reserve, and crisis propensity are *conditioned on* that frailty. Deterioration scenarios are scripted (e.g. evolving sepsis / acute respiratory infection — pneumonia), replayable, and speed-controllable for the demo.

**Pipeline.**
```
Synthetic engine (F5)
  ├─ Theograph event log ──► event overlay (F3)
  │                          ├─► history-as-prior covariates + pre-admission baseline (R1)
  │                          └─► CHARON prospective forecast (R2)
  └─ Physiological streams ─► latent embedding (F1) ──► forecast cone (F2)
                          │                          ├─► risk waterline (F4)
                          │                          └─► CADUCEUS dependency graph (R3)
                          └─► personal baseline ──► AEGIS silent-deterioration flag (F7)

  risk drivers (F2/F4/F7) ──► CALLIOPE rationale (F8) ──► why-this-alert · HERMES · handover
  Completed episode ──► summarised to discrete events ──► appended to the Theograph (loop closes)
```

**Stack & front-end (decided).** Python core throughout (numpy / scipy / scikit-learn; survival via lifelines or the existing Cox/DeepSurv stack; PyTorch / PyTorch-Geometric for the CADUCEUS reach). **Front-end: Streamlit + Plotly** — chosen over React/JS for the hackathon because it keeps the model and the UI in one Python process (no API boundary to build or break in two days), it's the fastest path for a solo build, and the bound visuals (latent map, cone, waterline, swimlane, graph) are all expressible as Plotly figures redrawn each rerun; the replay loop is a Streamlit auto-refresh advancing the clock and re-scoring the cohort (the A2 serving model above). Bespoke static set-pieces (e.g. a CARTOGRAPHER discharge poster) drop in as templated SVG via `st.components.v1.html`. **React is the deployment-horizon rebuild** — React/D3 against the A3 API — mirroring the A2→A3 path: Streamlit now, React later, `styx/` unchanged. `seed=42` throughout; append-only `EXPERIMENT_LOG.md`; one `CLAUDE.md`.

**Repo layout.** Logic lives in an importable package; the app, the notebooks, and the tests are *thin clients* of it — the UI holds no logic, the evidence notebooks import rather than reimplement (§14.2), and swapping Streamlit for a React+API client later touches nothing in `styx/`.
```
styx/                      # the package — all logic, imported everywhere
  config.py                #   seed=42, cadence, thresholds, vital set
  synth/                   #   F5 generator · scenario · cohort · replay
  state/                   #   F1 embedding · basin/attractor
  forecast/                #   F2 forecast · conformal bands
  risk/                    #   F4 risk + escalation · F7 AEGIS
  rationale/               #   F8 CALLIOPE (template over attributions)
  theograph/               #   F3 event model + overlay data
  cohort/                  #   F6 ward ranking · F10 ECHO similarity
  reach/                   #   R1 prior · R2 CHARON · R3 CADUCEUS · R4 HERMES
  viz/                     #   Plotly figure builders (data → figure), shared by app + notebooks
app/                       # Streamlit — thin UI over styx + styx.viz
  app.py                   #   entry; replay controls, patient selector
  pages/                   #   patient view · ward board
notebooks/                 # jupytext .py gate-evidence (01–05), import styx
tests/                     # test_g1.py … the gate tests (pytest)
data/  outputs/            # generated synthetic data / figures (gitignored)
CLAUDE.md  BUILD_MVP.md  EXPERIMENT_LOG.md  pyproject.toml  README.md
```

**Serving architecture (red-team verdict — `ARCH_REDTEAM_STYX.md`).** STYX is a *trend / trajectory* monitor, not an acute-spike detector, so per-event streaming is low-value and high-cost for it. The MVP serves as **A2-simple: a windowed re-score of the synthetic cohort over replay** — no streaming infrastructure, one slice — with the re-score cadence owned by gate G3 (the window must preserve the AEGIS→threshold lead). **Conformal, quality-gated outputs are a standing requirement, not a mode** — the uncertainty-first option dissolves into F2's cone + SENTINEL. The **deployment target is A3 (hybrid)**: streaming feature aggregation → frequent re-score against FHIR-shaped events; the data contract is shaped for it now (Appendix A) even though the MVP doesn't run it. The demo is *replay, not live*, and the pitch says so plainly — claiming an unbuilt streaming stack is what judges catch, and honesty is SENTINEL's point.

---

## 10. Mockups — key screens

Six screens. Screen 2 has already been prototyped (the integrated patient view shown earlier in this session). Screens 1 and 4 are rendered alongside this PRD; the rest are specified here for build.

1. **Ward board (triage / landing).** The clinician's entry point. Roster of patients sorted by predicted time-to-escalation; per-patient heat-strip of risk over the stay; a small latent-state thumbnail per patient; "quietest patient" (safe to deprioritise) and "newly admitted / low history" flags; a capacity lens for the duty manager (discharge-readiness leaderboard). *(Rendered below.)*

2. **Patient view (STYX × Theograph).** The integrated hero: lifelong Theograph ribbon (context) on top; the latent state-space map with basin, attractor, trajectory, *now* marker and forecast cone in the middle; the risk waterline with time-aligned care events beneath. Care events thread onto the trajectory (a Theograph event visibly bending the path back into the basin). *(Already prototyped.)*

3. **Prospective forecast (CHARON).** The Theograph extended past *now*: future swimlanes with event-probability glyphs (opacity = P(occurs)) and timing whiskers, plus a mode toggle to the intensity-surface heat-ribbon view for the analyst audience. The discrete companion to the forecast cone.

4. **Why-panel (CADUCEUS).** The reach-goal view: the patient-as-graph — physiological signals as nodes, edge thickness = current coupling strength — with a broken/weakening edge highlighted and time-stamped against the trajectory ("RR–SpO₂ decoupled, T+16 h"). Sits beside the state-space map. *(Rendered below.)*

5. **Carer card (HERMES, Challenge 2).** Phone-sized, plain language: a simplified journey ribbon, a stable/attention status derived from the same model, and one clear action ("message the team"). No numbers, no jargon — the Theograph's at-a-glance virtue applied to family.

6. **Trust drawer (SENTINEL).** A pull-out showing sensor health / missingness per stream and how it is currently discounting confidence — the honest-uncertainty receipts behind every other view.

---

## 11. Demo narrative (3 minutes)

1. **Legibility hook** (§473) — open with the contrast: a standard multi-line vitals dashboard beside the STYX trajectory view, same patient, one unreadable and one legible in a second.
2. Open the **ward board** — twelve synthetic patients; one is quietly climbing the triage order on the silent-but-rising watchlist.
3. Open that patient. The **Theograph ribbon** shows an elderly, frail history (escalating A&E, social care). The **trajectory** is drifting off the recovery corridor toward the crisis attractor; the **ghost trail** shows where they'd be on yesterday's trend.
4. Hit play. The **forecast cone** leans toward crisis and the **risk waterline** climbs. **AEGIS fires the silent-deterioration flag before the escalation threshold**, and **CALLIOPE** writes the one-line reason ("rising RR, falling SpO₂ over 3 h"). Anticipation, not reaction.
5. **ECHO** surfaces three similar past patients — two recovered, one escalated — anchoring the forecast in cases.
6. *(Reach)* Open the **CADUCEUS why-panel**: the RR–SpO₂ coupling decoupled two hours before the trajectory turned — *the model saw the systems come apart first*.
7. *(Reach)* The **CHARON** forecast shows the distribution of likely next care events — a non-elective admission probable within 24 h.
8. *(Challenge 2)* The **HERMES card** has already sent the carer a calm, plain-language nudge — CALLIOPE's words, lay-translated — to contact the team.
9. The episode ends; its events **append to the Theograph** — history for the next clinician. The loop closes.

---

## 12. Success criteria (rubric alignment)

| Rubric criterion (weight) | How STYX scores |
|---|---|
| Clinical impact / decision value (22) | Anticipation before threshold; triage by time-to-escalation; history as context. |
| Data-science depth & novelty (18) | Latent state space + survival forecast (core); GNN + MC point-process forecast (reach). |
| Visual / UX clarity (18) | One legible hero visual; glance-readable board; honest uncertainty encoding. |
| Hackathon feasibility (15) | Core (F1–F11) standalone; reaches (R1–R4) additive and individually droppable. |
| Demo-ability / judge wow (12) | Live, speeded deterioration; "saw the systems decouple first"; the closing loop. |
| Data availability (6) | Self-supplied synthetic engine — no data dependency. |
| Trust / validation / safety (5) | SENTINEL quality-gating folded throughout. |
| Challenge-2 bridge (4) | HERMES on the same model. |

### 12.1 Evaluation & metrics

The pitch's defensible numbers, not just AUC:
- **Lead-time gained** (§460, §478) — warning time vs a reactive threshold; train explicitly to maximise it (§217). The headline figure.
- **Alarm-burden** (§461) — alerts per patient-day, to demonstrate fatigue reduction.
- **Calibration** (§462, §104) — a calibration ribbon so probabilities mean what they say.
- **Failure-case gallery** (§465) — documented cases where the model breaks (your per-session failure-case discipline, applied to the demo).
- **Reproducibility** (§469) — fixed `seed=42`, logged experiments. RAIE by default.

---

## 13. Risks & mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| GNN (CADUCEUS) does not converge in time | High | Non-learned partial-correlation / Granger fallback renders the same visual + story (§8). |
| Synthetic data feels arbitrary / incoherent — **and is the single point of failure** (six features' value is gated on what F5 scripts) | High | **G1 (§14.1)** blocks the build until the synthetic patient demonstrably contains the phenomena the features must detect; make history *causally* drive physiology; tune one condition well, not many badly. |
| Latent embedding unstable or unintuitive | Med | **G2 (§14.1)** — start with PCA/UMAP; if the axes aren't legible, fall back to a labelled clinical two-axis. Only attempt a VAE/latent-ODE if time. |
| Scope creep across reaches | High | MAAFI tiering + the Slice-5 MVP gate; reaches strictly additive; pick by remaining time, not ambition. |
| Demo fragility (live compute) | Med | Pre-baked `seed=42` scenarios; replay rather than live-compute on stage. |
| Distributional views illegible to clinicians | Med | Audience split — intensity surface to analysts, expected-path-plus-bands to clinicians. |

---

## 14. Build plan — RAIE vertical slices

Each slice is a 50–100 LOC vertical increment with a logged result. Gates (§14.1) sit at slice boundaries; the build does not advance past a red gate.

- **Slice 0 — setup.** Repo, `CLAUDE.md`, `EXPERIMENT_LOG.md`, `seed=42`, deps.
- **Slice 1 — synthetic engine (F5).** One condition; coherent history → physiology; scripted deterioration; replay + speed control. Emit the features the detectors need (HRV loss, SpO₂ desaturation, HR–RR coupling). **→ Gate G1 (synthetic fidelity).**
- **Slice 2 — state space (F1).** Embed the physiological vector (PCA/UMAP first); static trajectory; cohort-derived basin/attractor. **→ Gate G2 (state legibility).**
- **Slice 3 — forecast, risk, silent-deterioration (F2, F4, F7).** Forecast cone + conformal bands; risk waterline + escalation threshold; AEGIS personal-baseline + change-point flag. **→ Gate G3 (anticipation dissociation).**
- **Slice 4 — Theograph overlay + ghost trail + rationale (F3, F9, F8).** Events on the trajectory + time-aligned strip; counterfactual ghost trail; CALLIOPE one-line rationale. **→ Gate G4 (rationale faithfulness).** *Minimum single-patient demo complete.*
- **Slice 5 — ward board + echoes (F6, F10).** N patients; sort + silent-but-rising watchlist + flags + focus mode; ECHO similar-patient overlays. **← 10-feature MVP gate.**
- **Slice 6 — reach (MAAFI order, pick by time).** R1 (history-as-prior) → R4 (HERMES, thin slice on F8) → R3 (CADUCEUS: coherence graph first, GNN if time) → R2 (CHARON).
- **Slice 7 — polish.** Demo flow (incl. the legibility A/B), SENTINEL confidence encoding, the closing-loop append.
- *(Deferred to pilot: F11 workflow touches.)*

### 14.1 Go/no-go gates

*Go/no-go gates* (fail-stop: on fail, the build halts rather than proceeding broken). Each gate is **set in advance**, has a **binary, measurable pass condition**, and a **pre-committed fallback** — so a failure triggers a named response, not improvisation or a foundation quietly left broken. They sit at the slice boundaries in §14.

**G1 — Synthetic fidelity** · *after Slice 1* · the root gate.
The dominant MAAFI finding: F5 is the single point of failure, and its scenario is the contract the MVP depends on. Pass requires all of the following, reproducibly at `seed=42`:
- *Determinism* — two runs at `seed=42` produce identical streams and event logs.
- *Dissociable silent case* — at least one patient has a window where every vital stays inside its normal range while the multivariate trend is adverse (a trend detector should fire where an absolute-threshold check would not).
- *Genuine decoupling* — at least one patient shows a real inter-signal decoupling (e.g. windowed RR–SpO₂ coherence dropping below baseline) that precedes any single-signal threshold breach by a set lead (≈ 90 min sim-time).
- *Coherent cohort with outcomes* — ≥ 12 patients, varied trajectories, labelled outcomes, with outcome correlated to history (frailty → worse) strongly enough that a simple model beats chance; i.e. the prior is learnable.
**On fail:** stop and fix the generator. No downstream model is meaningful on a substrate that lacks the phenomena it must detect. This is the one gate with no "proceed anyway" path.

**G2 — State legibility** · *after Slice 2*.
**Pass:** each 2-D latent axis correlates with a named physiological construct at |r| ≥ 0.6 (e.g. axis 1 ↔ oxygenation, axis 2 ↔ effort/perfusion), *or* a clinician (or proxy) correctly labels three held-out trajectories as improving / stable / deteriorating.
**On fail:** fall back to a hand-built, labelled clinical two-axis projection (oxygenation × effort). Never ship an unreadable embedding as the hero.

**G3 — Anticipation dissociation** · *after Slice 3* · *also owns the serving cadence (§9)*.
**Pass:** on the demo scenario the three deterioration signals fire *in order* — AEGIS (F7) during the silent window first, the forecast cone (F2) crossing threshold next, F4's absolute threshold last — with a measurable lead between AEGIS and F4 (this lead *is* the "lead-time gained" headline, §12.1). The chosen re-score cadence must preserve that lead — too coarse a window erases it.
**On fail:** tighten the re-score cadence, re-script the F5 scenario (back through G1), or re-tune the AEGIS baseline window. Never present three signals firing together (the "which one caught it?" failure).

**G4 — Rationale faithfulness** · *before shipping F8 / R4*.
**Pass:** on a held-out set, the signals CALLIOPE names match the model's actual top-_k_ attribution — top-1 agreement ≥ 90%, and no rationale ever names a signal outside the model's top contributors.
**On fail:** lock CALLIOPE to a strict template populated only from the real attribution vector; if even that cannot be trusted, revert to a fixed one-liner (the MVP cut-order contingency). Never ship free-form narration.

**Milestone gate — 10-feature MVP** · *after Slice 5*. The MVP demos end-to-end on the pre-baked scenario, on the demo machine, from the recorded fallback if needed. A checkpoint, not a fail-stop — but no reach starts until it is green.

**Claim-integrity principle** (governs every reach). Never narrate a phenomenon the data does not contain. A reach's headline claim — CADUCEUS's "the model saw the systems decouple first" — is made only if it is verifiable on the scenario (for CADUCEUS, this leans on G1's decoupling check). If it is not verifiable, the visual is illustrative only, or the claim is cut.

### 14.2 Evidence notebooks

Thin jupytext `.py` notebooks that import `styx` and turn each gate into visible proof — the rigour layer behind the app, not a second demo surface and not where the app is built. Produced *as* each gate is cleared (after its slice), never upfront.

| Notebook | Proves | Output feeds |
|---|---|---|
| `01_synthetic_fidelity` | G1 — the synthetic patient has a dissociable silent window, a genuine decoupling, a learnable cohort | gate G1; the "is the test fair?" answer |
| `02_state_space` | G2 — the latent axes are interpretable; the map is legible | gate G2 |
| `03_anticipation_lead` | G3 — the signals fire in order; the AEGIS→threshold lead, measured | gate G3; **the headline pitch number** |
| `04_rationale_faithfulness` | G4 — CALLIOPE's named signals match the model's real attributions | gate G4; the trust story |
| `05_methods_story` *(optional)* | the end-to-end DS narrative — embedding, forecast, conformal coverage, calibration | technical-judge backup; DS-depth marks |

Rules that keep them cheap: import the package (never reimplement); build each after its slice's gate is green; jupytext `.py` in the repo, render to `.ipynb` only for sharing; the Streamlit app stays the single demo surface.

---

## 15. Open questions

- ~~Which single condition anchors the demo — post-op sepsis, COPD exacerbation, or heart-failure decompensation?~~ **Resolved: acute respiratory infection (pneumonia / happy-hypoxia)** — it matches the modelled physiology (healthy SpO₂ baseline, silent on-air desaturation, flat effort) and gives the clearest decoupling story; the NEWS2 comparator uses Scale 1 accordingly.
- ~~Streamlit + Plotly, or a bespoke web front-end?~~ **Resolved: Streamlit + Plotly** (§9); React is the deployment-horizon rebuild.
- Latent embedding: stable-but-generic (PCA/UMAP) for the core, with a VAE/latent-ODE only as its own reach?
- Does the ward board lead, or the patient view? (Judging-narrative decision.)

---

## Appendix A — Background ideas (considered, deferred)

Logged from the ideation cross-check for provenance. **Not committed to this build** — referenced so the design space and its lineage are preserved. Numbers are corpus idea references in `virtual_wards_ideation.md`.

**Reach-strengtheners — would sharpen R1–R3 if pursued.**
- *CADUCEUS (R3):* reframe the headline as edge-*prediction* — forecast the emerging abnormal coupling before single signals move (§187); regularise training with physiology-informed graph priors so it works on little data (§190); make the non-learned fallback windowed coherence between signal pairs (§248), more specific than Granger; natural extension — predict the likely *cause*, narrowing the differential (§490).
- *CHARON / forecast:* a switching state-space / HMM with labelled stable/watch/critical regimes for a legible layer (§250); competing risks — deteriorate vs discharge vs transfer (§223); a single simple scalar for HERMES, "stability half-life" (§230).
- *R1 history-as-prior:* §384 (pre-admission baseline import) is the Theograph→baseline mechanism by name; a MORPHEUS phenotype label (§195, §199) with phenotype-switching as an AEGIS signal (§201); the attribution partition (§276) is shared IP with FAER-BEACON.
- *TOPOS (giotto-tda):* loss of a stable physiological loop as a *second* early-warning channel (§309), with topological features feeding the predictor (§308) — an existing asset that backstops CADUCEUS's story.

**Output artefact — CARTOGRAPHER (concept #11).** A Minard-style discharge / handover summary auto-generated from the stay — flow width = stability, colour = risk, annotations = interventions (§62, §69, §66, §502). It is the *visual form of the loop-close* and subsumes the handover-builder (§166); print-first for poor-connectivity wards (§74). The natural "what we'd do next" deliverable and a fit for the Minard aesthetic.

**Data-contract & realism nudges — cheap credibility (FHIR shaping is now a Phase-2 enabler for the A3 target).** Shape the Theograph event schema as FHIR / SNOMED-coded so the stub isn't a toy *and so the A3 deployment target can ingest it unchanged* (§449, §451); state the synthetic engine as the information-governance answer — no real data in the demo (§345, §348); have the engine emit the features that matter so the models have signal — HRV loss (§283, §46), SpO₂ desaturation events (§285), HR–RR phase coupling (§292) — with adjustable difficulty (§358) and a counterfactual-scenario mode (§362) for the demo.

**Optional wow — low priority.** Ambient sonification + ward-wall — SONUS (§144, §141, §486); an avatar that visibly looks unwell as risk rises (§485); an LLM "ward registrar" answering free-text questions over the cohort (§487, valuable if CALLIOPE's NL layer exists anyway); a risk-momentum quadrant as a compact companion panel (§42); expected-value-of-information — which extra measurement would most reduce uncertainty (§331).

**Consciously left out — scope discipline.** The full JANUS POMDP policy (keep only the F9 ghost trail), TOPOS as a headline view (keep it a feed), the entire 3-D / VR / immersive cluster bar a throwaway WebXR (corpus L), FHIR *integration* (stub only), foundation-model pretraining (corpus Y), full multimodal fusion (corpus W). These are the tempting-but-fatal additions for a two-day build — the §13 scope-creep risk made concrete.
