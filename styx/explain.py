"""Plain-language explainer registry — the page's what/how/why copy for a non-technical room.

Pure data, no behaviour and no Streamlit (LYR-1): the text analogue of ``styx/viz`` (which holds
streamlit-free *figure* presentation). The app reads one entry per panel into an ⓘ popover; the
notebooks can cite the same copy. Honesty anchors ("synthetic", "replay", "constructed") are kept
*in* the text where relevant, and forbidden over-claims are barred — both enforced by
``tests/test_explainer.py`` (the copy analogue of the closed-vocabulary gate).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Explainer:
    """Plain-language card for one page component."""

    what: str
    how: str
    why: str


#: The component ids the pages render — the registry must cover exactly these (patient + ward).
COMPONENTS: tuple[str, ...] = (
    "trajectory", "waterline", "aegis", "cone", "ghost",
    "calliope", "sentinel", "theograph", "raw_vitals",
    "ward_board", "watchlist", "echo",
)

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
        what="The forecast we'd have made at the AEGIS moment, drawn over what actually happened.",
        how="It re-runs the same forecast from the earlier anchor.",
        why="It shows the early warning was right — ghost and reality line up.",
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
            "patients; outcomes are synthetic labels; ECHO illustrates, it does not forecast this "
            "patient.)",
    ),
}
