# STYX ward-board UX — P1 slice spec

Overview strip, ranked triage, bay-header propagation, verdict-copy contract.
Supersedes the deferred P1 items in `STYX_WARD_FIX_SPEC.md`. **P0 is CLOSED** (UX/MAAFI composite 4.1 → 6.1).

slice: `ward-ux-p1` (presentation) — assign the canonical S-id in `features.json`.
gate: `G-ward-ux-p1` — human sign-off in `GATE_REVIEW.md`. Do NOT self-pass.
seed: 42
scope: presentation layer only, **except** the conditional data slice in §B2 (gated separately).
visual targets: `ward_overview_target.html` (overview strip + corrected bay header), `ward_card_target.html` (card treatment).

---

## Invariant guard — presentation slice

- baseline `pytest -q` GREEN before any edit.
- determinism sentinel: scored-cohort SHA-256 **byte-identical** pre/post for `ward-ux-p1`. If it changes, you have crossed into the scoring path — STOP, revert, re-scope (see §B2).

---

## A  Bay-header propagation — resolve the STEADY safety inversion  *(presentation)*

**Problem.** Respiratory reads `STEADY · 0 high · 0 med` while containing Bed 0 and Bed 6, both flagged `deteriorating — silent`. A NEWS2-only summary tells the nurse to relax about the one bay STYX is worried about.

**Resolve.** The bay status badge is computed from the **worst** of `{NEWS2 state, STYX state}`, never NEWS2 alone. Add a STYX count to the header line.
- status ladder (worst-wins): any red/critical bed → `ATTENTION` (red); else any STYX early-signal/deteriorating bed → `WATCH` (amber); else `STEADY` (neutral/green).
- header line: `{n} beds · {h} high · {m} med · {x} max NEWS2 · {f} early signal` + badge. Respiratory → `… · 2 early signal` + `WATCH`. (rename badges if preferred.)

**Accept (AppTest).** For every bay: if it contains ≥1 flagged bed, the bay status token ≠ `STEADY`; the bay `early signal` count == number of flagged cards rendered in that bay. **Hard invariant:** no bay renders `STEADY` while any descendant card carries an early-signal/deteriorating verdict.

*Note.* Derives the badge from already-computed per-bed states → hash-safe, presentation only.

## B  The identical twins (Bed 0 & Bed 6) — diagnose, then route

**Problem.** Bed 0 and Bed 6 render identical vitals (`SpO₂ 94%, was 97; RR 16 →`) but different lead-time copy. Twins are a credibility risk in a Faculty demo.

### B1  Diagnose (do this first)
Pull the seed=42 records backing Bed 0 and Bed 6 from the cohort generator and compare.
- records DIFFER but cards render the same → **rendering collapse**. Route to §B3 (this slice).
- records (near-)IDENTICAL → **generator clones the silent-hypoxia archetype**. Route to §B2.

### B2  IF generator clone — SEPARATE GATED DATA SLICE  *(NOT this slice)*
This changes the scoring path and therefore the determinism hash. Do NOT bundle it into `ward-ux-p1`.
- new slice `data-cohort-variance`, own gate `G-data-variance`.
- inject per-patient variance for the silent-hypoxia archetype (baseline SpO₂, RR, onset time, drift rate) drawn deterministically from the seeded RNG, so two silent deteriorators differ.
- preserve seed=42 reproducibility; record a NEW determinism baseline **deliberately** and log the hash change with rationale in `EXPERIMENT_LOG.md`. Re-run full `pytest`.

### B3  IF rendering collapse — presentation fix  *(this slice)*
Render each bed's own record values; remove any shared/template binding at the view layer.
**Accept.** Rendered vitals for each card == that bed's record values (no view-layer collapse). After the fix, no two flagged beds render byte-identical vitals unless their underlying records are identical (and if so, that's a §B2 generator finding — log it).

## C  Verdict-copy contract — stop negating the alert  *(presentation)*

**Problem.** `rising — no NEWS2 escalation projected yet` says "deteriorating" then negates it ("nothing projected") — reads as "nothing to do". Inconsistent register vs the twin's `~1–2 h before NEWS2 would escalate`.

**Resolve.** One copy contract for flagged-card subtext. It foregrounds the STYX signal/lead; it may note NEWS2 is below trigger **only** as the demoted footer counterpoint (§D), never as the headline. The "NEWS2 hasn't fired" fact is framed as *STYX is ahead of NEWS2*, not as reassurance.
- allowed subtext templates (one family per verdict class):
  - lead-time known: `~{N}–{M} h ahead of NEWS2`  (e.g. "~1–2 h ahead of NEWS2")
  - lead-time uncertain: `rising — flagged ahead of NEWS2`
- banned (negation trap): subtext that leads with or rests on `no … projected`, `nothing …`, `not … yet`. (The contrast belongs in the footer, framed as below-trigger.)
- same verdict class → same template family across all cards (no mixed registers).

**Accept (AppTest).** Every flagged-card subtext matches the allowed template set; zero matches for the banned patterns (e.g. `/no .*projected/i`, `/nothing/i`, `/not .*yet/i` in the subtext line); cards sharing a verdict class share a template family.

## D  Keep the demoted NEWS2 counterpoint on flagged cards  *(presentation)*

**Problem.** The `NEWS2 N · below trigger` line is the productive-disagreement hook (standard score says fine; STYX says watch) and must stay visible on flagged cards.

**Resolve.** Every flagged card renders a footer `NEWS2 {n} · below trigger` (qualifier present when NEWS2 < the bay escalation threshold).

**Accept (AppTest).** Every flagged card emits a NEWS2 footer element; "below trigger" present where NEWS2 < threshold.

## E  Replace the flat attention rail with overview + ranked worklist  *(presentation)*

**Problem.** 21 identical `early signal` pills (42% of the ward) is neither orientation nor triage.

**Resolve.** Two components (see `ward_overview_target.html`):
- **ward overview strip:** cohort line + status counts (critical / early signal / stable). Counts, not pills. This is the ward-level home for silent deterioration.
- **ranked review-now worklist:** top N (default N=6) by rank key (reds first, then shortest lead-time / highest score); each row = `rank · bed · the one moving number · lead-time`, with click-to-jump. The tail collapses to `+{k} more in watch`.

two-tier (display layer): split `early signal` into review-now (ranked, ≤N) and watch (count), cut on the existing model lead-time/score. This is a DISPLAY cut over existing output → hash-safe. (If you instead want to move the underlying classification threshold, that is a MODEL slice, not this one — flag it.)

**Accept (AppTest).** Rail renders ≤ N review-now items, ordered by the rank key (reds/shortest-lead first); watch collapsed to a count; review-now + watch + stable + critical == cohort size; no flat list of all flagged beds remains.

---

## Definition of done (`ward-ux-p1`)

1. A, C, D, E implemented; B routed (B3 here, or B2 spun out as its own gated slice).
2. new AppTest invariants green; baseline `pytest -q` still green.
3. determinism hash byte-identical for `ward-ux-p1` (B2, if triggered, re-baselines separately).
4. before/after screenshot of the ward board + overview for the visual gate.
5. one vertical-slice commit; `features.json` status flipped; `EXPERIMENT_LOG.md` appended (append-only).
6. read-only MAAFI Red-Team + Arbiter pass appended to `GATE_REVIEW.md`. Human signs `G-ward-ux-p1`.

## Notes

- AppTest sees the element/markup tree, not rendered CSS — it enforces the content/count/order rules; visual treatment (overview layout, bay-badge colour) is checked at the visual gate.
- sensors-not-actuators: you build and verify; you do not pass any gate. 3 failed verifies → STOP + blocker note. Do not cross the scoring-path boundary inside a presentation slice (§B2).
