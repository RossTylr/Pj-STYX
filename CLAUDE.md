# CLAUDE.md — Claude Code Instructions for STYX

## What This Repo Is

STYX is a virtual-ward physiological-trajectory monitor for the Virtual Wards
hackathon (Challenge 3, considerate of Challenge 2). It renders each patient's
telemetry as a path through a learned state space, anticipates deterioration
*before* threshold breach, and integrates the patient's care history (Theograph).

Streamlit + Plotly UI over an importable `styx/` package, served as a windowed
re-score over synthetic replay (A2). The 10-feature MVP and the build order were
fixed by the MAAFI verdict and the architecture red-team (see Key Files).

## Hard Rules (Never Violate)

1. **50–100 LOC per slice.** If a change touches >100 lines, split it.

2. **No `streamlit` import inside `styx/`.** Logic lives in the package; `app/`
   and `notebooks/` are *thin clients* of it. The app holds zero modelling logic;
   notebooks import `styx`, never reimplement. Swapping Streamlit for React later
   must touch nothing in `styx/`.

3. **Do not advance past a red gate.** G1–G4 are stop conditions (BUILD_MVP.md).
   **G1 has no fallback** — if the synthetic patient lacks the phenomena, stop and
   fix the generator; everything downstream inherits its fidelity.

4. **Regression invariant.** After any change to `synth/`, `forecast/`, or `risk/`,
   re-run G1 + G3: the silent window, the decoupling lead, and the AEGIS→threshold
   lead must all still hold. The lead-time is logged every time.

5. **CALLIOPE is a strict template over the model's real top-k attribution.** Never
   free-form narration; never name a signal outside the model's top contributors.

6. **Never render or narrate a phenomenon the data does not contain.** A reach's
   headline claim (e.g. CADUCEUS decoupling) ships only if verifiable on the scenario.

7. **The demo is replay-of-synthetic, and the app says so.** No real patient data.
   Never imply a live or streaming deployment.

8. **Gate proves it.** A slice is done only when its gate test passes *and* its
   proof notebook renders the evidence. Log the result to `EXPERIMENT_LOG.md`.

## Architecture Constraints (from MAAFI verdict + architecture red-team)

- **DET-1**: deterministic replay, fixed `seed=42`. No module-level RNG; seed in `styx/config.py`.
- **LYR-1**: layering — `app/` → imports `styx`; `styx/` → no Streamlit; `notebooks/` → import `styx` only.
- **A2-1**: serving = windowed re-score of the cohort over replay. No streaming infra, no per-event inference (STYX is a trend monitor, not an acute-spike detector).
- **A2-2**: `rescore_cadence` is an explicit parameter, owned by gate G3 (the window must preserve the AEGIS→threshold lead).
- **UQ-1**: conformal intervals + per-window quality gating on every model output (uncertainty-first, folded in as a requirement — never fabricate confident precision).
- **SIG-1**: tight vital set — RR, SpO₂, HR, temp + one labs proxy. Add more only at deployment.
- **TIER-1**: build the Tier-0+1 10-feature MVP first; reaches (order R1 → R4 → R3 → R2) only after the milestone gate.

## Current Phase: MVP build (Slices S0–S7)

10-feature MVP = `{F5, F1, F2, F4, F7, F3, F8, F6, F9, F10}`. Slice order:

1. S0 → scaffold (repo layout, this file, deps)
2. S1 → `styx/synth` (F5) — gate **G1**
3. S2 → `styx/state` + `styx/viz` (F1) — gate **G2**
4. S3 → `styx/forecast` + `styx/risk` (F2, F4, F7) — gate **G3**
5. S4 → `styx/theograph` + `styx/rationale` + patient page (F3, F9, F8) — gate **G4**
6. S5 → `styx/cohort` + ward-board page (F6, F10) — **milestone** (MVP)
7. S6 → `styx/reach` (R1 → R4 → R3 → R2) — claim-integrity
8. S7 → polish (legibility A/B, fallback recording, replay framing)

Full spec per slice: `BUILD_MVP.md`.

## Key Files

| File | Purpose |
|------|---------|
| `BUILD_MVP.md` | Master S0→S7 build order, gates, proof notebooks |
| `docs/STYX_PRD.md` | Product requirements (v0.5) |
| `docs/MAAFI_STYX_verdict.md` | Feature tiers, 10-feature MVP, the gates |
| `docs/ARCH_REDTEAM_STYX.md` | Serving architecture (A2 now / A3 later) |
| `EXPERIMENT_LOG.md` | Append-only per-slice result log |
| `styx/config.py` | `SEED=42`, `RESCORE_CADENCE`, thresholds, `VITALS` |
| `styx/viz/` | Plotly figure builders (data → figure), shared by app + notebooks |

## Coding Style

- Python 3.10+, type hints on all public functions
- Frozen dataclasses for decision/record objects (`@dataclass(frozen=True)`)
- Protocols for interfaces (`typing.Protocol`); Enums for outcomes
- No global state. No module-level RNG. No dict-iteration-order dependence.
- `styx/viz` builders are pure: data in, Plotly figure **or HTML/SVG string** out — no I/O, no
  Streamlit. A page may inject a builder's HTML/CSS via `st.markdown(..., unsafe_allow_html=True)`
  (e.g. the ward routine board, `styx/viz/board.py`); the markup/styling logic stays in the builder,
  never in the page. Band colour is reserved for the NEWS2 band signal; the STYX teal is identity/trend.
- Notebooks are jupytext `.py` (paired to `.ipynb` only for sharing)
- `ruff` for linting (line-length=100)

## Testing Pattern

```python
# DET-1 — same seed -> identical run
from styx.synth import build_cohort
a, b = build_cohort(seed=42), build_cohort(seed=42)
assert a.equals(b)                      # streams, events, scores all identical

# Gate G1 — synthetic fidelity (before leaving S1)
p = a.silent_case()
assert has_silent_window(p)             # vitals in range, trend adverse
assert decoupling_lead_min(p) >= 90     # RR-SpO2 coherence drop precedes any breach
assert cohort_outcome_auc(a) > 0.6      # outcome learnable from history

# Gate G3 — anticipation dissociation (before leaving S3)
t = fire_times(p, cadence=RESCORE_CADENCE)
assert t.aegis < t.forecast < t.threshold   # fire in order
assert t.threshold - t.aegis > 0            # the lead-time headline; cadence must preserve it
```
