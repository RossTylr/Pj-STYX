"""styx.rationale — F8 CALLIOPE — strict template over top-k attribution.

Public surface for the gate test, the proof notebook, and the app
(LYR-1: import, never reimplement).
"""

from styx.rationale.calliope import VOCABULARY, Rationale, explain

__all__ = [
    "VOCABULARY",
    "Rationale",
    "explain",
]
