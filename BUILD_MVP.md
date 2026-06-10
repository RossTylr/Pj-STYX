# BUILD_MVP.md — STYX build order

## How To Use This

Read with `CLAUDE.md`. **One slice per Claude Code session, 50–100 LOC, in order.**
Per slice: build → run the gate test (must be green) → write the proof notebook →
append the result to `EXPERIMENT_LOG.md` → commit → next.

**Do not advance past a red gate. G1 has no fallback.**

MVP = `{F5, F1, F2, F4, F7, F3, F8, F6, F9, F10}` (10 features). Reaches come after
the milestone gate, in order **R1 → R4 → R3 → R2**.

## Gates (stop conditions)

| Gate | After | Pass | On fail |
|------|-------|------|---------|
| **G1** Synthetic fidelity | S1 | determinism (`seed=42`); a dissociable silent window; a genuine RR–SpO₂ decoupling with ≥90 min lead; a ≥12-patient cohort with learnable outcomes | **stop, fix the generator** (no proceed) |
| **G2** State legibility | S2 | each latent axis \|r\|≥0.6 with a named construct, or a proxy reads 3 trajectories right | fall back to a labelled clinical 2-axis (oxygenation × effort) |
| **G3** Anticipation dissociation | S3 | on the scenario: AEGIS → forecast → threshold, in order, with a measurable AEGIS→threshold lead the cadence preserves | tighten cadence; re-script F5 (→ G1); re-tune AEGIS baseline |
| **G4** Rationale faithfulness | S4 | CALLIOPE's named signals match the model's top-k (top-1 ≥90%); no out-of-set signal | strict template over the attribution vector; else a fixed one-liner |
| **Milestone** 10-feature MVP | S5 | MVP runs end-to-end on the pre-baked scenario (from the fallback recording if needed) | — (no reach starts until green) |
| **Claim-integrity** | every reach | the reach's headline claim is verifiable on the scenario | visual illustrative only, or cut the claim |

---

## S0 — Scaffold

**Objective:** repo skeleton that runs.
**Build:** the repo layout — `styx/` package with module dirs (`synth state forecast risk rationale theograph cohort reach viz`) + `config.py` holding `SEED=42`, `RESCORE_CADENCE`, thresholds, `VITALS`; `app/app.py` stub + `app/pages/`; `notebooks/`; `tests/`; `CLAUDE.md`; `EXPERIMENT_LOG.md`; `pyproject.toml` (deps: numpy, scipy, scikit-learn, lifelines, streamlit, plotly, jupytext, pytest, ruff); `.gitignore` (`data/`, `outputs/`).
**Gate:** none — `streamlit run app/app.py` launches; `pytest` collects.
**Done when:** skeleton runs; `CLAUDE.md` committed.

## S1 — Synthetic engine (F5) · `styx/synth`

**Objective:** one coherent synthetic patient + cohort, deteriorating on cue.
**Build:** a generator where a multi-year Theograph history (event density → latent frailty) *conditions* the physiological episode's baseline, reserve, and crisis propensity. One condition (acute respiratory infection — pneumonia / happy-hypoxia; *not* COPD — see scenario.py). Script: a **dissociable silent window** (vitals in range, trend adverse) and a **genuine RR–SpO₂ decoupling** preceding any single-signal breach by ≥90 min. **≥12-patient cohort** with labelled outcomes correlated to history. Tight `VITALS` (RR, SpO₂, HR, temp + one labs proxy). Replay + speed; expose `rescore_cadence`.
**Gate:** **G1**. `tests/test_g1.py`.
**Proof:** `notebooks/01_synthetic_fidelity` — plot the silent window, the decoupling + lead, the cohort outcome-vs-history correlation.
**Done when:** `test_g1.py` green; G1 evidence renders; log entry.

## S2 — State space (F1) · `styx/state` + `styx/viz`

**Objective:** the legible trajectory hero.
**Build:** embed the `VITALS` vector to 2-D (PCA/UMAP first). `styx/state`: fit the embedding, learn the stability basin + crisis attractor from the cohort, compute the now-position. `styx/viz`: a pure builder `trajectory_figure(patient, embedding, basins)` → path + now-marker + shaded basin/attractor. Report axis↔physiology correlations.
**Gate:** **G2** (fail → labelled oxygenation × effort 2-axis).
**Proof:** `notebooks/02_state_space` — axis correlations + three labelled trajectories.
**Done when:** trajectory renders; G2 green; log entry.

## S3 — Forecast, risk, AEGIS (F2, F4, F7) · `styx/forecast` + `styx/risk`

**Objective:** anticipation, dissociated.
**Build:** `styx/forecast`: short-horizon forecast + conformal residual bands → cone. `styx/risk`: a risk score + escalation threshold (continuous gradient, not a traffic light); **AEGIS** = personal baseline (learned in the first hours) + change-point → silent-deterioration flag. Re-score the cohort on `rescore_cadence`. `styx/viz`: `cone_figure`, `waterline_figure`.
**Gate:** **G3**. `tests/test_g3.py`.
**Proof:** `notebooks/03_anticipation_lead` — firing order + the measured AEGIS→threshold lead (**the headline number**).
**Done when:** dissociation holds at cadence; G3 green; log entry.

## S4 — Overlay, ghost, rationale + patient page (F3, F9, F8) · `styx/theograph` + `styx/rationale`

**Objective:** the integrated single-patient view (minimum demo).
**Build:** `styx/theograph`: care-event model; `styx/viz`: events threaded onto the trajectory + a time-aligned swimlane strip beneath the waterline; **ghost trail** (re-run the forecast from an earlier anchor). `styx/rationale`: **CALLIOPE** — a strict template populated from the model's top-k attribution. First Streamlit patient page (`app/pages/`) wiring map + cone + waterline + overlay + rationale, driven by the replay clock.
**Gate:** **G4**. `tests/test_g4.py`.
**Proof:** `notebooks/04_rationale_faithfulness` — attribution-agreement check.
**Done when:** single-patient demo runs; G4 green; log entry.

## S5 — Ward board + ECHO (F6, F10) · `styx/cohort`

**Objective:** the 10-feature MVP.
**Build:** `styx/cohort`: rank by time-to-escalation; silent-but-rising watchlist; "quietest" / "new low-history" flags; focus mode; **ECHO** = similarity over the embedding → 3 nearest past patients + outcomes. Ward-board Streamlit page; click a patient → drill into the S4 patient view.
**Gate:** **Milestone** — MVP end-to-end on the pre-baked scenario.
**Proof:** `notebooks/05_methods_story` *(optional)* — end-to-end DS narrative (embedding, forecast, conformal coverage, calibration).
**Done when:** MVP runs end-to-end; **tag the commit**.

## S6 — Reaches · `styx/reach` (order: R1 → R4 → R3 → R2)

Each additive and droppable; **claim-integrity** governs every one.
- **R1 history-as-prior:** Theograph features as Cox / survival covariates; telemetry as the time-varying covariate; condition baseline, basin geometry, hazard.
- **R4 HERMES:** a carer Streamlit page reading the same state in plain language (CALLIOPE, lay-translated) + a simplified journey + one action.
- **R3 CADUCEUS:** signals-as-graph. **Start with the non-learned windowed-coherence graph** (renders the same decoupling visual); GNN (GAT) only if time. Claim the "decouple first" line *only* if G1's decoupling is real.
- **R2 CHARON:** prospective Theograph — Monte Carlo forward event distribution; expected-path + bands for the clinician, intensity surface for the analyst.
**Done when:** each reach that lands passes claim-integrity; log entry.

## S7 — Polish

**Build:** the standard-dashboard-vs-STYX legibility A/B; SENTINEL confidence encoding across views; the closing-loop append (completed episode → new Theograph events); record a fallback video; frame the demo as **replay-of-synthetic, A3 as the deployment target**.
**Done when:** demo dry-run passes on the demo machine; pitch-ready.
