"""STYX landing (LYR-1: thin client — imports styx, holds zero logic).

The one-glance front page: brand lockup, BLUF / Impact / Effect, the obs-timeline motif, and the
honesty rail. App-wide chrome (page config, logo, theme) is owned by the router in app/app.py.
"""

import streamlit as st

from styx.clinical_basis import NEWS2_FOOTNOTE
from styx.explain import SCOPE_LINE
from styx.readouts import footer_text
from styx.viz.landing import obs_timeline_figure

# (6h) Brand lockup — logo mark beside the product name and the one-line hook.
left, right = st.columns([2, 3], vertical_alignment="center")
with left:
    st.image("docs/Pj-STYX.jpeg", width="stretch")
with right:
    st.title("STYX — virtual-ward trajectory monitor")
    st.caption("Minding the gap between observations — before the numbers do.")

# Bottom line (BLUF) — the claim, first and in bold.
st.markdown(
    "**Bottom line.** STYX surfaces the virtual-ward patient who still looks well on today's "
    "numbers but is drifting toward deterioration — and flags them hours before a threshold "
    "alarm would — so the hub looks at the right patient first. In support of nurse-led NEWS2, "
    "never a replacement."
)

# Demo banner — immediately under the BLUF so the headline never travels without its caveat.
st.warning(
    "Demo: **replay of synthetic data** — no real patients, not a live deployment, not a "
    "validated tool or a medical device. Lead times shown are illustrative.",
    icon="⚠️",
)

# Impact — who it helps and what changes for them (the "so what").
st.markdown(
    "**Impact.** At the 07:30 hub triage, STYX shortens the call-first list to the few patients "
    "genuinely moving the wrong way — putting earlier eyes on silent deterioration and supporting "
    "the board round, without adding to alert load. For the patient it means a person looks "
    "sooner; nothing happens automatically."
)

# Effect — the mechanism that produces it, quiet by default, in support of NEWS2.
st.markdown(
    "**Effect.** Every 15 simulated minutes STYX re-scores each patient's trajectory across RR, "
    "SpO₂, HR and Temp against *that patient's own baseline* — flagging departure from their "
    "normal before an absolute threshold is crossed, and forecasting time to escalation. In the "
    "replay it surfaces silent-hypoxia drift up to about five hours ahead of NEWS2's red score "
    "on the clearest case — across the ward the typical lead is one to two hours — and "
    "does so *even when NEWS2 is scored on the same continuous data* — so the lead comes from "
    "reading the trajectory, not from scoring more often. Quiet by default: it surfaces only the "
    "few who are drifting and stays silent on the rest. It supports the obs, the nurse and NEWS2 "
    "— it does not replace them."
)

# The hero motif — the idea shown, not told (intermittent obs, the line between, the caught drift).
st.plotly_chart(obs_timeline_figure(), width="stretch", config={"displayModeBar": False})
st.caption("NEWS2 scores at the obs. STYX watches in between.")

# What it is not — the honesty rail kept beside the claim.
st.markdown(
    "**What it is not.** Not NEWS2, and not a new early-warning score. Not autonomous — a "
    "clinician reviews everything; nothing auto-escalates. \"No alert\" means review as normal — "
    "never \"safe\"."
)

# (6b) Scope / blind-spot: the intended-use line in the shared banner — what STYX sees, and what
# "no alert" must and must not be read as.
st.info(SCOPE_LINE)

# Start here — one line into the demo, with the onward link to the clinical basis.
st.markdown(
    "**Start here.** Open **Ward board** in the sidebar → press ▶ on the replay clock → open the "
    "top card.   ·   New here? See **Clinical basis** for scope and limits."
)
st.caption(footer_text())
st.page_link("pages/04_clinical_basis.py", label=NEWS2_FOOTNOTE)
