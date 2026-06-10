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
# # 07 — R1 history-as-prior · descriptive hazard (proof)
#
# **Descriptive, not predictive — no lift claim.** Telemetry saturates in-sample (AUC 1.000), so R1
# adds *description*: denser Theograph care-history stratifies the deterioration hazard (shorter
# time-to-escalation). Reported as a hazard ratio + stratified survival + a c-index — never accuracy.
#
# **Augmentation, not re-derivation.** Time-to-escalation is read off the *existing* risk waterline
# (`CohortContext.risk` crossing the F4 threshold); this notebook plots only the arrays `stratify`
# returns — it remodels nothing. One synthetic cohort, scored in-sample (construct validity).

# %%
import numpy as np
import plotly.graph_objects as go

from styx.cohort import build_cohort_context
from styx.reach.history import stratify, survival_table
from styx.synth import build_cohort

cohort = build_cohort(seed=42)
cctx = build_cohort_context(cohort)
s = stratify(cctx)
print(f"n_events={s.n_events}/{len(cohort.patients)}  (the survival event count = escalators)")
print(f"hazard ratio (per +1 care-event) = {s.hazard_ratio:.3f}  95% CI [{s.hr_ci[0]:.3f}, {s.hr_ci[1]:.3f}]")
print(f"c-index = {s.c_index:.3f}   log-rank p = {s.logrank_p:.4f}")
print(f"honest residuals (bottom-quartile history yet escalated) = {s.residual_pids}")

# %% [markdown]
# ## Stratified survival — denser vs thinner history
#
# The strata separate (log-rank above): the denser-history stratum escalates sooner. This is the
# descriptive headline — a hazard *stratification*, not a claim that R1 predicts better than the
# saturated telemetry.

# %%
fig = go.Figure()
for c, colour in ((s.high, "#c0392b"), (s.low, "#2980b9")):
    fig.add_trace(go.Scatter(
        x=c.t_min, y=c.survival, mode="lines", line_shape="hv",
        name=c.label, line=dict(color=colour, width=2),
    ))
fig.update_layout(
    title=f"Time-to-escalation by care-history density (log-rank p={s.logrank_p:.4f}, c-index={s.c_index:.3f})",
    xaxis_title="sim-minutes", yaxis_title="S(t) — fraction not yet escalated",
    yaxis_range=[0, 1.02], template="plotly_white", height=420,
)
fig.show()

# %% [markdown]
# ## The honest residual — pid 39
#
# pid 39 carries a thin care history (bottom-quartile density) yet escalates. History alone would
# have ranked it low; the **live signal** catches it. R1 is a prior, not an oracle — this residual is
# the explicit limit, and it is exactly the patient the MVP's `new_low_history` watch-flag surfaces.

# %%
df = survival_table(cctx)
print(df[df["pid"].isin(s.residual_pids)].to_string(index=False))
assert 39 in s.residual_pids, "pid 39 missing — the residual claim no longer holds"

# %% [markdown]
# ## Fallback (degrade, never overclaim)
#
# Claim-integrity discipline: if the strata ever stop separating (HR CI straddles 1, or log-rank
# p ≥ 0.05), R1 drops the stratification claim and ships the standalone descriptor *"history-only
# AUC 0.765"* (observable `comorbidity_index`) plus the pid-39 residual. The branch below renders the
# fallback only when the primary path fails — so the proof always tells the honest story.

# %%
separated = s.hr_ci[0] > 1.0 and s.logrank_p < 0.05
if separated:
    print("PRIMARY: strata separate — ship the hazard stratification (HR + c-index + curves).")
else:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from styx.synth import Outcome

    X = np.array([[p.comorbidity_index] for p in cohort.patients])
    y = np.array([1 if p.outcome is Outcome.ESCALATED else 0 for p in cohort.patients])
    auc = roc_auc_score(y, LogisticRegression(max_iter=1000).fit(X, y).predict_proba(X)[:, 1])
    print(f"FALLBACK: strata did not separate — ship 'history-only AUC {auc:.3f}' + residual {s.residual_pids}.")
