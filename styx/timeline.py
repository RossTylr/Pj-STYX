"""Episode timeline — the fire-points assembled onto one ordered strip (build-once, no recompute).

Pure assembly (LYR-1): it *reads* the already-computed anticipation outputs off a prebuilt
``PatientContext`` — AEGIS / forecast / breach fire-indices and the banded ETA — and lays them on a
single object the patient page (and R4) render. It runs no model maths and re-calls no fire
function, so it can never drift from its sources (``tests/test_timeline.py`` asserts exactly that).
Deterministic (DET-1): every input is.
"""

from __future__ import annotations

from dataclasses import dataclass

from styx.cohort.ranking import eta_band
from styx.explain import TIMELINE_LABELS
from styx.forecast import project
from styx.frame import PatientContext
from styx.readouts import news2_crossing

#: Technical (clinician-facing) labels; the lay one-liners live in ``styx.explain.TIMELINE_LABELS``.
_TECH_LABELS: dict[str, str] = {
    "aegis": "AEGIS fire — baseline departure",
    "forecast": "forecast fire — cone reaches threshold",
    "eta": "projected escalation (banded)",
    "breach": "absolute threshold breach",
}


@dataclass(frozen=True)
class TimelineEvent:
    """One marker on the episode strip. For ``eta`` the band fields carry the projected window."""

    key: str  # "aegis" | "forecast" | "eta" | "breach"
    idx: int | None  # re-score index it fires at (None if it never fires)
    t_min: float | None  # sim-minute of the fire (None if it never fires)
    label_tech: str
    label_lay: str
    eta_soonest_min: float | None = None  # ETA only — cone upper edge crosses (soonest)
    eta_central_min: float | None = None  # ETA only — cone point crosses (None if it never does)
    eta_confident: bool = False  # ETA only — True iff the point forecast itself crosses


@dataclass(frozen=True)
class EpisodeTimeline:
    """The episode's fire-points on one axis, ordered AEGIS → forecast → ETA → breach."""

    pid: int
    default_idx: int  # the silent-window frame the ETA band is projected from (the money shot)
    events: tuple[TimelineEvent, ...]
    news2_crossing_min: float | None = None  # comparator: when the partial NEWS2 would escalate

    def _idx(self, key: str) -> int | None:
        return next((e.idx for e in self.events if e.key == key), None)

    @property
    def aegis(self) -> int | None:
        return self._idx("aegis")

    @property
    def forecast(self) -> int | None:
        return self._idx("forecast")

    @property
    def breach(self) -> int | None:
        return self._idx("breach")


def _point(ctx: PatientContext, idx: int | None, key: str) -> TimelineEvent:
    """A single-instant fire event (AEGIS / forecast / breach) read straight off the context."""
    t = None if idx is None else float(ctx.patient.t_min[idx])
    return TimelineEvent(key, idx, t, _TECH_LABELS[key], TIMELINE_LABELS[key])


def episode_timeline(ctx: PatientContext) -> EpisodeTimeline:
    """Assemble the episode timeline from the prebuilt context (no recompute of any fire-point).

    The single-instant fires come from the cached indices (``ctx.aegis_idx`` / ``ctx.ticks``); the
    ETA band is projected **once** from the silent-window frame (``ctx.default_idx``) and banded
    through the shared ``eta_band`` helper the ward board uses — a range, never a hard minute (UQ-1).
    """
    aegis = _point(ctx, ctx.ticks["aegis"], "aegis")
    forecast = _point(ctx, ctx.ticks["forecast"], "forecast")
    breach = _point(ctx, ctx.ticks["breach"], "breach")

    di = ctx.default_idx
    t = ctx.patient.t_min
    cone = project(ctx.risk, t, di, ctx.band)
    status, soonest, central, confident = eta_band(
        cone, float(t[di]), float(ctx.risk[di]), ctx.threshold
    )
    eta = TimelineEvent(
        "eta", di, float(t[di]), _TECH_LABELS["eta"], TIMELINE_LABELS["eta"],
        eta_soonest_min=soonest, eta_central_min=central, eta_confident=confident,
    )

    # The named-standard comparator (read-only over vitals): when NEWS2 would first escalate.
    news2 = news2_crossing(ctx.patient)

    return EpisodeTimeline(ctx.patient.pid, di, (aegis, forecast, eta, breach), news2)
