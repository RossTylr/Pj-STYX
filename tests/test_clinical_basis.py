"""Clinical-basis copy integrity — verbatim, honesty and attribution lints for the reference page.

Five guarantees on ``styx.clinical_basis``: the required scope statements are present verbatim
(no-alert ≠ safe, the SpO₂ Scale 2 safety constraint, the oxygen-uplift rationale, the
virtual-ward guardrail); the cascade-stage definitions are settled and grounded in their detector; both
attribution mechanisms are intact (the RCP acknowledgement byte-for-byte, the Harvard list with
access dates); the warm ramp is the schematic's own ``palette.WARM_RAMP`` and equals the assets
§E literals; and the copy never over-claims, with codenames confined to the glossary (LYR-1:
the new styx modules import no Streamlit)."""

import re
from pathlib import Path

from styx import clinical_basis as cb
from styx.viz import palette
from styx.viz.scoring_table import RAMP_FOR_POINT

_REPO = Path(__file__).resolve().parent.parent
#: Same over-claim/codename vocabulary as tests/test_explainer.py (kept in lockstep).
_FORBIDDEN = ("predicts the patient", "diagnoses", "learns the patient", "real-time")
_CODENAMES = ("aegis", "sentinel", "calliope", "echo", "caduceus", "charon")


def _strings(value) -> list[str]:
    # Flatten every string out of the module's public constants (tuples, dicts, dataclasses).
    if isinstance(value, str):
        return [value]
    if isinstance(value, (tuple, list)):
        return [s for v in value for s in _strings(v)]
    if isinstance(value, dict):
        return [s for kv in value.items() for v in kv for s in _strings(v)]
    if isinstance(value, (cb.GlossaryEntry, cb.ChartAsset)):
        return [s for v in vars(value).values() for s in _strings(v)]
    return []


def _all_copy() -> dict[str, list[str]]:
    public = {n: v for n, v in vars(cb).items() if not n.startswith("_") and n.isupper()}
    return {n: _strings(v) for n, v in public.items()}


def test_required_scope_statements_verbatim() -> None:
    # The governance statements the acceptance criteria name, pinned exactly (one source).
    assert cb.NO_ALERT_LINE == "No alert means review as normal — never 'safe'."
    low = cb.SCALE2_CONSTRAINT.lower()
    assert "scale 2" in low and "scale 1" in low and "88–92" in low and "clinically wrong" in low
    assert "need not move the aggregate score" in cb.OXYGEN_UPLIFT_LINE
    assert "silent-hypoxia" in cb.OXYGEN_UPLIFT_LINE
    guard = cb.VIRTUAL_WARD_GUARDRAIL
    assert "standalone remote monitoring" in guard and "deterioration prevention" in guard
    assert "(NHS England, 2024)" in guard


def test_cascade_definitions_are_settled_and_grounded() -> None:
    # The three cascade-stage definitions are now settled (methodology §5: decoupling → AEGIS →
    # threshold crossing): each is a real definition, none renders the placeholder, and stage 2
    # cross-references the AEGIS entry rather than restating it.
    cascade = [e for e in cb.GLOSSARY if "cascade stage" in e.term]
    assert len(cascade) == 3
    for e in cascade:
        assert not e.placeholder
        assert e.definition and e.definition != cb.PLACEHOLDER_DEFINITION
    assert not any(e.placeholder for e in cb.GLOSSARY)  # nothing renders as unsettled now
    stage2 = next(e for e in cb.GLOSSARY if e.term == "Early warning (cascade stage 2)")
    assert "Early warning (AEGIS)" in stage2.definition  # cross-references the entry above


def test_silent_window_is_defined() -> None:
    # The demo's default frame must be defined for a viewer — a real, non-placeholder definition
    # that ties the "silent" family together (references "silent hypoxia").
    entry = next((e for e in cb.GLOSSARY if e.term == "Silent window"), None)
    assert entry is not None and not entry.placeholder
    assert entry.definition != cb.PLACEHOLDER_DEFINITION
    assert "silent hypoxia" in entry.definition


def test_both_attribution_mechanisms_intact() -> None:
    # The RCP acknowledgement is a copyright condition — byte-for-byte from the assets pack —
    # distinct from the Harvard reference list (academic), which carries access dates.
    assert cb.RCP_ACKNOWLEDGEMENT == (
        "Reproduced from: Royal College of Physicians. National Early Warning Score (NEWS) 2: "
        "Standardising the assessment of acute-illness severity in the NHS. Updated report of a "
        "working party. London: RCP, 2017."
    )
    assert cb.DERIVED_BADGE.startswith("Derived from NEWS2")
    assert len(cb.REFERENCES) == 2
    assert cb.REFERENCES[0].startswith("NHS England (2024)")
    assert cb.REFERENCES[1].startswith("Royal College of Physicians (2017)")
    assert all("(Accessed: 12 June 2026)" in r for r in cb.REFERENCES)


def test_table_a_matches_assets_pack() -> None:
    # Table A verbatim from docs/STYX_clinical_basis_assets.md §A/§E (the NEWS2 Scale 1 bands).
    assert cb.TABLE_A_COLUMNS == ("3", "2", "1", "0", "1 ", "2 ", "3 ")
    assert cb.TABLE_A_SCORES == (3, 2, 1, 0, 1, 2, 3)
    assert cb.TABLE_A_ROWS == {
        "Respiration rate (min⁻¹)": ("≤8", "", "9–11", "12–20", "", "21–24", "≥25"),
        "SpO₂ — Scale 1 (%)": ("≤91", "92–93", "94–95", "≥96", "", "", ""),
        "Pulse / HR (min⁻¹)": ("≤40", "", "41–50", "51–90", "91–110", "111–130", "≥131"),
        "Temperature (°C)": ("≤35.0", "", "35.1–36.0", "36.1–38.0", "38.1–39.0", "≥39.1", ""),
    }


def test_ramp_is_the_schematics_own() -> None:
    # "Warm ramp matches the schematic" by construction: each table stop IS palette.WARM_RAMP at
    # the summed two-vital sub-score (2p) — and equals the assets §E literals exactly.
    assert RAMP_FOR_POINT == {0: "#FFFFFF", 1: "#F7D9C6", 2: "#E79C74", 3: "#C4532D"}
    assert all(RAMP_FOR_POINT[p] == palette.WARM_RAMP[2 * p] for p in range(4))


def test_new_styx_modules_import_no_streamlit() -> None:
    # LYR-1: logic and copy live in the package; the app is a thin client of it.
    for rel in ("styx/clinical_basis.py", "styx/viz/scoring_table.py"):
        source = (_REPO / rel).read_text(encoding="utf-8")
        assert not re.search(r"^\s*(import|from)\s+streamlit\b", source, re.M), f"LYR-1: {rel}"


def test_no_overclaim_and_codenames_confined_to_glossary() -> None:
    # Honesty lint over every public string; codenames may appear only where they are *defined*
    # (the glossary renders plain-name-first, e.g. "Early warning (AEGIS)") — nowhere else.
    glossary_text = " ".join(s for e in cb.GLOSSARY for s in _strings(e))
    for name, texts in _all_copy().items():
        for text in texts:
            hit = [p for p in _FORBIDDEN if p in text.lower()]
            assert not hit, f"{name} over-claims: {hit}"
            if name != "GLOSSARY":
                leak = [c for c in _CODENAMES if re.search(rf"\b{c}\b", text, re.IGNORECASE)]
                assert not leak, f"codename leaked outside the glossary in {name}: {leak}"
    assert re.search(r"\baegis\b", glossary_text, re.IGNORECASE)  # the glossary defines them
    assert re.search(r"\becho\b", glossary_text, re.IGNORECASE)


def test_page_renders_with_required_statements() -> None:
    # AppTest smoke over the rendered page: no exception, and the load-bearing statements —
    # no-alert ≠ safe, the NHS England citation — all visible; no placeholder renders any more.
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(_REPO / "app" / "pages" / "04_clinical_basis.py"),
                           default_timeout=90).run()
    assert not at.exception
    blob = " ".join(
        str(el.value)
        for kind in ("markdown", "caption", "info", "warning", "title")
        for el in getattr(at, kind)
    )
    assert cb.NO_ALERT_LINE in blob
    assert "[definition to confirm]" not in blob  # cascade definitions are settled now
    assert "(NHS England, 2024)" in blob
    assert cb.RCP_ACKNOWLEDGEMENT in blob


def test_chart_manifest_official_sources_and_files_present() -> None:
    # Every embedded chart is the official RCP artwork: sourced from rcp.ac.uk and rasterised
    # unmodified into app/assets/ (reproduced in colour, per the §B copyright rule).
    assert len(cb.CHARTS) == 3
    for chart in cb.CHARTS:
        assert chart.source_url.startswith("https://www.rcp.ac.uk/media/"), chart.filename
        assert (_REPO / "app" / "assets" / chart.filename).exists(), chart.filename
