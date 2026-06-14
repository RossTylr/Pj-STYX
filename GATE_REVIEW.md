# GATE_REVIEW.md — STYX

Append-only. One read-only MAAFI Red-Team + Arbiter pass per gated slice. **Sensors, not
actuators:** these reviews recommend; a human signs the gate. Do not self-pass.

---

## MAAFI Red-Team + Arbiter — ward-ux-p0 (2026-06-14)

### Findings

| Severity | Area | Finding | Evidence |
|----------|------|---------|----------|
| (clean) | scoring-path isolation | Determinism sentinel byte-identical; scoring path provably untouched. `pipeline_digest(build_cohort(seed=42))` == recorded `9ea38949…a5347`. | `tests/test_baseline.py:17`; `tests/test_observations.py:27`; live recompute MATCH |
| nit | scope | Diff touches more than "ward rendering": `styx/readouts.py` adds `news2_subscores_at` and `styx/viz/palette.py` adds brand-chrome tokens. Both are off the scoring path (verified by the unchanged digest), but they exceed the spec's literal "ward rendering only" wording. `readouts` change is a legitimate read-only slice the card needs; palette change belongs to a different (brand) slice bundled in. | `styx/readouts.py:161-175`; `styx/viz/palette.py:10-22` |
| minor | oracle adequacy | `test_baseline.py` only asserts run-A == run-B; it does **not** pin against the recorded constant. The hard pin lives in `test_observations.py:27`. Both green, so covered — but the regression invariant relies on a *different* test file than the one named "baseline". | `tests/test_baseline.py:31-34` vs `tests/test_observations.py:118` |
| nit | accessibility (colour-not-alone) | The badge dot (`.styx-dot`) is identical round shape for flagged and calm, differentiated by accent colour. Redundant non-colour cues do exist (left accent bar present only when flagged, bolder verdict, distinct badge/verdict text), so it is not colour-alone — but the target HTML uses a warning-triangle glyph for the flagged badge (an explicit shape cue) that the implementation drops. | `styx/viz/board.py:214,280`; target `docs/ward_card_target.html:63-67` |
| nit | oracle gaps | `test_ward_ux.py` P0-3 ordering test checks only the silent case (Bed 0). It does not assert ordering on a *non-silent* flagged bed, nor that calm cards omit the verdict-state token. (`test_board.py` covers calm/flagged builders directly, so the gap is mitigated at unit level.) | `tests/test_ward_ux.py:78-85` |

### Red-team narrative

**Scoring-path leak — none.** The headline risk for a "presentation-only" slice is a silent change to the determinism digest. It holds: recomputing the full pipeline digest at seed=42 yields `9ea38949db8e5b8c19f969b9919d804013285fb78e0e48f5449c7e76336a5347`, byte-identical to the recorded sentinel. No `synth/`, `cohort`, `scorer`, `forecast`, `risk`, or `embedding` file is in the diff. `news2_subscores_at` (`readouts.py`) is a read-only column slice of the existing `_news2_complete_subscores` comparator — no new maths, asserted in `test_board.py`. `vital_reading` (`board.py`) reads `patient.vitals[key]` only, which is permitted.

**Fabricated data — none.** Every card value is sourced: SpO₂/RR from `patient.vitals`; the "(was X)" prior is a real early-stay baseline (`series[:24].mean()`) — honest, not invented. NEWS2 aggregate is the existing comparator. The sparkline is the real STYX risk history; empty-history returns `""` rather than a fabricated line.

**P0-1 (typography) — compliant.** Rendered state labels are constrained to `APPROVED_STATES` and enforced at the app layer. Live render: flagged cards carry only `deteriorating — silent`; badges are `early signal`/`stable`/`recovering` — the off-vocabulary long forms (`silent-hypoxia-like`) are retired. No soft hyphen. CSS injects `overflow-wrap:normal; word-break:keep-all; hyphens:none` — the wrap fix itself is a visual-gate item (AppTest sees markup, not CSS), correctly flagged in the spec notes.

**P0-2 (SpO₂) — compliant.** Cards render the `SpO₂ 91% ↓ (was 96)` form. Live scan: only percentage tokens appear; zero bare `SpO₂ [0-3]` across both ward and patient pages. The patient page never emits a bare SpO₂ label (it uses SpO2 only as a plotted axis), so the cross-app guard is honest, not vacuous.

**P0-3 (hierarchy inversion) — compliant.** On flagged cards the `styx-verdict` element precedes `styx-news2-foot` in DOM order (asserted in `test_ward_ux.py` and `test_board.py`). The accent (`--accent`) owns dot, border/left-bar, and verdict text together, so the encodings cannot disagree. NEWS2 is genuinely demoted: a muted foot line reading `NEWS2 2 · below trigger`.

**Oracle adequacy.** Mostly sound and hard to game: the SpO₂ regexes test the contiguous stripped-text token and the approved-set test runs the real page across all flagged cards, not just one. Two soft spots: the P0-3 ordering AppTest exercises only the silent Bed 0, and `test_baseline.py` self-compares rather than pinning the constant (the pin is in `test_observations.py`). Both are mitigated by sibling unit tests and do not let the UX ship wrong.

**Spelling / accessibility / LOC.** User-facing copy is UK-clean. Colour-not-alone holds via redundant bar/weight/text cues, though the target's warning-triangle shape glyph was dropped to a plain dot (cosmetic, non-blocking). Production LOC is within reasonable bounds for the slice, the CSS block being the bulk and inherently presentation.

### Arbiter verdict

**RECOMMEND-PASS-WITH-NITS.** The slice does exactly what P0-1..P0-3 require, matches the Bed 6 / Bed 9 target in substance, and — most importantly for a presentation slice — leaves the scoring path provably untouched (digest byte-identical to `9ea38949…a5347`). All relevant tests pass. The findings are nits and one minor: the diff bundles two adjacent off-scope-but-off-path changes (a `readouts` display helper and brand palette tokens), the regression pin lives in `test_observations` rather than the file named `test_baseline`, the P0-3 AppTest only exercises the silent bed, and the target's flagged-badge triangle glyph was simplified to a dot. None compromise clinical safety or the determinism invariant; they are worth a follow-up note, not a block.

**Gate status:** sensor, not actuator. The **G-ward-ux gate is left for human sign-off — not self-passed.** The visual-gate items (mid-word wrap at the demo viewport, flagged-outranks-stable, before/after screenshots) remain to be confirmed by a human against the running app, as the spec requires.
