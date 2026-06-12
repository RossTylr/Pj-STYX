"""R4a HERMES faithfulness gate — the lay relabel must name the clinician's primary driver.

Patient-facing, so the bar is *exact* (1.000, not ≥0.90): a carer line that reorders or contradicts
the clinician CALLIOPE top-1 is a safety/honesty failure. CALLIOPE is regime-aware, so faithfulness
is checked **pre- and post-breach**. Two further guards: the patient-safe register carries no
alarming/clinical term and no codename, and it stays injective (no two factors collapse onto one
lay phrase — which would make the headline ambiguous about which driver it names).
"""

import re

from streamlit.testing.v1 import AppTest

from styx.cohort import build_cohort_context
from styx.explain import (
    CARER_ACTION,
    CARER_FOOTER,
    CARER_NAMES,
    CARER_STATUS,
    CARER_TIMELINE_NAMES,
)
from styx.frame import build_context
from styx.rationale import explain
from styx.reach.carer import STABLE_HEADLINE, lay_explain, lay_status
from styx.synth import build_cohort
from styx.timeline import episode_timeline
from styx.viz.carer import carer_timeline_figure

#: Alarming / clinical register the carer-facing copy must never carry (the R4 patient-safe set).
_BANNED = (
    "breach", "fires", "fire", "red zone", "news2", "crisis", "scale 1", "threshold",
    "escalat", "alarm", "deteriorat", "danger", "emergency", "critical",
)
#: Engineer's codenames — never in user-facing copy (mirrors tests/test_explainer.py::_CODENAMES).
_CODENAMES = ("aegis", "sentinel", "calliope", "echo", "caduceus", "charon", "hermes", "styx")


def _copy_offences(text: str) -> list[str]:
    """Strict matcher for *authored* carer copy: alarming term, codename (incl. styx/hermes), or raw
    score. The product name and version live only in rendered provenance, never in authored copy — so
    here the full ``_CODENAMES`` and the raw-score regex apply (cf. the looser rendered-scan matcher
    used on the page/figure, where ``v0.5``/axis floats would false-positive)."""
    low = text.lower()
    hits = [b for b in _BANNED if b in low]
    hits += [c for c in _CODENAMES if re.search(rf"\b{c}\b", low)]
    if re.search(r"\dσ|\d\.\d|risk \d", low):
        hits.append("raw-score")
    return hits


#: The carer (family) surface is the *softest* register: unlike the clinician pages it must not even
#: carry the *product* name "STYX"/"HERMES" (plan-review decision — the brand is engineer/clinical
#: framing that does not belong on the lay surface; the clinician footer keeps it, the carer footer
#: ``CARER_FOOTER`` is brand-free). So the rendered matcher bans the *full* codename set — it differs
#: from the authored matcher only in dropping the raw-score regex (a rendered surface legitimately
#: shows a patient id like "patient 0", which the strict \d\.\d guard would false-positive on).
def _rendered_offences(text: str) -> list[str]:
    """Matcher for *rendered* carer surfaces — alarming term or any codename (incl. the product name)."""
    low = text.lower()
    hits = [b for b in _BANNED if b in low]
    hits += [c for c in _CODENAMES if re.search(rf"\b{c}\b", low)]
    return hits


def _figure_strings(obj) -> list[str]:
    """Every string leaf in a Plotly figure dict (re-created from tests/test_no_codename.py to keep
    this module self-contained — there is no ``tests`` package to import from)."""
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in _figure_strings(v)]
    if isinstance(obj, (list, tuple)):
        return [s for v in obj for s in _figure_strings(v)]
    return []


def _rendered_text(at) -> str:
    """Every text element an AppTest can see (re-created from tests/test_no_codename.py)."""
    parts: list[str] = []
    for coll in (at.markdown, at.caption, at.title, at.header, at.subheader):
        parts += [el.value for el in coll]
    for m in at.metric:
        parts += [str(m.label), str(m.value)]
    for df in at.get("dataframe"):
        parts.append(df.value.to_string())
    return " ".join(parts)


def _ctx(seed: int = 42):
    return build_cohort_context(build_cohort(seed=seed))


def _pre_idx(risk, threshold, grid):
    """A representative pre-breach scrub index (risk below the line), or None."""
    pres = [i for i in grid if risk[i] < threshold]
    return pres[len(pres) // 2] if pres else None


def _post_idx(risk, threshold, grid):
    """The first post-breach scrub index (risk at/above the line), or None if it never crosses."""
    posts = [i for i in grid if risk[i] >= threshold]
    return posts[0] if posts else None


def _windows(cctx):
    """Every (patient, idx) the faithfulness gate sweeps — a pre- and a post-breach window each."""
    for p in cctx.cohort.patients:
        risk = cctx.risk[p.pid]
        for idx in (_pre_idx(risk, cctx.threshold, cctx.indices),
                    _post_idx(risk, cctx.threshold, cctx.indices)):
            if idx is not None:
                yield p, idx


def test_hermes_faithfulness() -> None:
    # The headline number: the lay top-1 names the clinician CALLIOPE top-1 across the cohort,
    # pre- and post-breach. Patient-facing → exactly 1.000.
    reverse = {phrase: factor for factor, phrase in CARER_NAMES.items()}
    cctx = _ctx()
    agree = total = 0
    for p, idx in _windows(cctx):
        r = explain(p, cctx.emb, cctx.basins, idx)
        lay = lay_explain(r)
        total += 1
        clinician_top1 = r.top_k[0][0]
        # rank preserved — the lay factor order is the CALLIOPE top-k order, unchanged.
        assert tuple(f for _, f in lay.factors) == tuple(f for f, _ in r.top_k)
        # the recovered underlying factor of the lay headline == the clinician top-1.
        recovered = reverse.get(lay.headline) if lay.headline != STABLE_HEADLINE else clinician_top1
        if recovered == clinician_top1 and lay.primary_factor == clinician_top1:
            agree += 1
    assert total > 0
    faithfulness = agree / total
    assert faithfulness == 1.0, f"faithfulness {faithfulness:.3f} over {total} windows (must be 1.000)"


def test_register_injective() -> None:
    # No two factors collapse onto one lay phrase — the guard in lay_explain can never be defeated.
    assert len(set(CARER_NAMES.values())) == len(CARER_NAMES)


def test_patient_safe_register() -> None:
    # Every register value is free of alarming/clinical terms and of codenames.
    for factor, phrase in CARER_NAMES.items():
        low = phrase.lower()
        banned = [b for b in _BANNED if b in low]
        assert not banned, f"{factor!r} carries alarming term(s) {banned}: {phrase!r}"
        codenames = [c for c in _CODENAMES if re.search(rf"\b{c}\b", phrase, re.IGNORECASE)]
        assert not codenames, f"{factor!r} carries codename(s) {codenames}: {phrase!r}"
        assert not re.search(r"\dσ|\d\.\d|risk \d", low), f"{factor!r} leaks a raw score: {phrase!r}"


def test_determinism_seed42() -> None:
    # DET-1 — the relabel carries no RNG; two independent builds render identically.
    a, b = _ctx(), _ctx()
    pa = a.cohort.silent_case()
    pb = b.cohort.silent_case()
    la = lay_explain(explain(pa, a.emb, a.basins, a.default_idx))
    lb = lay_explain(explain(pb, b.emb, b.basins, b.default_idx))
    assert la == lb


# --- R4b: carer status + safe action ----------------------------------------------------------

def test_carer_status_safe_register() -> None:
    # Every authored status phrase is free of alarming/clinical terms, codenames and raw scores.
    for state, phrase in CARER_STATUS.items():
        assert not _copy_offences(phrase), f"CARER_STATUS[{state!r}] offends {_copy_offences(phrase)}: {phrase!r}"


def test_carer_action_safe_register() -> None:
    # The one safe action is contact / what-to-watch only — pristine register, no clinical instruction.
    assert not _copy_offences(CARER_ACTION), f"CARER_ACTION offends {_copy_offences(CARER_ACTION)}"


def test_carer_footer_safe_register() -> None:
    # The carer footer is brand-free provenance — pristine register, no product name/codename/score.
    assert not _copy_offences(CARER_FOOTER), f"CARER_FOOTER offends {_copy_offences(CARER_FOOTER)}"


def test_lay_status_faithful_and_calm() -> None:
    # status ↔ state stay consistent, and "involved" appears iff the regime has crossed — a carer is
    # never told "nothing standing out" post-threshold. Both silent states are reachable in the cohort.
    cctx = _ctx()
    seen = set()
    for p, idx in _windows(cctx):
        r = explain(p, cctx.emb, cctx.basins, idx)
        s = lay_status(r)
        assert s.status == CARER_STATUS[s.state]
        assert (s.state == "involved") == (r.regime == "crossed")
        assert s.regime == r.regime
        seen.add(s.state)
    assert "involved" in seen and ("watching" in seen or "steady" in seen)


def test_lay_status_determinism_seed42() -> None:
    # DET-1 — the status carries no RNG; two independent builds render identically.
    a, b = _ctx(), _ctx()
    sa = lay_status(explain(a.cohort.silent_case(), a.emb, a.basins, a.default_idx))
    sb = lay_status(explain(b.cohort.silent_case(), b.emb, b.basins, b.default_idx))
    assert sa == sb


# --- R4b: carer timeline figure ---------------------------------------------------------------

def test_carer_timeline_names_safe_register() -> None:
    # Every authored carer timeline label is pristine register (strict matcher).
    for key, phrase in CARER_TIMELINE_NAMES.items():
        assert not _copy_offences(phrase), \
            f"CARER_TIMELINE_NAMES[{key!r}] offends {_copy_offences(phrase)}: {phrase!r}"


def test_carer_timeline_figure_safe_register() -> None:
    # AppTest is blind inside Plotly, so scan the figure dict directly: no codename, no alarming term.
    ctx = build_context(build_cohort(seed=42), build_cohort(seed=42).silent_case())
    fig = carer_timeline_figure(episode_timeline(ctx))
    for s in _figure_strings(fig.to_dict()):
        assert not _rendered_offences(s), f"carer figure leaks {_rendered_offences(s)} in {s!r}"


def test_carer_timeline_figure_is_descriptive_only() -> None:
    # The strip never draws a *future* event (no predictive claim): the only fire-moment it can show is
    # the early warning, and only once it has already happened by the silent-window frame.
    ctx = build_context(build_cohort(seed=42), build_cohort(seed=42).silent_case())
    tl = episode_timeline(ctx)
    strings = " ".join(_figure_strings(carer_timeline_figure(tl).to_dict())).lower()
    # the carer label for any *future* fire-point (forecast/eta/breach) must not appear
    assert "projected" not in strings and "forecast" not in strings
    # the early-warning label appears iff that moment is already in the past at the drawn frame
    aegis = next((e for e in tl.events if e.key == "aegis"), None)
    already = aegis is not None and aegis.idx is not None and aegis.idx <= tl.default_idx
    assert ("watching more closely" in strings) == already


# --- R4b: carer page (page-text arm — hand-maintained, both matchers) --------------------------

def test_carer_page_safe_register() -> None:
    # Drive the real carer page and scan every text element it renders — the softest register: no
    # alarming/clinical term and no codename *including the product name* (the carer footer is the
    # brand-free CARER_FOOTER; STYX is softened off the family surface — plan-review decision).
    at = AppTest.from_file("app/pages/03_patient_display.py", default_timeout=90)
    at.session_state["patient_pick"] = 0
    at.run()
    assert not at.exception
    offences = _rendered_offences(_rendered_text(at))
    assert not offences, f"carer page leaked: {offences}"
