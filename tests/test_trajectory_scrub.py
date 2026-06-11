"""6d.2 — the clinical hero's scrub: markers reveal in cascade order as "now" passes each fire-time.

Builder-only (LYR-1): the figure takes ``now_idx`` and renders; the page's replay clock just sets
the index. ``now_idx=None`` must reproduce the 6d.1 static view (parked at the breach, all four).
"""

from __future__ import annotations

import re

import numpy as np

from styx.frame import build_context
from styx.readouts import news2_crossing
from styx.synth import build_cohort
from styx.viz.trajectory import clinical_trajectory_figure


def _setup():
    cohort = build_cohort(seed=42)
    patient = cohort.silent_case()
    ctx = build_context(cohort, patient)
    from styx.reach.decoupling import decoupling_onset

    d = decoupling_onset(patient)  # the silent case always carries an onset
    return patient, dict(
        decoupling_min=d.onset_min, aegis_min=ctx.fire.aegis_min,
        escalation_min=ctx.fire.threshold_min, news2_min=news2_crossing(patient),
    )


def _revealed(fig) -> set[int]:
    """The cascade-marker numbers present in the figure (from the ``"n · label"`` trace names)."""
    hits = (re.match(r"^([1-4]) · ", tr.name or "") for tr in fig.data)
    return {int(m.group(1)) for m in hits if m}


def test_markers_reveal_in_cascade_order() -> None:
    patient, fires = _setup()
    order = ["decoupling_min", "aegis_min", "escalation_min", "news2_min"]
    assert all(fires[k] is not None for k in order)
    # just before the first fire-time: path + now only, no markers yet
    before_i = int(np.searchsorted(patient.t_min, fires["decoupling_min"])) - 1
    assert _revealed(clinical_trajectory_figure(patient, **fires, now_idx=before_i)) == set()
    # at each fire-time (first sample at/past it), exactly the cascade so far is shown
    for n, key in enumerate(order, start=1):
        at_i = int(np.searchsorted(patient.t_min, fires[key]))
        fig = clinical_trajectory_figure(patient, **fires, now_idx=at_i)
        assert _revealed(fig) == set(range(1, n + 1)), f"wrong reveal at marker {n} ({key})"


def test_default_now_parks_at_breach_with_all_markers() -> None:
    patient, fires = _setup()
    fig = clinical_trajectory_figure(patient, **fires)  # now_idx=None → 6d.1 static view
    assert _revealed(fig) == {1, 2, 3, 4}


def test_marker_tooltips_carry_sim_time_and_vitals() -> None:
    patient, fires = _setup()
    fig = clinical_trajectory_figure(patient, **fires)
    tmpl = [tr.hovertemplate for tr in fig.data if re.match(r"^[1-4] · ", tr.name or "")]
    assert len(tmpl) == 4
    for t in tmpl:
        assert "sim-min" in t and "SpO₂" in t and "RR" in t
