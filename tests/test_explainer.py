"""Explainer integrity — the copy analogue of the closed-vocabulary gate (test_g4).

Two guarantees on the plain-language registry: it covers every rendered component (completeness),
and it never over-claims (honesty lint) — no "predicts the patient" / "diagnoses" / "learns the
patient" / "real-time", while keeping the synthetic/replay/constructed anchors. Evidence comes from
styx.explain (LYR-1: imported, never reimplemented)."""

from styx.explain import COMPONENTS, EXPLAINERS

#: Over-claims STYX must never make (Hard Rule 7: replay-of-synthetic, not a live predictor).
_FORBIDDEN = ("predicts the patient", "diagnoses", "learns the patient", "real-time")
#: Honesty anchors that must appear somewhere in the registry (present "where relevant").
_ANCHORS = ("synthetic", "replay", "constructed")


def test_registry_covers_every_component() -> None:
    # Completeness: exactly one non-empty card per rendered component, no orphans, no gaps.
    assert set(EXPLAINERS) == set(COMPONENTS), f"mismatch: {set(EXPLAINERS) ^ set(COMPONENTS)}"
    for cid in COMPONENTS:
        e = EXPLAINERS[cid]
        assert e.what.strip() and e.how.strip() and e.why.strip(), f"empty card: {cid}"


def test_no_overclaim() -> None:
    # Honesty lint: not one card may imply STYX diagnoses, predicts a person, or runs live.
    for cid, e in EXPLAINERS.items():
        blob = f"{e.what} {e.how} {e.why}".lower()
        hit = [p for p in _FORBIDDEN if p in blob]
        assert not hit, f"{cid} over-claims: {hit}"


def test_honesty_anchors_present() -> None:
    # The replay-of-synthetic framing must be stated somewhere in the registry.
    blob = " ".join(f"{e.what} {e.how} {e.why}" for e in EXPLAINERS.values()).lower()
    missing = [a for a in _ANCHORS if a not in blob]
    assert not missing, f"missing honesty anchors: {missing}"
