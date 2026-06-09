"""styx.risk — F4 risk + escalation · F7 AEGIS silent-deterioration.

Public surface for the gate test, the proof notebook, and the app (LYR-1: import, never reimplement).
"""

from styx.risk.aegis import aegis_axis_departures, aegis_fire_index, aegis_signal
from styx.risk.score import (
    decoupling_drop,
    escalation_fire_index,
    exceedance_per_vital,
    proximity_components,
    risk_series,
)

__all__ = [
    "aegis_axis_departures",
    "aegis_fire_index",
    "aegis_signal",
    "decoupling_drop",
    "escalation_fire_index",
    "exceedance_per_vital",
    "proximity_components",
    "risk_series",
]
