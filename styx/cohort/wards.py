"""(6k) Ward grouping for the board — a pure, pid-derived presentation split.

The synthetic cohort has no ward attribute, so the board derives one: a fixed round-robin over
pids into ``WARD_COUNT`` boxes. Display labels come from ``styx.explain.WARD_LABEL_PRESETS``
(a setting preset, never stored on the patient). Digest-safe by construction: no RNG, no read
of vitals/history/risk — the pipeline digest cannot move.
"""

from __future__ import annotations

from styx.config import WARD_COUNT


def ward_of(pid: int) -> int:
    """The ward index (0..WARD_COUNT-1) a patient's card renders under — fixed round-robin."""
    return pid % WARD_COUNT
