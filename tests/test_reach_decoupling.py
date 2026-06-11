"""R3a.1 mechanism gate — the decoupling onset + the cascade marker verdict.

Mechanism-only: this asserts the decoupling is a *real, sustained, single-sourced* signal and
places it in the cascade. There is no accuracy/lift claim (S5.5 is binding) — none is tested.
"""

import numpy as np

from styx.config import DECOUPLING_LEAD_MIN, RESCORE_CADENCE_MIN
from styx.reach.decoupling import cascade_verdict, decoupling_onset
from styx.synth import build_cohort
from styx.synth.gates import (
    decoupling_lead_min,
    decoupling_onset_index,
    windowed_coherence,
)


def _silent(seed: int = 42):
    c = build_cohort(seed=seed)
    return c, c.silent_case()


def test_determinism_seed42() -> None:
    # DET-1 — two independent builds yield an identical onset and an identical verdict.
    (ca, pa), (cb, pb) = _silent(), _silent()
    a, b = decoupling_onset(pa), decoupling_onset(pb)
    assert (a.onset_index, a.onset_min, a.g1_lead_min, a.breach_min, a.silent_window) == (
        b.onset_index, b.onset_min, b.g1_lead_min, b.breach_min, b.silent_window
    )
    va, vb = cascade_verdict(ca, pa), cascade_verdict(cb, pb)
    assert (va.markers, va.gap_min, va.onset_min, va.aegis_min) == (
        vb.markers, vb.gap_min, vb.onset_min, vb.aegis_min
    )


def test_single_source() -> None:
    # The reach reads the G1 computation — it never recomputes coherence or the lead.
    _, p = _silent()
    d = decoupling_onset(p)
    assert d.onset_index == decoupling_onset_index(p)
    assert d.g1_lead_min == decoupling_lead_min(p)
    assert np.array_equal(
        d.coherence, windowed_coherence(p.vitals["RR"], p.vitals["SpO2"]), equal_nan=True
    )


def test_mechanism_is_real() -> None:
    # Claim-integrity: the onset exists, the silent window holds, the lead clears the G1 floor.
    _, p = _silent()
    d = decoupling_onset(p)
    assert d.onset_index is not None
    assert d.silent_window is True
    assert d.g1_lead_min >= DECOUPLING_LEAD_MIN  # ≥ floor — a real, sustained mechanism (not lift)


def test_cascade_verdict() -> None:
    # The gate output: 2 or 3 markers, consistent with the one-cadence margin rule.
    c, p = _silent()
    v = cascade_verdict(c, p)
    assert v.markers in {2, 3}
    assert v.detectably_earlier == (v.gap_min > RESCORE_CADENCE_MIN)
    assert v.markers == (3 if v.detectably_earlier else 2)
