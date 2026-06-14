"""Per-patient trajectory diversity — escalators are distinct, not clones, and stagger in time.

Slice A adds per-escalator severity + decoupling-onset jitter (patient 0 stays the scripted index
case). These checks prove the diversity is real *and* that it preserves the per-patient phenomenon:
every escalator still has a silent window and a finite breach. G1/G3 (which read only patient 0) are
guarded by their own suites; here we cover patients 1..n.
"""

from styx.synth import Archetype, build_cohort, has_silent_window
from styx.synth.gates import breach_index, decoupling_onset_index
from styx.synth.scenario import DT_MIN


def _escalators(cohort):
    return [p for p in cohort.patients if p.archetype is not Archetype.STABLE]


def test_patient_zero_is_frozen_index_case() -> None:
    # The diversity draws must not touch the scripted index case (G1/G3 baseline).
    p = build_cohort(seed=42).silent_case()
    assert p.pid == 0 and p.archetype is Archetype.SILENT_HYPOXIA
    assert has_silent_window(p)


#: The silent presentations — COMPENSATED is deliberately *visible* (effort rises, RR breaches), so
#: it is not required to carry a silent window; only the silent phenotypes are.
_SILENT_ARCHETYPES = (Archetype.SILENT_HYPOXIA, Archetype.COUPLED)


def test_every_escalator_breaches_in_stay() -> None:
    # Jitter must not push any escalator's breach outside the stay.
    for p in _escalators(build_cohort(seed=42)):
        assert breach_index(p) is not None, f"patient {p.pid} never breaches in-stay"


def test_silent_phenotypes_keep_silent_window() -> None:
    # The silent presentations must still be silent after jitter (COMPENSATED is exempt by design).
    for p in _escalators(build_cohort(seed=42)):
        if p.archetype in _SILENT_ARCHETYPES:
            assert has_silent_window(p), f"patient {p.pid} ({p.archetype.value}) lost its silent window"


def test_onsets_span_a_range() -> None:
    # The stagger is real: silent windows open at materially different times across the cohort.
    onsets = [
        decoupling_onset_index(p) for p in _escalators(build_cohort(seed=42))
    ]
    onsets = [o for o in onsets if o is not None]
    spread_min = (max(onsets) - min(onsets)) * DT_MIN
    assert spread_min >= 60.0, f"onset spread only {spread_min} sim-min — not staggered"


def test_diversity_is_deterministic() -> None:
    # DET-1 — same seed → identical jittered onsets.
    a = [decoupling_onset_index(p) for p in _escalators(build_cohort(seed=42))]
    b = [decoupling_onset_index(p) for p in _escalators(build_cohort(seed=42))]
    assert a == b
