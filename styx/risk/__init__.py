"""styx.risk — F4 risk + escalation · F7 AEGIS silent-deterioration.

Public surface for the gate test, the proof notebook, and the app (LYR-1: import, never reimplement).
"""

from styx.risk.aegis import aegis_fire_index, aegis_signal
from styx.risk.score import escalation_fire_index, risk_series

__all__ = [
    "aegis_fire_index",
    "aegis_signal",
    "escalation_fire_index",
    "risk_series",
]
