# STYX — "Clinical basis" page · drop-in assets

Companion to `STYX_clinical_basis_build_prompt.md`. Each block below is
independently placeable. UK English throughout. All clinical figures are
**derived renderings** of the NEWS2 charts (Royal College of Physicians, 2017)
unless explicitly the official image — see §B for the copyright rule.

---

## §A — Tables

### Table A · What STYX reads (NEWS2 Scale 1)
*Mirrors NEWS2 Chart 1 layout (Royal College of Physicians, 2017). Derived rendering — see official chart in §B (IMG-1). Column headers are the NEWS2 point value.*

| Parameter (in SIG-1) | 3 | 2 | 1 | 0 | 1 | 2 | 3 |
|---|---|---|---|---|---|---|---|
| Respiration rate (min⁻¹) | ≤8 | — | 9–11 | 12–20 | — | 21–24 | ≥25 |
| SpO₂ — Scale 1 (%) | ≤91 | 92–93 | 94–95 | ≥96 | — | — | — |
| Pulse / heart rate (min⁻¹) | ≤40 | — | 41–50 | 51–90 | 91–110 | 111–130 | ≥131 |
| Temperature (°C) | ≤35.0 | — | 35.1–36.0 | 36.1–38.0 | 38.1–39.0 | ≥39.1 | — |

*STYX plots two of these — SpO₂ (Scale 1) and respiration rate — on the state-space view; the warm risk shading is the summed NEWS2 sub-score for those two parameters.*

### Table B · What STYX does not read — and why it matters
*The remaining NEWS2 parameters are outside SIG-1. STYX is structurally blind to them.*

| Parameter (not in SIG-1) | NEWS2 scoring | What STYX cannot detect |
|---|---|---|
| Systolic blood pressure (mmHg) | ≤90 (3) · 91–100 (2) · 101–110 (1) · 111–219 (0) · ≥220 (3) | Hypotensive deterioration — e.g. sepsis, haemorrhage, cardiogenic shock |
| Consciousness (ACVPU) | Alert (0) · new confusion / V / P / U (3) | New confusion or falling consciousness level |
| SpO₂ — Scale 2 (target 88–92%) | Separate scale for hypercapnic (type 2) respiratory failure | **Safety constraint:** for a patient prescribed Scale 2 (e.g. COPD), STYX's Scale 1 shading is clinically wrong |
| Air or oxygen (+2 uplift) | +2 points if on supplemental O₂ | A rising oxygen requirement may not move the score — the basis of the silent-hypoxia case (Royal College of Physicians, 2017) |

### Table C · NEWS2 thresholds and triggers
*NEWS2 Chart 2 (Royal College of Physicians, 2017).*

| NEWS aggregate | Clinical risk | Response |
|---|---|---|
| 0–4 | Low | Ward-based response |
| Red score — 3 in any single parameter | Low–medium | Urgent ward-based response |
| 5–6 | Medium | Key threshold for urgent response |
| ≥7 | High | Urgent or emergency response |

### Table D · Clinical response and monitoring frequency
*NEWS2 Chart 4 (Royal College of Physicians, 2017), summarised.*

| NEW score | Monitoring frequency | Clinical response (summary) |
|---|---|---|
| 0 | ≥12-hourly | Continue routine NEWS monitoring |
| 1–4 | ≥4–6-hourly | Registered nurse decides on increased monitoring and/or escalation; inform medical team |
| 3 in a single parameter | ≥1-hourly | Registered nurse informs medical team; review for escalation |
| 5+ (urgent threshold) | ≥1-hourly | Urgent assessment by a clinician/team with competence in acute illness; monitored environment; inform medical team (≥ specialist registrar) |
| 7+ (emergency threshold) | Continuous | Emergency assessment by a team with critical-care competence (incl. advanced airway); consider transfer to level 2/3 care |

---

## §B — Image manifest

> **Copyright rule (applies to every image below).** NEWS2 may be reproduced
> free of charge, but only if the RCP is acknowledged in the exact wording in
> §C, the charts are reproduced **in colour**, and the material is **not
> modified or amended in any way** (Royal College of Physicians, 2017).
> Therefore: embed the **official** colour chart verbatim, *or* use a STYX
> table/plot clearly badged as **derived** — never a redrawn/restyled chart
> presented as the NEWS2 chart.

| ID | Image | Source | Placement | Caption |
|---|---|---|---|---|
| IMG-1 | **Official** NEWS2 Chart 1 — the NEWS scoring system (colour) | Download high-quality colour version from the RCP NEWS2 resource page (see §D) | §"What STYX reads", inside an expander "View the official NEWS2 chart" | Verbatim RCP acknowledgement (§C) |
| IMG-2 | **Official** NEWS2 Chart 4 — clinical response to trigger thresholds | RCP NEWS2 resource page | §"STYX and NEWS2", inside an expander | Verbatim RCP acknowledgement (§C) |
| IMG-3 | **Official** NEWS2 Chart 2 — thresholds and triggers *(optional)* | RCP NEWS2 resource page | §"STYX and NEWS2", expander | Verbatim RCP acknowledgement (§C) |
| IMG-D1 | **STYX-derived** state-space trajectory (`styx_clinical_view.png`, already produced) | This project | Top of page or §"How STYX reads the picture" | "STYX trajectory, clinical view. Risk shading derived from NEWS2 sub-scores (Royal College of Physicians, 2017). Synthetic replay — not real patient data." |
| IMG-D2 | **STYX-derived** warm-ramp scoring table (Table A rendered with cell colour — see §E) | This project | §"What STYX reads" | "Derived from NEWS2 Scale 1 (Royal College of Physicians, 2017)." |

---

## §C — Verbatim RCP acknowledgement (use under any reproduced chart)

> Reproduced from: Royal College of Physicians. National Early Warning Score (NEWS) 2: Standardising the assessment of acute-illness severity in the NHS. Updated report of a working party. London: RCP, 2017.

Reproduction conditions (Royal College of Physicians, 2017): acknowledge the RCP in the wording above; do not modify or amend the material; reproduce charts in colour; use the high-quality versions, not the low-quality ones embedded in the report. STYX-derived visualisations are derived works — badge them "Derived from NEWS2 (RCP, 2017)" and never present them as the official chart.

---

## §D — References (Harvard) and in-text examples

**Reference list (place at the foot of the page):**

NHS England (2024) *Virtual wards operational framework*. Publication reference PRN01289. Available at: https://www.england.nhs.uk/publication/virtual-wards-operational-framework/ (Accessed: 12 June 2026).

Royal College of Physicians (2017) *National Early Warning Score (NEWS) 2: standardising the assessment of acute-illness severity in the NHS. Updated report of a working party*. London: Royal College of Physicians. Available at: https://www.rcp.ac.uk/resources/national-early-warning-score-news-2/ (Accessed: 12 June 2026).

**In-text examples to model the page's prose:**
- "NEWS2 aggregates six physiological parameters, each scored by its deviation from a normal range (Royal College of Physicians, 2017)."
- "The oxygen-supplementation score is binary, so a rising oxygen requirement need not raise the aggregate score (Royal College of Physicians, 2017)."
- "A virtual ward delivers acute, consultant-led care in a patient's usual residence and is not intended for standalone remote monitoring or proactive deterioration prevention (NHS England, 2024)."
- "Daily board rounds, reviewing every patient under a senior clinical decision-maker, are a defining component of a virtual ward (NHS England, 2024)."

---

## §E — Optional: warm-ramp coloured scoring table (Streamlit Styler)

Drop-in to render Table A with the same warm ramp as the schematic. Cells are
coloured by the NEWS2 point of their column.

```python
import pandas as pd
import streamlit as st

# warm ramp shared with the schematic: NEWS2 point 0..3
RAMP = {0: "#FFFFFF", 1: "#F7D9C6", 2: "#E79C74", 3: "#C4532D"}
INK_FOR = {0: "#1A1A1A", 1: "#1A1A1A", 2: "#1A1A1A", 3: "#FFF4ED"}

# columns mirror NEWS2 Chart 1: scores 3,2,1,0,1,2,3
COLS = ["3", "2", "1", "0", "1 ", "2 ", "3 "]   # trailing spaces keep keys unique
SCORE = [3, 2, 1, 0, 1, 2, 3]

rows = {
    "Respiration rate (min⁻¹)": ["≤8", "", "9–11", "12–20", "", "21–24", "≥25"],
    "SpO₂ — Scale 1 (%)":       ["≤91", "92–93", "94–95", "≥96", "", "", ""],
    "Pulse / HR (min⁻¹)":       ["≤40", "", "41–50", "51–90", "91–110", "111–130", "≥131"],
    "Temperature (°C)":         ["≤35.0", "", "35.1–36.0", "36.1–38.0", "38.1–39.0", "≥39.1", ""],
}
df = pd.DataFrame(rows, index=COLS).T
df.columns = COLS

def colour_col(col):
    s = SCORE[COLS.index(col.name)]
    return [f"background-color: {RAMP[s]}; color: {INK_FOR[s]}" for _ in col]

styled = df.style.apply(colour_col, axis=0)
st.table(styled)
st.caption("Derived from NEWS2 Scale 1 (Royal College of Physicians, 2017).")
```
