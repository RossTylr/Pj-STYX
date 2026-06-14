"""F3 — care-event model. Expand the cohort's per-channel event *counts* into a dated timeline.

The synthetic engine stores each patient's lifelong care history as ``Patient.theograph`` — a
per-channel *count* (DET-1, set in ``styx.synth.cohort``), not a list of dated events. This module
materialises those counts into timestamped ``CareEvent``s deterministically, seeded from the patient
id (no module-level RNG, no change to ``synth`` → G1 untouched). Placement is recency-biased: a
frail patient's contacts intensify as the illness declares, so more events fall near *now* — which
also gives the recent-days detail strip content. These are *derived* events for the display layer
(Hard Rule 6): an overlay, never a claim that an event changed the physiology.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from styx.config import CHANNELS, SEED
from styx.state.embedding import Embedding, trajectory_path
from styx.synth.cohort import Patient
from styx.synth.scenario import DT_MIN, N_SAMPLES

#: Lifelong history horizon (days) over which past care events are spread.
LIFELONG_DAYS: float = 1825.0  # ~5 years
#: Recent-window span (days) for the detail strip aligned to the live episode.
RECENT_DAYS: float = 14.0
#: The live monitored episode occupies the final day (the 24 h ward stay → sim-minute frame).
EPISODE_DAYS: float = 1.0
#: Recency bias: t_days = -LIFELONG_DAYS · u**POWER pulls events toward now as POWER grows.
RECENCY_POWER: float = 2.5

#: Channel-specific recency. Primary-care / outpatient contacts intensify as the illness declares,
#: so they cluster harder toward now (a higher power) — giving the recent-days detail strip a visible
#: run-up into the stay. Other channels fall back to RECENCY_POWER. Re-timing only: counts are fixed.
_CHANNEL_POWER: dict[str, float] = {"primary_care": 5.0, "outpatient": 4.0}

#: A&E→admission clustering: a non-elective admission is usually preceded by an A&E attendance. We
#: place this fraction of a patient's *existing* A&E events a short lead before a drawn admission
#: (the rest stay recency-biased) — a readable history, not extra volume (Hard Rule 6).
_AE_PAIR_PROB: float = 0.6
_AE_LEAD_DAYS: tuple[float, float] = (0.5, 4.0)  # A&E precedes the admission by this many days

_EPISODE_SPAN_MIN: float = float((N_SAMPLES - 1) * DT_MIN)  # 1435 sim-min


def _care_event(channel: str, t_days: float) -> CareEvent:
    """Build one CareEvent, deriving its in-episode flag + sim-minute position (the shared mapping)."""
    in_ep = bool(t_days >= -EPISODE_DAYS)
    t_min = (t_days + EPISODE_DAYS) / EPISODE_DAYS * _EPISODE_SPAN_MIN if in_ep else float("nan")
    return CareEvent(channel, float(t_days), in_ep, float(t_min))


def _recency_times(rng: np.random.Generator, n: int, power: float) -> np.ndarray:
    """n event times (days before now, ≤0), recency-biased by ``power`` (higher → nearer now)."""
    return -LIFELONG_DAYS * (rng.random(n) ** power)


@dataclass(frozen=True)
class CareEvent:
    """One dated care contact on a named channel. ``t_days`` ≤ 0 (days before now)."""

    channel: str
    t_days: float
    in_episode: bool  # falls within the final EPISODE_DAYS → has a sim-minute position
    t_min: float  # sim-minute within the episode (nan when not in_episode)


def expand_history(patient: Patient) -> tuple[CareEvent, ...]:
    """Materialise ``patient.theograph`` counts into a deterministic, narrative event timeline.

    Per-channel *counts* are preserved exactly (Hard Rule 6 — a display overlay, not new volume);
    only the *timing* carries the story: contacts are recency-biased (per channel), and a fraction of
    A&E attendances are clustered just before a non-elective admission (the readable A&E→admit run-up).
    """
    rng = np.random.default_rng((SEED, patient.pid))  # explicit vector seed → DET-1
    events: list[CareEvent] = []
    # Admissions first: their times anchor the A&E pairing below (fixed channel order → DET-1).
    admit_times = _recency_times(rng, int(patient.theograph["non_elective_admission"]), RECENCY_POWER)
    for channel in CHANNELS:
        n = int(patient.theograph[channel])
        if n <= 0:
            continue
        if channel == "non_elective_admission":
            times = admit_times
        elif channel == "ae" and admit_times.size:
            times = _recency_times(rng, n, RECENCY_POWER)
            for i in range(n):  # attach a fraction of A&E events to a drawn admission, a lead earlier
                if rng.random() < _AE_PAIR_PROB:
                    anchor = float(admit_times[rng.integers(admit_times.size)])
                    lead = rng.uniform(*_AE_LEAD_DAYS)
                    times[i] = max(anchor - lead, -LIFELONG_DAYS)
        else:
            times = _recency_times(rng, n, _CHANNEL_POWER.get(channel, RECENCY_POWER))
        events.extend(_care_event(channel, td) for td in times)
    return tuple(sorted(events, key=lambda e: e.t_days))


def recent_events(
    events: tuple[CareEvent, ...], window_days: float = RECENT_DAYS
) -> tuple[CareEvent, ...]:
    """The subset within the recent window — the detail strip aligned to the live episode."""
    return tuple(e for e in events if e.t_days >= -window_days)


def events_on_path(
    patient: Patient, emb: Embedding, events: tuple[CareEvent, ...]
) -> list[tuple[int, CareEvent]]:
    """Map each in-episode event to its nearest trajectory sample index (for path markers)."""
    _ = trajectory_path(patient, emb)  # path indices share the sample grid; validates emb fit
    out: list[tuple[int, CareEvent]] = []
    for e in events:
        if not e.in_episode:
            continue
        idx = int(np.clip(round(e.t_min / DT_MIN), 0, N_SAMPLES - 1))
        out.append((idx, e))
    return out
