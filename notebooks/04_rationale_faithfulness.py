# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 04 — Rationale faithfulness (Gate G4)
#
# Proof for **F8 (CALLIOPE)**. The rationale is a *strict template* over the model's real top-k
# attribution — it names only the closed vocabulary, and its top-1 risk driver is the **exactly
# additive** decomposition of the risk (so the choice is unambiguous, no tie-wobble). G4 asks two
# things and this notebook shows both:
#
# 1. **Faithfulness** — does the named top-1 driver match the *actual* deteriorating physiology?
#    The independent oracle is the synthetic **archetype** (the generating mechanism), which the
#    attribution never sees: silent-hypoxia → oxygenation proximity, compensated → effort proximity,
#    coupled → either. Measured on the held-out silent window across the cohort.
# 2. **Closed vocabulary** — no rationale ever names a signal outside the five named terms.
#
# Imports `styx.rationale` (LYR-1 — never reimplements). Replay-of-synthetic; no live data.

# %%
import plotly.graph_objects as go

from styx.config import G4_FAITHFULNESS_FLOOR
from styx.rationale import VOCABULARY, explain
from styx.rationale.calliope import EFFORT_PROX, OXY_PROX
from styx.risk import proximity_components, risk_series
from styx.state import fit_embedding, learn_basins
from styx.synth import Archetype, build_cohort
from styx.synth.gates import breach_index, replay_windows

cohort = build_cohort(seed=42)
emb = fit_embedding(cohort)
basins = learn_basins(cohort, emb)
p0 = cohort.silent_case()

_SIGNATURE = {
    Archetype.SILENT_HYPOXIA: {OXY_PROX},
    Archetype.COMPENSATED: {EFFORT_PROX},
    Archetype.COUPLED: {OXY_PROX, EFFORT_PROX},
}

# Determinism + the headline faithfulness rate, computed exactly as gate G4 does.
agree = total = 0
per_arch: dict[str, list[int]] = {}
for p in cohort.patients:
    if p.archetype is Archetype.STABLE:
        continue
    brk = breach_index(p) or p.t_min.size
    risk = risk_series(p, emb, basins)
    for _, sl in replay_windows(p, cohort.rescore_cadence_min):
        idx = sl.stop - 1
        if idx >= brk or risk[idx] < 0.1:
            continue
        ok = explain(p, emb, basins, idx).top_k[0][0] in _SIGNATURE[p.archetype]
        total += 1
        agree += ok
        per_arch.setdefault(p.archetype.value, [0, 0])
        per_arch[p.archetype.value][0] += ok
        per_arch[p.archetype.value][1] += 1

rate = agree / total
r0 = explain(p0, emb, basins, 150)
print(f"determinism (seed 42 ×2 identical rationale): "
      f"{explain(p0, emb, basins, 150) == explain(build_cohort(seed=42).silent_case(), emb, basins, 150)}")
print(f"named vocabulary ({len(VOCABULARY)}): {VOCABULARY}")
print(f"top-1 faithfulness: {agree}/{total} = {rate:.3f}  (floor {G4_FAITHFULNESS_FLOOR})  "
      f"→ G4 {'PASS' if rate >= G4_FAITHFULNESS_FLOOR else 'FAIL'}")
for a, (ok, n) in sorted(per_arch.items()):
    print(f"  {a:>15}: {ok}/{n} = {ok / n:.3f}")
print(f"patient-0 rationale @ idx 150: {r0.headline}")

# %% [markdown]
# ## Panel A — faithfulness by archetype
# Per-archetype top-1 agreement against the independent (archetype) oracle, with the G4 floor.

# %%
arch_names = sorted(per_arch)
figA = go.Figure()
figA.add_trace(go.Bar(
    x=arch_names, y=[per_arch[a][0] / per_arch[a][1] for a in arch_names],
    text=[f"{per_arch[a][0]}/{per_arch[a][1]}" for a in arch_names], textposition="outside",
    marker_color="#36c", name="top-1 agreement",
))
figA.add_hline(y=G4_FAITHFULNESS_FLOOR, line=dict(color="#c33", dash="dot"),
               annotation_text=f"G4 floor {G4_FAITHFULNESS_FLOOR}")
figA.update_layout(title=f"CALLIOPE top-1 faithfulness — overall {rate:.1%}",
                   yaxis_title="agreement", yaxis_range=[0, 1.05], height=420)
figA.write_html("outputs/04_faithfulness_by_archetype.html")
figA

# %% [markdown]
# ## Panel B — the additive risk decomposition over patient 0's silent window
# The two proximity contributions (oxygenation, effort) and the per-vital exceedance, scaled so they
# sum to the risk. CALLIOPE names the top band at each re-score. For the silent-hypoxia index case
# the **oxygenation** contribution dominates throughout the silent window — faithful to the physics.

# %%
t = p0.t_min
risk0 = risk_series(p0, emb, basins)
pc = proximity_components(p0, emb, basins)
figB = go.Figure()
figB.add_trace(go.Scatter(x=t, y=0.5 * pc[OXY_PROX], name="oxygenation proximity",
                          mode="lines", stackgroup="c", line=dict(color="#36c")))
figB.add_trace(go.Scatter(x=t, y=0.5 * pc[EFFORT_PROX].clip(min=0), name="effort proximity",
                          mode="lines", stackgroup="c", line=dict(color="#2a8")))
figB.add_trace(go.Scatter(x=t, y=risk0, name="risk (total)", mode="lines",
                          line=dict(color="#222", width=1, dash="dot")))
figB.update_layout(title="Additive risk contributions — patient 0 (oxygenation dominates the silent window)",
                   xaxis_title="sim-minutes", yaxis_title="contribution to risk", height=420)
figB.write_html("outputs/04_contribution_decomposition.html")
figB

# %% [markdown]
# ## Panel C — the patient-0 rationale line at the AEGIS fire
# The exact clinician-facing line CALLIOPE renders, with its top-k expand drawn from the same real
# signals (departure direction, breathing–oxygen decoupling) — strict template, nothing free-form.

# %%
print(r0.headline)
for name, val in r0.top_k:  # the additive risk contributors
    print(f"  • {name}: {val:+.2f}")
for line in r0.context:  # the AEGIS 'why early' context (σ-clamped)
    print(f"  • {line}")
print(f"  regime={r0.regime} additive={r0.additive} | terms in vocabulary: "
      f"{set(r0.terms) <= set(VOCABULARY)}")
