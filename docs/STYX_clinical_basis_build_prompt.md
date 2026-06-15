# Build prompt — STYX "Clinical basis" reference page

> **Superseded (2026-06-15):** the "leave the three cascade-stage definitions as placeholders; do
> not invent" instruction below (§8, and the checklist items at the foot of this file) no longer
> applies — those definitions are now settled in `styx/clinical_basis.py` (see the glossary),
> each grounded in its detector. This prompt is retained as the historical build record.

## Role and context
You are extending **Pj-STYX**, a Streamlit + Plotly virtual-ward trajectory
monitor (demo mode, synthetic replay — not a medical device). The app has three
sidebar pages: App landing, Ward board, Patient view. Build a fourth page,
**"Clinical basis"**, that states the tool's clinical grounding, scope and
limits. The plan is already agreed; this prompt specifies the build.

Companion file `STYX_clinical_basis_assets.md` holds the drop-in **Tables A–D**,
the **image manifest** (IMG-1…IMG-D2), the verbatim **RCP acknowledgement**, and
the **Harvard reference list**. Place those assets verbatim where this prompt
names them. Do not paraphrase the tables or the acknowledgement.

## Non-negotiable house rules
- **UK English** throughout; clinician register; SpO₂ with subscript; Temp (°C).
- **Sentence case** for all headings and labels.
- **Light mode**; the **warm risk ramp** (NEWS2 point 0 = white → 3 = deep
  terracotta) shared with the state-space schematic.
- **Native Streamlit components only** — no custom components, no `localStorage`.
- Demo / not-a-device banner consistent with the other pages.
- **Harvard author–date referencing** in the page prose (see "Referencing").

## Page identity and placement
- New page in the multipage app; sidebar label **"Clinical basis"**, positioned
  last (App · Ward · Patient · Clinical basis).
- Add a one-line footer/link on the other three pages:
  *"Built on NEWS2 (RCP, 2017) — see Clinical basis for scope and limits."*

## Section-by-section specification (in order)
Each section names the asset to drop in and the citation to use.

1. **Header + banner.** Page title "Clinical basis"; one-line purpose; the
   demo/synthetic-replay/not-a-device banner.

2. **Intended use and scope (governance).** Who it is for (hub clinicians);
   what decision it supports (prioritisation for the board round / call-first
   list, under senior clinical oversight); what it explicitly does **not** do
   (no autonomous escalation, no auto-dial to 999). State plainly:
   *"No alert means review as normal — never 'safe'."*

3. **What STYX reads.** Short prose + **Table A**. Optionally embed **IMG-1**
   (official NEWS2 Chart 1, colour) inside an expander with the verbatim
   acknowledgement. Render Table A with the warm ramp (assets §E, IMG-D2).
   Cite (Royal College of Physicians, 2017).

4. **What STYX cannot see.** Prose + **Table B**. Call out two things
   explicitly: the **SpO₂ Scale 2 safety constraint** (Scale 1 shading is wrong
   for a hypercapnic/COPD patient on a 88–92% target), and the **oxygen-uplift /
   silent-hypoxia rationale** (a rising oxygen requirement need not move the
   score). Cite (Royal College of Physicians, 2017).

5. **STYX and NEWS2 (relationship and escalation).** One clear statement that
   STYX is a *trajectory/forecast layer* and NEWS2 is the *threshold standard it
   does not replace*. Add **Table C** and **Table D**; optionally **IMG-2/IMG-3**
   in an expander. Cite (Royal College of Physicians, 2017).

6. **Why trajectory, not just threshold.** The clinical rationale: NEWS2's
   binary oxygen score means deterioration can be under way before the aggregate
   moves — the gap STYX targets. Keep it to a short paragraph, attributed
   (Royal College of Physicians, 2017).

7. **Place within the virtual-ward framework.** STYX is a monitoring/triage aid
   *within* an acute virtual ward under senior oversight; it supports the daily
   board round; it spans the three named pathways (acute respiratory illness,
   frailty, heart failure). State the guardrail: a virtual ward is **not** for
   standalone remote monitoring or proactive deterioration prevention, so STYX
   does not claim to be either. Cite (NHS England, 2024).

8. **Glossary.** One-line definitions: STYX score, AEGIS, ECHO,
   "silent but rising", and the three cascade stages (silent flag → early
   warning/AEGIS → escalation crossing). **IMPORTANT:** the three cascade-stage
   clinical definitions are not yet settled — render them as clearly-marked
   placeholders (e.g. "*[definition to confirm]*"). Do **not** invent clinical
   semantics.

9. **References and attribution.** The verbatim RCP acknowledgement (assets §C)
   for any reproduced chart, **and** the Harvard reference list (assets §D) at
   the foot of the page.

## Streamlit component mapping (guidance, not prescriptive)
`st.title` / `st.caption`; `st.warning` / `st.info` for banners; `st.columns`
for the "reads / cannot see" split; `st.table` or a styled `st.dataframe` for
Tables A–D; `st.expander` for the official charts and any depth; `st.image` for
IMG-1/2/3; `st.divider` between sections; sidebar footer or `st.page_link` for
cross-page links.

## Referencing
- UK English; **Harvard author–date** in-text, e.g. (Royal College of
  Physicians, 2017), (NHS England, 2024). Model prose on the in-text examples in
  assets §D.
- Full **reference list** at the foot (assets §D), with access dates.
- Keep the two attribution mechanisms distinct and both present: the **Harvard
  reference list** (academic) and the **RCP-mandated chart acknowledgement**
  (a copyright condition).

## Acceptance criteria — the built page must pass all of these
- [ ] UK English throughout; SpO₂ subscript and Temp (°C) correct; sentence case.
- [ ] Light mode; warm ramp matches the schematic; native components only.
- [ ] Tables A–D present and accurate to the assets pack.
- [ ] Any reproduced NEWS2 chart is the **official colour image, unmodified**,
      with the verbatim RCP acknowledgement; any STYX-derived table/plot is
      badged "derived from NEWS2 (RCP, 2017)" and never labelled the official chart.
- [ ] Intended-use/scope and "no alert ≠ safe" statements present.
- [ ] SpO₂ Scale 2 safety constraint stated; oxygen/silent-hypoxia rationale stated.
- [ ] Virtual-ward guardrail present (not standalone monitoring / not
      deterioration prevention), cited to NHS England (2024).
- [ ] Harvard in-text citations and a foot-of-page reference list with access dates.
- [ ] Cascade-stage definitions are placeholders, not invented.
- [ ] No clinician-only alarm language ("red zone", "fires") on any
      patient-facing element.

## Do NOT
- Recreate, restyle or modify the official NEWS2 charts — this breaches the RCP
  reproduction terms. Embed the official colour image, or use a clearly-badged
  derived table.
- Present a STYX-derived table as "the NEWS2 chart".
- Overclaim STYX as deterioration-prevention or standalone remote monitoring.
- Invent the three cascade-stage clinical definitions — leave placeholders.
- Use `localStorage`/`sessionStorage` or any custom component.
