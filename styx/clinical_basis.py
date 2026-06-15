"""Clinical-basis copy registry — the reference page's grounding, scope and limits.

Pure data, no behaviour and no Streamlit (LYR-1): the ``styx.explain`` analogue for the
"Clinical basis" page. Tables A–D, the scope statements, the glossary and the references are
placed verbatim from ``docs/STYX_clinical_basis_assets.md``; linted by
``tests/test_clinical_basis.py`` (codenames confined to the glossary, the cascade-stage
placeholders never invented, the RCP acknowledgement byte-for-byte).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GlossaryEntry:
    """One glossary line; ``placeholder=True`` marks a definition not yet clinically settled."""

    term: str
    definition: str
    placeholder: bool = False


@dataclass(frozen=True)
class ChartAsset:
    """An official NEWS2 chart embedded on the page — reproduced unmodified, in colour (§B)."""

    filename: str  # under app/assets/
    title: str  # the expander label the page shows
    source_url: str  # the RCP media URL the PNG was rasterised from


#: One-line purpose under the page title.
PAGE_PURPOSE: str = (
    "What STYX is clinically grounded in, the decision it supports, and the limits of what it "
    "can see."
)

#: §2 — intended use and scope (governance). Rendered as bullets.
INTENDED_USE: tuple[str, ...] = (
    "**Who it is for** — hub clinicians staffing an acute virtual ward, under senior clinical "
    "oversight.",
    "**What decision it supports** — prioritisation for the daily board round and the call-first "
    "list: which patient to review or call first.",
    "**What it does not do** — no autonomous escalation, no auto-dial to 999, no treatment "
    "advice; every action goes through a clinician.",
)

#: §2 — what the absence of an alert must and must not be read as. One source, quoted verbatim.
NO_ALERT_LINE: str = "No alert means review as normal — never 'safe'."

#: The one-line footer/link shown on the clinician-facing pages.
NEWS2_FOOTNOTE: str = "Built on NEWS2 (RCP, 2017) — see Clinical basis for scope and limits."

#: §3 — what STYX reads.
READS_PROSE: str = (
    "NEWS2 aggregates six physiological parameters, each scored by its deviation from a normal "
    "range (Royal College of Physicians, 2017). STYX reads four of them — respiration rate, "
    "SpO₂ (Scale 1), pulse and temperature, the tight vital set fixed by SIG-1 — and watches "
    "their trajectory rather than their instantaneous score."
)

#: Table A — NEWS2 Scale 1 bands for the four SIG-1 vitals (assets §A/§E, verbatim). The column
#: headers are the NEWS2 point values (trailing spaces keep the duplicate keys unique).
TABLE_A_COLUMNS: tuple[str, ...] = ("3", "2", "1", "0", "1 ", "2 ", "3 ")
TABLE_A_SCORES: tuple[int, ...] = (3, 2, 1, 0, 1, 2, 3)
TABLE_A_ROWS: dict[str, tuple[str, ...]] = {
    "Respiration rate (min⁻¹)": ("≤8", "", "9–11", "12–20", "", "21–24", "≥25"),
    "SpO₂ — Scale 1 (%)": ("≤91", "92–93", "94–95", "≥96", "", "", ""),
    "Pulse / HR (min⁻¹)": ("≤40", "", "41–50", "51–90", "91–110", "111–130", "≥131"),
    "Temperature (°C)": ("≤35.0", "", "35.1–36.0", "36.1–38.0", "38.1–39.0", "≥39.1", ""),
}
TABLE_A_NOTE: str = (
    "STYX plots two of these — SpO₂ (Scale 1) and respiration rate — on the state-space view; "
    "the warm risk shading is the summed NEWS2 sub-score for those two parameters."
)

#: §3b — the two NEWS2 params a wearable cannot capture, supplied to the comparator by the nurse.
NURSE_OBS_PROSE: str = (
    "Two NEWS2 parameters a wearable cannot stream — systolic blood pressure and consciousness "
    "(ACVPU) — are entered by a nurse on the obs round and scored in the NEWS2 comparator, so the "
    "side-by-side baseline is a complete NEWS2 but for the oxygen-supplementation flag. STYX's own "
    "trajectory model still reads only the four wearable vitals: the comparator is handed two "
    "parameters STYX never uses, and the early warning still leads it (Royal College of "
    "Physicians, 2017)."
)

#: Table B′ — the nurse-entered params the comparator now scores (assets §A bands, verbatim).
TABLE_NURSE_COLUMNS: tuple[str, str, str] = (
    "Parameter (nurse-entered)", "NEWS2 scoring", "Recorded by",
)
TABLE_NURSE_ROWS: tuple[tuple[str, str, str], ...] = (
    (
        "Systolic blood pressure (mmHg)",
        "≤90 (3) · 91–100 (2) · 101–110 (1) · 111–219 (0) · ≥220 (3)",
        "Nurse obs round (4-hourly) — preserved in band 0 in this scenario",
    ),
    (
        "Consciousness (ACVPU)",
        "Alert (0) · new confusion / V / P / U (3)",
        "Nurse obs round (4-hourly) — Alert throughout in this scenario",
    ),
)

#: §4 — what STYX's own model still cannot see (the comparator's nurse obs do not feed it).
CANNOT_SEE_PROSE: str = (
    "STYX's trajectory model reads only the four wearable vitals; blood pressure and consciousness "
    "are not read by it, not modelled and never inferred — they reach the comparator only through "
    "the nurse obs round above. What no part of the picture scores is the oxygen-supplementation "
    "flag and the Scale 2 alternative (Royal College of Physicians, 2017)."
)

#: Table B — the parameters that remain outside even the completed comparator, and why each matters.
TABLE_B_COLUMNS: tuple[str, str, str] = (
    "Parameter (still unscored)", "NEWS2 scoring", "What this means",
)
TABLE_B_ROWS: tuple[tuple[str, str, str], ...] = (
    (
        "SpO₂ — Scale 2 (target 88–92%)",
        "Separate scale for hypercapnic (type 2) respiratory failure",
        "Safety constraint: for a patient prescribed Scale 2 (e.g. COPD), "  # not modelled — see
        "STYX's Scale 1 shading is clinically wrong",  # explain.CONDITION (ARI, not COPD)
    ),
    (
        "Air or oxygen (+2 uplift)",
        "+2 points if on supplemental O₂",
        "A rising oxygen requirement may not move the score — the basis of the silent-hypoxia "
        "case (Royal College of Physicians, 2017)",
    ),
)

#: §4 call-out 1 — the SpO₂ Scale 2 safety constraint, stated explicitly.
SCALE2_CONSTRAINT: str = (
    "Safety constraint — SpO₂ Scale 2: for a patient in hypercapnic (type 2) respiratory "
    "failure (e.g. COPD) prescribed an 88–92% target, NEWS2 scores SpO₂ "  # not the modelled cohort
    "on Scale 2. STYX's Scale 1 shading is clinically wrong for that patient and must not be "
    "relied on (Royal College of Physicians, 2017)."
)

#: §4 call-out 2 — the oxygen-uplift / silent-hypoxia rationale.
OXYGEN_UPLIFT_LINE: str = (
    "The oxygen-supplementation score is binary (+2 if on supplemental O₂), so a rising oxygen "
    "requirement need not move the aggregate score — the basis of the silent-hypoxia case "
    "(Royal College of Physicians, 2017)."
)

#: §4 call-out 3 — the measurement-source assumption (respiration rate). The model reads a
#: wearable stream and cannot verify how each count was taken; carer-counted RR reliability is a
#: named deployment-readiness item, out of scope for the synthetic demo.
RR_SOURCE_LINE: str = (
    "Measurement source — STYX reads a wearable respiration-rate stream and cannot see how each "
    "breath count was taken. Respiration rate is the load-bearing signal for the silent-hypoxia "
    "case, and manually or carer-counted respiration rate is known to be unreliable; validating "
    "the measurement source is a named deployment-readiness item (RFI DP/RFI-01) and is out of "
    "scope for this synthetic demo."
)

#: §5 — the relationship: STYX is a trajectory layer; NEWS2 is the standard it does not replace.
RELATIONSHIP_LINE: str = (
    "STYX is a trajectory and forecast layer over the vital signs; NEWS2 is the threshold "
    "standard it is built on and does not replace. When a NEWS2 trigger fires, the NEWS2 "
    "escalation response applies unchanged (Royal College of Physicians, 2017)."
)

#: Table C — NEWS2 thresholds and triggers (assets §A, verbatim).
TABLE_C_COLUMNS: tuple[str, str, str] = ("NEWS aggregate", "Clinical risk", "Response")
TABLE_C_ROWS: tuple[tuple[str, str, str], ...] = (
    ("0–4", "Low", "Ward-based response"),
    ("Red score — 3 in any single parameter", "Low–medium", "Urgent ward-based response"),
    ("5–6", "Medium", "Key threshold for urgent response"),
    ("≥7", "High", "Urgent or emergency response"),
)
TABLE_C_CAPTION: str = "Derived from NEWS2 Chart 2 (Royal College of Physicians, 2017)."

#: Table D — clinical response and monitoring frequency (assets §A, verbatim).
TABLE_D_COLUMNS: tuple[str, str, str] = (
    "NEW score", "Monitoring frequency", "Clinical response (summary)",
)
TABLE_D_ROWS: tuple[tuple[str, str, str], ...] = (
    ("0", "≥12-hourly", "Continue routine NEWS monitoring"),
    (
        "1–4",
        "≥4–6-hourly",
        "Registered nurse decides on increased monitoring and/or escalation; inform medical team",
    ),
    (
        "3 in a single parameter",
        "≥1-hourly",
        "Registered nurse informs medical team; review for escalation",
    ),
    (
        "5+ (urgent threshold)",
        "≥1-hourly",
        "Urgent assessment by a clinician/team with competence in acute illness; monitored "
        "environment; inform medical team (≥ specialist registrar)",
    ),
    (
        "7+ (emergency threshold)",
        "Continuous",
        "Emergency assessment by a team with critical-care competence (incl. advanced airway); "
        "consider transfer to level 2/3 care",
    ),
)
TABLE_D_CAPTION: str = (
    "Derived from NEWS2 Chart 4 (Royal College of Physicians, 2017), summarised."
)

#: §6 — why trajectory, not just threshold (the gap STYX targets).
WHY_TRAJECTORY: str = (
    "NEWS2 scores each observation against fixed bands, and its oxygen score is binary, so "
    "deterioration can be under way before the aggregate moves (Royal College of Physicians, "
    "2017). That gap is what STYX targets: it watches the direction and pace of change while "
    "every vital is still inside its band, so the review can start before a threshold is "
    "crossed. The live trajectory for each patient is on the Patient view in the sidebar."
)

#: §7 — place within the virtual-ward framework.
VIRTUAL_WARD_PLACEMENT: str = (
    "STYX is a monitoring and triage aid within an acute virtual ward, used under senior "
    "clinical oversight. A virtual ward delivers acute, consultant-led care in a patient's "
    "usual residence, and daily board rounds — reviewing every patient under a senior clinical "
    "decision-maker — are a defining component (NHS England, 2024). STYX supports that board "
    "round across the three named pathways: acute respiratory illness, frailty and heart "
    "failure."
)
VIRTUAL_WARD_GUARDRAIL: str = (
    "A virtual ward is not intended for standalone remote monitoring or proactive "
    "deterioration prevention — so STYX does not claim to be either. It orders the work of a "
    "clinical team already caring for the patient (NHS England, 2024)."
)

#: §7 — regulatory scope. The demo is a synthetic-replay prototype; classification and a formal
#: clinical safety case are named as deployment (A3) work, not claimed here.
REGULATORY_SCOPE_LINE: str = (
    "Regulatory scope — STYX as shown is a synthetic-replay prototype, not a medical device. "
    "Regulatory classification and a formal clinical safety case are out of scope for this demo "
    "and are named as deployment (A3) work, not claimed here."
)

#: §8 — glossary. The three cascade-stage definitions are now settled, each grounded in its
#: detector (decoupling → AEGIS → threshold crossing; methodology §5); the placeholder sentinel is
#: retained for any future term not yet clinically confirmed (linted).
PLACEHOLDER_DEFINITION: str = "*[definition to confirm]*"
GLOSSARY: tuple[GlossaryEntry, ...] = (
    GlossaryEntry(
        "STYX score",
        "a 0–1 trajectory index summarising how far and how fast the vital signs are moving "
        "toward escalation — a trajectory number, never a NEWS2 score.",
    ),
    GlossaryEntry(
        "Early warning (AEGIS)",
        "the silent-deterioration flag: it learns each patient's own normal in the first hours, "
        "then fires on departure from that baseline — not a population threshold.",
    ),
    GlossaryEntry(
        "Similar past patients (ECHO)",
        "a few past synthetic patients whose course most resembles this one, shown with their "
        "outcomes — context, not a prediction.",
    ),
    GlossaryEntry(
        "“Silent but rising”",
        "deteriorating within the normal range: every vital still inside its NEWS2 band while "
        "the trajectory moves adversely.",
    ),
    GlossaryEntry(
        "Silent window",
        "the period a patient is “silent but rising” — vitals all in range yet the trajectory "
        "climbing toward escalation, as in silent hypoxia (oxygen falling while breathing effort "
        "stays flat). The replay clock lands here by default: it is the window an absolute-"
        "threshold check stays silent through, and the head-start STYX surfaces.",
    ),
    GlossaryEntry(
        "Silent flag (cascade stage 1)",
        "the earliest sign — oxygenation and breathing effort begin to diverge, their normal "
        "coupling breaking down, while both vitals are still inside their NEWS2 bands.",
    ),
    GlossaryEntry(
        "Early warning (cascade stage 2)",
        "the AEGIS early-warning flag — see “Early warning (AEGIS)” above.",
    ),
    GlossaryEntry(
        "Escalation crossing (cascade stage 3)",
        "the STYX trajectory index crossing its own absolute-risk threshold — STYX's escalation "
        "line, not a NEWS2 trigger.",
    ),
)

#: §9 — the RCP-mandated chart acknowledgement (assets §C, byte-for-byte; a copyright condition,
#: distinct from the Harvard reference list below).
RCP_ACKNOWLEDGEMENT: str = (
    "Reproduced from: Royal College of Physicians. National Early Warning Score (NEWS) 2: "
    "Standardising the assessment of acute-illness severity in the NHS. Updated report of a "
    "working party. London: RCP, 2017."
)

#: Badge for every STYX-derived rendering of NEWS2 material (never labelled the official chart).
DERIVED_BADGE: str = "Derived from NEWS2 Scale 1 (Royal College of Physicians, 2017)."

#: §9 — Harvard reference list (assets §D, verbatim, with access dates).
REFERENCES: tuple[str, str] = (
    "NHS England (2024) *Virtual wards operational framework*. Publication reference PRN01289. "
    "Available at: https://www.england.nhs.uk/publication/virtual-wards-operational-framework/ "
    "(Accessed: 12 June 2026).",
    "Royal College of Physicians (2017) *National Early Warning Score (NEWS) 2: standardising "
    "the assessment of acute-illness severity in the NHS. Updated report of a working party*. "
    "London: Royal College of Physicians. Available at: "
    "https://www.rcp.ac.uk/resources/national-early-warning-score-news-2/ "
    "(Accessed: 12 June 2026).",
)

#: §B — the official charts the page embeds (rasterised unmodified, in colour, from these URLs).
CHARTS: tuple[ChartAsset, ...] = (
    ChartAsset(
        filename="news2_chart1_scoring_system.png",
        title="View the official NEWS2 chart (Chart 1 — the NEWS scoring system)",
        source_url=(
            "https://www.rcp.ac.uk/media/alxev00t/news2-chart-1_the-news-scoring-system_0_0.pdf"
        ),
    ),
    ChartAsset(
        filename="news2_chart4_clinical_response.png",
        title="View the official NEWS2 chart (Chart 4 — clinical response to trigger thresholds)",
        source_url=(
            "https://www.rcp.ac.uk/media/mrllczrj/"
            "news2-chart-4_clinical-response-to-news-trigger-thresholds_0.pdf"
        ),
    ),
    ChartAsset(
        filename="news2_chart2_thresholds_triggers.png",
        title="View the official NEWS2 chart (Chart 2 — thresholds and triggers)",
        source_url=(
            "https://www.rcp.ac.uk/media/2acdezkd/news2-chart-2_news-thresholds-and-triggers_0.pdf"
        ),
    ),
)
