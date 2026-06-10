"""Plain-language explainer registry — the page's what/how/why copy for a non-technical room.

Pure data, no behaviour and no Streamlit (LYR-1): the text analogue of ``styx/viz`` (which holds
streamlit-free *figure* presentation). The app reads one entry per panel into an ⓘ popover; the
notebooks can cite the same copy. Honesty anchors ("synthetic", "replay", "constructed") are kept
*in* the text where relevant, and forbidden over-claims are barred — both enforced by
``tests/test_explainer.py`` (the copy analogue of the closed-vocabulary gate).
"""

from __future__ import annotations

from dataclasses import dataclass

#: The single source for the modelled condition's name. The generator models pneumonia / COVID-style
#: happy-hypoxia (SpO₂ baselined healthy, silently desaturating on air, effort flat, patient alert) —
#: *not* COPD (which baselines chronically hypoxic, hypercapnic, with rising effort). One constant so
#: every surface stays consistent and a relabel is a one-line change.
CONDITION: str = "acute respiratory infection (pneumonia)"

#: (6b) The scope/blind-spot line for the front page — what STYX sees, and what "no alert" means.
SCOPE_LINE: str = (
    "STYX sees RR, SpO₂, HR, Temp — no blood pressure, no consciousness level. "
    "No alert means *review as normal*, never *safe*."
)

#: (6g) Lay "Pattern: …" labels for the deterioration archetypes — never the raw enum on a board.
#: Keyed by ``Archetype.value``; honesty-linted (no raw enum token may appear in rendered output).
ARCHETYPE_PATTERNS: dict[str, str] = {
    "silent_hypoxia": "silent-hypoxia-like",
    "compensated": "compensating",
    "coupled": "coupled decline",
    "stable": "stable / recovering",
}


@dataclass(frozen=True)
class Explainer:
    """Plain-language card for one page component."""

    what: str
    how: str
    why: str


#: The component ids the pages render — the registry must cover exactly these (patient + ward).
COMPONENTS: tuple[str, ...] = (
    "trajectory", "waterline", "aegis", "cone", "ghost",
    "calliope", "sentinel", "theograph", "raw_vitals", "timeline",
    "ward_board", "watchlist", "echo", "history",
)

#: (S5.7) The single source for plain UK-clinical display labels — codenames live only in the code
#: (function/module/key identifiers, docstrings); plain English faces the ward. Keyed by the same
#: component/role ids the pages use, so a page or a viz builder renders ``DISPLAY_NAMES[key]`` rather
#: than a Greek codename. STYX (product name) and the Pattern labels (ARCHETYPE_PATTERNS) stay as-is.
#: ``caduceus``/``charon`` are reserved here so the reaches ship plain from their first panel.
DISPLAY_NAMES: dict[str, str] = {
    "aegis": "Early warning",
    "calliope": "Why this score",
    "sentinel": "Confidence",
    "echo": "Similar past patients",
    "waterline": "Risk over time",
    "cone": "Forecast range",
    "trajectory": "Trajectory",
    "ghost": "Hindsight forecast",
    "history": "History-based risk",  # R1 history-as-prior hazard panel
    "caduceus": "How the vital signs move together",  # reserved for R3
    "charon": "Projected care events",  # reserved for R2
}

EXPLAINERS: dict[str, Explainer] = {
    "trajectory": Explainer(
        what="Recent vitals as one moving point on a 2-axis clinical map "
             "(left↔right oxygenation, up↕down breathing effort).",
        how="The vitals are combined into the two axes; the shaded zones are the stable basin and "
            "the crisis attractor, learned from the cohort.",
        why="It shows direction of travel — a patient drifting toward crisis while every vital "
            "still reads normal. (Constructed axes; synthetic replay.)",
    ),
    "waterline": Explainer(
        what="A 0–1 risk over time, with the escalation line.",
        how="Closeness to the crisis zone, plus how far any vital is outside normal — the second "
            "held at zero until an actual breach.",
        why="It rises early (the warning) but only crosses late (when a threshold alarm would "
            "finally fire).",
    ),
    "aegis": Explainer(
        what="The silent-deterioration flag.",
        how="It learns each patient's own normal in the first hours, then fires on departure from "
            "their baseline — not a population threshold.",
        why="It catches deterioration within the normal range — here, 3.5 h before threshold.",
    ),
    "cone": Explainer(
        what="Where the trajectory is heading, with an uncertainty band.",
        how="A robust trend fit plus a calibrated interval.",
        why="Anticipation with stated confidence, never false precision.",
    ),
    "ghost": Explainer(
        what="The hindsight forecast — the one we'd have made at the early-warning moment, "
             "drawn over what actually happened.",
        how="It re-runs the same forecast from the earlier anchor.",
        why="It shows the early warning was right — the hindsight forecast and reality line up.",
    ),
    "calliope": Explainer(
        what="The plain reason for the current risk.",
        how="It reads the model's actual top contributor in fixed wording — it can only name "
            "signals the model used.",
        why="An explanation tied to the maths, not a generated story. (Template over real "
            "attribution.)",
    ),
    "sentinel": Explainer(
        what="Confidence in this estimate now.",
        how="From the forecast band width plus the window's data quality.",
        why="High vs low confidence changes how you act.",
    ),
    "theograph": Explainer(
        what="The patient's care history over years.",
        how="Two scales — a lifelong overview and a recent-days strip aligned to the episode.",
        why="Heavier history → frailer baseline → faster fall; it grounds why this patient "
            "deteriorates as they do. (History pattern real; specific dates illustrative — "
            "synthetic replay.)",
    ),
    "raw_vitals": Explainer(
        what="The underlying RR / SpO₂ / HR / temp traces.",
        how="The measured numbers behind everything above.",
        why="Check the source signal yourself.",
    ),
    "timeline": Explainer(
        what="The episode as one strip: when each signal fires, and where escalation is projected.",
        how="It reads the already-computed fire-points — early warning, forecast, the projected "
            "window, the threshold crossing — and lays them on one time axis (no new calculation).",
        why="One read of the order and the lead. The projected window is drawn as a band, never a "
            "single time, so it can't imply false precision. (Synthetic replay.)",
    ),
    "ward_board": Explainer(
        what="Every patient, ranked by how soon they're forecast to need escalation.",
        how="It re-scores the whole cohort at the current time and sorts by forecast time-to-"
            "threshold, pulling the silent-but-rising patients into a watchlist.",
        why="Triage attention first to who needs it — including the quiet ones a threshold board "
            "shows as green. (Synthetic replay.)",
    ),
    "watchlist": Explainer(
        what="Patients deteriorating within their normal range — the early flag has fired, no "
             "threshold crossed.",
        how="Departure from personal baseline with the risk still below the escalation line.",
        why="Exactly the patients a vitals-threshold board misses. (Synthetic replay.)",
    ),
    "echo": Explainer(
        what="A few past patients whose course most resembles this one, and how they turned out.",
        how="It finds the nearest trajectories in the same constructed state space, matched on "
            "shape rather than a single reading.",
        why="It grounds the case in similar ones — context, not a prediction. (Other synthetic "
            "patients; outcomes are synthetic labels; this view illustrates, it does not forecast "
            "this patient.)",
    ),
    "history": Explainer(
        what="How rich the patient's recent care history is, and how that tracks the time it takes "
             "to reach escalation across the ward.",
        how="A proportional-hazards model on care-event density, plus a median split tested with a "
            "log-rank test; the curves show patients with denser history reach escalation sooner.",
        why="A descriptive association, not a cause — denser history flags a sicker patient; it does "
            "not make them deteriorate faster. It adds no measurable accuracy over the live vital-"
            "sign signal here, and it misses patients who deteriorate on thin history (patients 7 "
            "and 39), so a stratum is a prior, never a safety guarantee. (Synthetic replay.)",
    ),
}

#: Lay one-liners for the episode-timeline events — kept here so they're honesty-linted with the
#: rest of the copy (``tests/test_explainer.py``). Keyed by the timeline event ``key``.
TIMELINE_LABELS: dict[str, str] = {
    "aegis": "early warning — deteriorating within their normal range",
    "forecast": "forecast now confirms a trend toward escalation",
    "eta": "escalation projected — timing uncertain",
    "breach": "would cross the escalation threshold",
}

#: (R1) The two care-history strata for the hazard panel — the single source for ``KMCurve.label``
#: (imported by ``styx.reach.history``) and the legend the panel renders. Honesty-linted as copy.
KM_STRATUM_LABELS: dict[str, str] = {
    "high": "Denser recent care history",
    "low": "Thinner recent care history",
}

#: (6f) Caption under the STYX index — the index is a trajectory number, never a NEWS2 score.
SCORE_CAPTION: str = "trajectory index — not NEWS2"

#: (6i) Ordinal time-to-escalation bands — keyed by ``styx.readouts.eta_ordinal`` output. A band,
#: never a spurious exact minute (UQ-1).
ETA_BANDS: dict[str, str] = {
    "lt30": "< 30 min",
    "30_60": "30–60 min",
    "1_2h": "1–2 h",
    "gt2h": "> 2 h",
    "unclear": "unclear",
}

#: (6c) Obs-age stamp — the honest provenance of a score (which observation it was scored on).
OBS_AGE_TEMPLATE: str = "scored on obs at {clock} (sim)"

#: Label for the partial-NEWS2 comparator — honest about which 3 of 7 params are not modelled (and
#: that they are normal in this scenario by construction, so the partial equals the full score here).
NEWS2_PARTIAL_LABEL: str = (
    "NEWS2 (partial, Scale 1; 4 of 7 — BP, consciousness, O₂ not modelled, normal in this scenario)"
)
