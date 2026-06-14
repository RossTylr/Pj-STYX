# STYX ward-board UX hardening — fix spec

slice: `ward-ux-p0` (assign the canonical S-id in `features.json`; suggest a presentation slice after the current one)
gate: `G-ward-ux` — human sign-off in `GATE_REVIEW.md`. Do NOT self-pass.
seed: 42
scope: **presentation layer only** (`styx/` ward rendering). No change to cohort generation, scorer, embedding, or anything on the scoring path.
visual target: `ward_card_target.html` — Bed 6 (flagged treatment) and Bed 9 (stable, receding) are the look to match.

---

## Invariant guard — must hold before AND after the slice

- baseline `pytest -q` GREEN before any edit. If red, stop and report.
- determinism sentinel: the SHA-256 double-run hash of the scored cohort is **byte-identical** pre/post. A presentation slice that changes the hash has leaked into the scoring path — STOP and revert.

---

## P0 — ship before the next demo

### P0-1  Kill typographic breakage
**Problem.** Card labels break mid-word (`recoveri/ng`, `escalati/on`, `silent-/hypoxia/-like`). Reads as unfinished regardless of model quality.
**Change.**
- (a) inject card CSS: `overflow-wrap: normal; word-break: keep-all; hyphens: none;`
- (b) replace long state strings with the approved short-label set.
- (c) size cards / reduce columns so approved labels never wrap mid-word.

approved state labels: `silent hypoxia`, `stable`, `recovering`, `early signal`, `deteriorating — silent`.

**Accept (AppTest, data layer).** Every rendered state label ∈ approved set; no label contains a soft hyphen (U+00AD) or a mid-token hyphen-break.
**Accept (visual gate).** No mid-word break at the demo viewport width; matches `ward_card_target.html`.

### P0-2  Disambiguate SpO₂
**Problem.** Cards show `SpO₂ 1` / `SpO₂ 2` — reads as a 1–2% saturation (an emergency), or an unlabelled NEWS2 sub-score, or Scale 1 vs Scale 2. Three readings, one of them critical. Unsafe on a clinical surface.
**Change.** Render the actual saturation as a percentage with a trend glyph and prior value, e.g. `SpO₂ 91% ↓ (was 96)`. Never emit a bare `SpO₂ <small int>`.
**Accept (AppTest).** For every patient card, the SpO₂ token matches `/SpO.? ?\d{2,3}%/`; **zero** matches for a bare `/SpO.? ?[0-3]\b/` across the rendered app. (Adapt the pattern to your actual label token — `SpO2` vs `SpO₂`.)

### P0-3  Invert card hierarchy for flagged patients
**Problem.** Green dot + large NEWS2 number dominate every flagged card; the STYX verdict is small wrapping text. The signal STYX exists to surface is buried under the reassuring one.
**Change.** For STYX-flagged patients, the STYX verdict (state + trend + lead-time) is the **primary** element; NEWS2 becomes a muted counterpoint line (`NEWS2 2 · below trigger`). The status colour (amber / red) owns dot + border + verdict together so the encodings cannot disagree. Match Bed 6 in `ward_card_target.html`; stable patients take the Bed 9 (receding) treatment.
**Accept (AppTest, markup).** Flagged-card markup contains the STYX-verdict element and a demoted NEWS2 line; the verdict element precedes the NEWS2 line in DOM order.
**Accept (visual gate).** Flagged cards visibly outrank stable cards; stable cards recede.

---

## P1 — same slice only if time, else next slice

- **bay header propagates STYX.** A bay containing a flagged patient cannot read `STEADY`. Add a STYX count alongside the NEWS2 stats. (This is the safety-inversion finding: the bay summary currently lulls.)
- **rail triage.** Rank flagged patients by lead-time / model confidence, cap the visible set to ~6, reds first and larger, collapse the rest behind `+N watch`. Today ~36% of the ward lights amber and the two reds are lost in the crowd.
- **single severity colour system.** Reserve green for genuinely stable patients only.

## P2 — polish (not this slice)

- sparkline normal-range band + endpoint dot, so a rising line reads as leaving normal.
- labelled bay metrics; consistent vertical rhythm.

---

## Definition of done (this slice)

1. P0-1..P0-3 implemented; new AppTest invariants green; baseline `pytest -q` still green.
2. determinism hash byte-identical to the boot baseline.
3. before/after screenshot attached for the visual gate (run the app locally).
4. one vertical-slice commit (presentation only); `features.json` status flipped; `EXPERIMENT_LOG.md` appended (append-only).
5. read-only MAAFI Red-Team + Arbiter pass appended to `GATE_REVIEW.md`. Human signs `G-ward-ux`.

## Notes

- **AppTest sees the element/markup tree, not rendered CSS.** The CSS wrapping fix (P0-1a) is therefore verified at the visual gate, not by AppTest; AppTest enforces the label-set, SpO₂ glyph, and verdict-ordering rules.
- **sensors-not-actuators.** You build and verify; you do not pass the gate. Stop after 3 failed verifies and write a blocker note.
