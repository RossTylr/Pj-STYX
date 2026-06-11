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
# # 08 — R4 HERMES · lay explanation + patient-safe register (proof)
#
# **Read-only relabel, not a re-derivation (single-source).** HERMES renders the *existing* CALLIOPE
# real top-k into a carer/patient register and **preserves rank** — it computes no new attribution.
# `styx.reach.carer.lay_explain` maps each model factor through `CARER_NAMES` (single source:
# `styx.rationale.VOCABULARY`); the core maths is untouched, so the determinism digest is bit-identical
# by construction. **No predictive claim, no raw score, no σ.**
#
# **The gate is faithfulness.** A carer-facing line that reorders or contradicts the clinician's
# top-1 driver is a safety/honesty failure, not a style choice. CALLIOPE is regime-aware, so we check
# the lay top-1 names the clinician top-1 **pre- and post-breach**; patient-facing → the bar is exact
# (1.000). Two further guards: the register carries no alarming/clinical term and no codename, and it
# stays injective (no two factors collapse onto one phrase, which would make the headline ambiguous).

# %%
import re

from styx.cohort import build_cohort_context
from styx.explain import CARER_NAMES
from styx.rationale import explain
from styx.reach.carer import STABLE_HEADLINE, lay_explain
from styx.synth import build_cohort

cohort = build_cohort(seed=42)
cctx = build_cohort_context(cohort)
reverse = {phrase: factor for factor, phrase in CARER_NAMES.items()}


def _pre_idx(risk, threshold, grid):
    pres = [i for i in grid if risk[i] < threshold]
    return pres[len(pres) // 2] if pres else None


def _post_idx(risk, threshold, grid):
    posts = [i for i in grid if risk[i] >= threshold]
    return posts[0] if posts else None


# %% [markdown]
# ## The faithfulness number — pre- and post-breach (expect 1.000)
# Every patient contributes a pre-breach and (where it crosses) a post-breach window. For each, the
# lay headline must reverse-map to the clinician CALLIOPE top-1 factor.

# %%
agree = total = 0
pre_n = post_n = 0
for p in cohort.patients:
    risk = cctx.risk[p.pid]
    pre, post = _pre_idx(risk, cctx.threshold, cctx.indices), _post_idx(risk, cctx.threshold, cctx.indices)
    for idx, kind in ((pre, "pre"), (post, "post")):
        if idx is None:
            continue
        r = explain(p, cctx.emb, cctx.basins, idx)
        lay = lay_explain(r)
        total += 1
        pre_n += kind == "pre"
        post_n += kind == "post"
        clinician_top1 = r.top_k[0][0]
        recovered = reverse.get(lay.headline) if lay.headline != STABLE_HEADLINE else clinician_top1
        if recovered == clinician_top1 and lay.primary_factor == clinician_top1:
            agree += 1

faithfulness = agree / total
print(f"windows: {total}  ({pre_n} pre-breach, {post_n} post-breach)")
print(f"HERMES faithfulness (lay top-1 == clinician top-1) = {faithfulness:.3f}")
assert faithfulness == 1.0

# %% [markdown]
# ## The register check — patient-safe and injective
# No alarming/clinical term, no codename, no raw score; and no two factors collapse onto one phrase.

# %%
_BANNED = (
    "breach", "fires", "fire", "red zone", "news2", "crisis", "scale 1", "threshold",
    "escalat", "alarm", "deteriorat", "danger", "emergency", "critical",
)
_CODENAMES = ("aegis", "sentinel", "calliope", "echo", "caduceus", "charon", "hermes", "styx")

for factor, phrase in CARER_NAMES.items():
    low = phrase.lower()
    assert not [b for b in _BANNED if b in low], f"alarming term in {factor!r}: {phrase!r}"
    assert not [c for c in _CODENAMES if re.search(rf"\b{c}\b", phrase, re.IGNORECASE)], factor
    assert not re.search(r"\dσ|\d\.\d|risk \d", low), f"raw score in {factor!r}: {phrase!r}"
print(f"register clean: {len(CARER_NAMES)} factors, "
      f"injective={len(set(CARER_NAMES.values())) == len(CARER_NAMES)}, no banned term, no codename")

# %% [markdown]
# ## Worked example — clinician CALLIOPE beside lay HERMES (the silent case)
# At the default silent-window frame, the two lines agree on the primary driver — the clinician names
# the factor in model terms, HERMES in the carer register, same rank.

# %%
p = cohort.silent_case()
idx = cctx.default_idx
r = explain(p, cctx.emb, cctx.basins, idx)
lay = lay_explain(r)
print(f"frame idx={idx}  regime={r.regime}")
print()
print("CLINICIAN (CALLIOPE):", r.headline)
print("  ranked factors    :", [(f, round(v, 3)) for f, v in r.top_k])
print()
print("CARER     (HERMES)  :", lay.headline)
for rank, (phrase, factor) in enumerate(lay.factors, 1):
    print(f"  {rank}. {phrase}   [{factor}]")
print()
print(f"primary driver agree: lay {lay.primary_factor!r} == clinician {r.top_k[0][0]!r} "
      f"-> {lay.primary_factor == r.top_k[0][0]}")
