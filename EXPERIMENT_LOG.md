# EXPERIMENT_LOG.md — STYX

Append-only. One row per slice when its gate passes (BUILD_MVP.md). The
AEGIS→threshold lead-time is logged every time `synth/`, `forecast/`, or `risk/`
changes (Hard Rule 4).

| Slice | Gate | Result | Lead-time (min) | Date |
|-------|------|--------|-----------------|------|
| S0 — scaffold | none | repo skeleton runs; `pytest` collects; `streamlit run app/app.py` launches | — | 2026-06-06 |
