# STYX

A virtual-ward physiological-trajectory monitor (Virtual Wards hackathon,
Challenge 3). STYX renders each patient's telemetry as a path through a learned
state space, anticipates deterioration *before* threshold breach, and integrates
the patient's care history (Theograph). Logic lives in the importable `styx/`
package; `app/` (Streamlit + Plotly) and `notebooks/` are thin clients of it.

> **The demo is a replay of synthetic data — no real patient data, and not a live
> or streaming deployment.** The deployment target (A3) is described in the docs;
> the MVP serves an A2 windowed re-score over replay.

## Quickstart

```bash
pip install -e .            # editable install of the styx package
streamlit run app/app.py    # launch the demo UI
pytest                      # run tests / gate checks
```

## Where to look

- `BUILD_MVP.md` — the S0→S7 build order, gates, and proof notebooks.
- `CLAUDE.md` — hard rules and architecture constraints.
- `docs/` — PRD (`STYX_PRD.md`), feature verdict, serving-architecture red-team.
- `EXPERIMENT_LOG.md` — append-only per-slice results.
