"""Episode-timeline integrity — determinism, ordering (G3-consistent), and single-source.

The timeline assembles existing fire-points; these tests prove it (a) is deterministic, (b) keeps
the AEGIS → forecast → breach order, and (c) **cannot drift** from its sources — each event index
equals the canonical value the rest of styx computes. Evidence from styx (LYR-1: imported)."""

from styx.cohort.ranking import eta_band
from styx.forecast import project
from styx.frame import build_context
from styx.risk import aegis_fire_index
from styx.synth import build_cohort
from styx.timeline import episode_timeline
from styx.viz.timeline import timeline_figure


def _ctx():
    cohort = build_cohort(seed=42)
    return cohort, build_context(cohort, cohort.silent_case())


def test_determinism_seed42() -> None:
    a = episode_timeline(_ctx()[1])
    b = episode_timeline(_ctx()[1])
    assert a == b  # DET-1 — same seed → identical timeline


def test_order_is_g3_consistent() -> None:
    tl = episode_timeline(_ctx()[1])
    assert tl.aegis is not None and tl.forecast is not None and tl.breach is not None
    assert tl.aegis < tl.forecast < tl.breach  # the anticipation order, as in G3


def test_single_source_consistency() -> None:
    cohort, ctx = _ctx()
    tl = episode_timeline(ctx)
    # Fire-points are read straight off the context — never recomputed in the timeline.
    assert tl.aegis == ctx.aegis_idx == ctx.ticks["aegis"]
    assert tl.aegis == aegis_fire_index(ctx.patient, ctx.emb, ctx.indices)
    assert tl.forecast == ctx.ticks["forecast"]
    assert tl.breach == ctx.ticks["breach"]
    # ETA band matches the shared helper applied to the silent-window cone (no separate maths).
    di = ctx.default_idx
    t = ctx.patient.t_min
    cone = project(ctx.risk, t, di, ctx.band)
    status, soon, cen, conf = eta_band(cone, float(t[di]), float(ctx.risk[di]), ctx.threshold)
    eta = next(e for e in tl.events if e.key == "eta")
    assert (eta.eta_soonest_min, eta.eta_central_min, eta.eta_confident) == (soon, cen, conf)


def test_figure_builds() -> None:
    fig = timeline_figure(episode_timeline(_ctx()[1]))
    assert len(fig.data) >= 1  # at least the fired markers render
