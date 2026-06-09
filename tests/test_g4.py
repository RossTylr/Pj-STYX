"""Gate G4 — rationale faithfulness. CALLIOPE is a strict template over the model's real top-k
attribution: it names only the closed vocabulary, its named top-1 risk driver matches the actual
deteriorating physiology, and the decomposition faithfully reconstructs the risk it explains.
Evidence comes from styx.rationale (LYR-1: imported, never reimplemented)."""

from styx.config import G4_FAITHFULNESS_FLOOR
from styx.rationale import VOCABULARY, explain
from styx.rationale.calliope import EFFORT_PROX, OXY_PROX
from styx.risk import risk_series
from styx.state import fit_embedding, learn_basins
from styx.synth import Archetype, build_cohort
from styx.synth.gates import breach_index, replay_windows

#: Ground-truth driver per generating archetype — independent of the attribution computation.
_SIGNATURE = {
    Archetype.SILENT_HYPOXIA: {OXY_PROX},
    Archetype.COMPENSATED: {EFFORT_PROX},
    Archetype.COUPLED: {OXY_PROX, EFFORT_PROX},  # both move — either is faithful
}


def _fitted():
    cohort = build_cohort(seed=42)
    emb = fit_embedding(cohort)
    return cohort, emb, learn_basins(cohort, emb)


def test_determinism_seed42() -> None:
    a, b = _fitted(), _fitted()
    ra = explain(a[0].silent_case(), a[1], a[2], 150)
    rb = explain(b[0].silent_case(), b[1], b[2], 150)
    assert ra == rb  # DET-1 — same seed → identical rationale


def test_vocabulary_is_closed() -> None:
    # The strict-template guarantee made executable: no rationale ever names an out-of-set signal.
    cohort, emb, basins = _fitted()
    vocab = set(VOCABULARY)
    for p in cohort.patients:
        for _, sl in replay_windows(p, cohort.rescore_cadence_min):
            named = set(explain(p, emb, basins, sl.stop - 1).terms)
            assert named <= vocab, f"out-of-vocabulary signal: {named - vocab}"


def test_additive_completeness() -> None:
    # A *faithful* attribution reconstructs the model output — the named terms sum to the risk.
    # Checked on the silent window (risk ≥ 0.1, pre-breach), where neither term saturates the clip
    # — the regime the rationale exists to explain (post-breach the proximity overshoots and clips).
    cohort, emb, basins = _fitted()
    p = cohort.silent_case()
    brk = breach_index(p) or p.t_min.size
    risk = risk_series(p, emb, basins)
    checked = 0
    for _, sl in replay_windows(p, cohort.rescore_cadence_min):
        idx = sl.stop - 1
        if idx >= brk or risk[idx] < 0.1:
            continue
        total = sum(v for _, v in explain(p, emb, basins, idx).top_k)
        assert abs(total - float(risk[idx])) < 1e-9, f"contributions don't reconstruct risk at {idx}"
        checked += 1
    assert checked > 0  # the silent case must have an active window to reconstruct


def test_top1_faithfulness_clears_floor() -> None:
    # On the held-out silent window, the named top-1 driver matches the true driving physiology.
    cohort, emb, basins = _fitted()
    agree = total = 0
    for p in cohort.patients:
        if p.archetype is Archetype.STABLE:
            continue
        brk = breach_index(p) or p.t_min.size
        risk = risk_series(p, emb, basins)
        for _, sl in replay_windows(p, cohort.rescore_cadence_min):
            idx = sl.stop - 1
            if idx >= brk or risk[idx] < 0.1:  # pre-breach, attribution meaningful
                continue
            total += 1
            agree += explain(p, emb, basins, idx).top_k[0][0] in _SIGNATURE[p.archetype]
    rate = agree / total
    assert rate >= G4_FAITHFULNESS_FLOOR, f"top-1 faithfulness {rate:.3f} below {G4_FAITHFULNESS_FLOOR}"


def test_headline_is_template_only() -> None:
    # Fixed grammar, never free narration: a single line, patient-anchored, with a numeric risk.
    cohort, emb, basins = _fitted()
    for p in cohort.patients:
        for _, sl in replay_windows(p, cohort.rescore_cadence_min):
            r = explain(p, emb, basins, sl.stop - 1)
            assert "\n" not in r.headline and r.headline.startswith(f"Patient {p.pid}:")
            # every expand line is a "<vocab term>: ..." pair — no free text
            for line in r.expand:
                assert line.split(":")[0] in VOCABULARY, f"non-template expand line: {line!r}"
