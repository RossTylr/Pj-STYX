"""No engineer's codename in rendered output (S5.7) — the analogue of ``test_no_raw_enum``.

Plain UK-clinical language faces the ward; the Greek codenames (AEGIS, SENTINEL, CALLIOPE, ECHO,
and the reserved CADUCEUS / CHARON) live only in the code — function/module/key identifiers and
docstrings, never in anything a user reads. This is the load-bearing guard: it is what stops a
codename creeping back into the UI via a future reach panel (R3/R4 especially).

Two arms, because ``AppTest`` is blind to the inside of a Plotly figure:
  * page-text arm — drive the real pages via ``AppTest`` and scan every text element they render;
  * figure arm — build the ``styx.viz`` figures directly and scan their serialised strings (titles,
    annotations, lane labels, legend/trace names — none of which the page-text arm can see).
"""

from __future__ import annotations

import re

from streamlit.testing.v1 import AppTest

from styx.config import THRESHOLDS
from styx.frame import build_context, patient_frame
from styx.synth import build_cohort
from styx.timeline import episode_timeline

_WARD = "app/pages/02_ward.py"
_PATIENT = "app/pages/01_patient.py"

#: The codenames that must never survive into rendered, user-facing output — matched whole-word,
#: case-insensitively (so a lowercase hover leak is caught too). Plain-only: there are no exemptions.
CODENAMES: tuple[str, ...] = ("AEGIS", "SENTINEL", "CALLIOPE", "ECHO", "CADUCEUS", "CHARON")
_LEAK = re.compile(r"\b(" + "|".join(CODENAMES) + r")\b", re.IGNORECASE)


def _rendered_text(at) -> str:
    parts: list[str] = []
    for coll in (at.markdown, at.caption, at.title, at.header, at.subheader):
        parts += [el.value for el in coll]
    for m in at.metric:
        parts += [str(m.label), str(m.value)]
    for df in at.get("dataframe"):
        parts.append(df.value.to_string())
    return " ".join(parts)


def _figure_strings(obj) -> list[str]:
    """Every string leaf in a Plotly figure dict — title, annotations, names, axis/category text."""
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in _figure_strings(v)]
    if isinstance(obj, (list, tuple)):
        return [s for v in obj for s in _figure_strings(v)]
    return []


# --- guard the guard ---------------------------------------------------------------------------

def test_codename_matcher_catches_a_known_leak() -> None:
    # The forbid-set must actually fire on the codenames it names (and tolerate case).
    assert _LEAK.search("Early warning (AEGIS)")
    assert _LEAK.search("echo illustrates")
    assert not _LEAK.search("Similar past patients")  # the plain replacement is clean


# --- page-text arm -----------------------------------------------------------------------------

def test_patient_page_shows_no_codename() -> None:
    pt = AppTest.from_file(_PATIENT, default_timeout=90)
    pt.session_state["patient_pick"] = 0
    pt.run()
    assert not pt.exception
    hit = _LEAK.search(_rendered_text(pt))
    assert hit is None, f"codename {hit.group()!r} leaked into the patient page"


def test_ward_page_shows_no_codename() -> None:
    at = AppTest.from_file(_WARD, default_timeout=90).run()
    assert not at.exception
    hit = _LEAK.search(_rendered_text(at))
    assert hit is None, f"codename {hit.group()!r} leaked into the ward board"


# --- figure arm (covers the AppTest plotly blind spot) -----------------------------------------

def _figure_builders() -> dict:
    """Map every public viz builder → a thunk building its figure as the page does (seed=42).

    Keyed by the builder *function object* so the meta-test below can assert, by identity, that the
    scan covers every ``*_figure`` discovered in ``styx.viz`` — a new reach builder is forced in here
    before the suite can pass. The patient + cohort fit is done once and shared across thunks.
    """
    from styx.cohort import build_cohort_context
    from styx.cohort.echo import echo_neighbours
    from styx.reach.decoupling import decoupling_onset
    from styx.reach.history import stratify
    from styx.viz.carer import carer_timeline_figure
    from styx.viz.coherence import coherence_figure
    from styx.viz.cone import cone_figure
    from styx.viz.echo import echo_figure
    from styx.viz.hazard import hazard_figure
    from styx.viz.theograph import detail_strip_figure, ribbon_figure
    from styx.viz.timeline import timeline_figure
    from styx.viz.trajectory import trajectory_figure
    from styx.viz.waterline import waterline_figure

    cohort = build_cohort(seed=42)
    patient = cohort.silent_case()
    ctx = build_context(cohort, patient)
    frame = patient_frame(ctx, ctx.default_idx)
    cctx = build_cohort_context(cohort)
    focus_pid = cctx.cohort.silent_case().pid
    now_idx = cctx.default_idx
    neighbours = echo_neighbours(cctx, focus_pid, now_idx)
    d = decoupling_onset(patient)  # patient is the silent case → onset always present
    return {
        trajectory_figure: lambda: trajectory_figure(
            patient, ctx.emb, ctx.basins, events=ctx.on_path),
        timeline_figure: lambda: timeline_figure(episode_timeline(ctx)),
        carer_timeline_figure: lambda: carer_timeline_figure(episode_timeline(ctx)),
        coherence_figure: lambda: coherence_figure(
            patient.t_min, d.coherence, d.onset_min, aegis_min=ctx.fire.aegis_min),
        waterline_figure: lambda: waterline_figure(
            patient.t_min, ctx.risk, ctx.threshold, aegis_idx=ctx.aegis_idx),
        cone_figure: lambda: cone_figure(
            patient.t_min, ctx.risk, frame.cone, THRESHOLDS.risk_escalation,
            now_idx=ctx.default_idx, ghost=ctx.ghost),
        ribbon_figure: lambda: ribbon_figure(ctx.events),
        detail_strip_figure: lambda: detail_strip_figure(ctx.events),
        echo_figure: lambda: echo_figure(cctx, focus_pid, neighbours, now_idx),
        hazard_figure: lambda: hazard_figure(
            stratify(cctx), focus_density=float(sum(patient.theograph.values()))),
    }


def _discover_viz_builders() -> set:
    """Every public ``*_figure`` builder defined in ``styx.viz`` — the set the scan must cover."""
    import importlib
    import inspect
    import pkgutil

    import styx.viz

    found = set()
    for m in pkgutil.iter_modules(styx.viz.__path__):
        mod = importlib.import_module(f"styx.viz.{m.name}")
        for name, fn in inspect.getmembers(mod, inspect.isfunction):
            # public, builds a figure, and *defined here* (not re-imported from a sibling).
            if name.endswith("_figure") and not name.startswith("_") and fn.__module__ == mod.__name__:
                found.add(fn)
    return found


def test_viz_figures_carry_no_codename() -> None:
    for build in _figure_builders().values():
        fig = build()
        for s in _figure_strings(fig.to_dict()):
            hit = _LEAK.search(s)
            assert hit is None, f"codename {hit.group()!r} leaked into a viz figure: {s!r}"


def test_every_viz_builder_is_scanned() -> None:
    # Self-maintaining: when a reach adds a `*_figure` (R1 hazard panel, R3 graph), this fails with
    # the builder's name until a thunk is added to _figure_builders() — the guard can't silently gap.
    missing = _discover_viz_builders() - set(_figure_builders())
    assert not missing, (
        "viz builder(s) not covered by the no-codename figure scan: "
        f"{sorted(f.__name__ for f in missing)} — add a thunk to _figure_builders()"
    )
