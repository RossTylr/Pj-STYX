"""Explainer integrity — the copy analogue of the closed-vocabulary gate (test_g4).

Two guarantees on the plain-language registry: it covers every rendered component (completeness),
and it never over-claims (honesty lint) — no "predicts the patient" / "diagnoses" / "learns the
patient" / "real-time", while keeping the synthetic/replay/constructed anchors. Evidence comes from
styx.explain (LYR-1: imported, never reimplemented)."""

import re
from pathlib import Path

from styx.explain import (
    ARCHETYPE_PATTERNS,
    CARER_NAMES,
    COHERENCE_LABELS,
    COMPARISON_LABELS,
    COMPONENTS,
    CONDITION,
    DISPLAY_NAMES,
    ETA_BANDS,
    EXPLAINERS,
    KM_STRATUM_LABELS,
    NEWS2_COMPARATOR_LABEL,
    SCOPE_LINE,
    SCORE_CAPTION,
    TIMELINE_LABELS,
    TRAJECTORY_MARKERS,
    WARD_LABEL_PRESETS,
    WARD_PRESET_NAMES,
    WATCH_TIER_CRITERIA,
    WATCH_TIER_LABELS,
)
from styx.synth import Archetype
from styx.timeline import _TECH_LABELS

_STYX = Path(__file__).resolve().parent.parent / "styx"

#: Over-claims STYX must never make (Hard Rule 7: replay-of-synthetic, not a live predictor).
_FORBIDDEN = ("predicts the patient", "diagnoses", "learns the patient", "real-time")
#: Honesty anchors that must appear somewhere in the registry (present "where relevant").
_ANCHORS = ("synthetic", "replay", "constructed")
#: (S5.7) Engineer's codenames the user-facing copy must never carry — plain-only, no exemptions.
#: They survive as code identifiers (keys, modules) and DISPLAY_NAMES is what the pages render.
_CODENAMES = ("aegis", "sentinel", "calliope", "echo", "caduceus", "charon")


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


def test_timeline_labels_honesty() -> None:
    # The episode-timeline lay labels are linted alongside the cards (one per event, no over-claim).
    assert set(TIMELINE_LABELS) == {"aegis", "forecast", "eta", "breach"}
    for key, label in TIMELINE_LABELS.items():
        assert label.strip(), f"empty timeline label: {key}"
        hit = [p for p in _FORBIDDEN if p in label.lower()]
        assert not hit, f"timeline label {key} over-claims: {hit}"


def test_honesty_anchors_present() -> None:
    # The replay-of-synthetic framing must be stated somewhere in the registry.
    blob = " ".join(f"{e.what} {e.how} {e.why}" for e in EXPLAINERS.values()).lower()
    missing = [a for a in _ANCHORS if a not in blob]
    assert not missing, f"missing honesty anchors: {missing}"


def test_no_codename_in_copy() -> None:
    # (S5.7/S5.8) Plain-only lint over every display-bound string map: no card, timeline label,
    # display name, technical episode label, pattern label, or ETA band may carry a codename. The
    # rendered guard is tests/test_no_codename.py; this keeps the source copy clean at the registry.
    # _TECH_LABELS is the clinician-facing episode strip (R4) — guarded plain before it ever renders.
    values = (
        [f"{e.what} {e.how} {e.why}" for e in EXPLAINERS.values()]
        + list(TIMELINE_LABELS.values())
        + list(DISPLAY_NAMES.values())
        + list(_TECH_LABELS.values())
        + list(ARCHETYPE_PATTERNS.values())
        + list(ETA_BANDS.values())
        + list(KM_STRATUM_LABELS.values())
        + list(CARER_NAMES.values())  # (R4) HERMES patient-safe register — plain, no codenames
        + list(COHERENCE_LABELS.values())  # (R3a.2) CADUCEUS coherence-panel labels — plain copy
        + list(TRAJECTORY_MARKERS.values())  # (6d) hero cascade-marker hover copy — plain copy
        + list(WATCH_TIER_LABELS.values())  # (6e) watchlist urgency-tier labels — plain copy
        + list(WATCH_TIER_CRITERIA.values())  # (6e) tier criteria captions — plain copy
        + list(COMPARISON_LABELS.values())  # (S7) NEWS2 A/B side-by-side labels — plain copy
        + list(WARD_PRESET_NAMES.values())  # (6k) board setting presets — plain copy
        + [s for labels in WARD_LABEL_PRESETS.values() for s in labels]  # (6k) ward labels
    )
    for text in values:
        hit = [c for c in _CODENAMES if re.search(rf"\b{c}\b", text, re.IGNORECASE)]
        assert not hit, f"codename leaked into copy {text!r}: {hit}"


# --- S5.6 new copy: the honesty-lint extended to the index caption, NEWS2 label, scope, bands ---


def test_score_caption_and_news2_label_honest() -> None:
    # (6f) The index caption must warn it is not NEWS2; the comparator label must state its scope —
    # 6 of 7 (BP + consciousness from the nurse round), naming the one param still unscored.
    assert "not NEWS2" in SCORE_CAPTION
    low = NEWS2_COMPARATOR_LABEL.lower()
    assert "6 of 7" in low and "scale 1" in low and "nurse" in low
    for named in ("bp", "consciousness", "o₂"):  # the two now scored + the one still unscored
        assert named in low


def test_scope_line_states_blind_spots() -> None:
    # (6b) The scope line names what STYX sees, the blind-spots, and what "no alert" must not mean.
    for token in ("RR", "SpO₂", "HR", "Temp", "blood pressure", "consciousness"):
        assert token in SCOPE_LINE, f"scope line missing {token}"
    low = SCOPE_LINE.lower()
    assert "review as normal" in low and "never" in low and "safe" in low


def test_eta_bands_keys_closed() -> None:
    # (6i) Exactly the five ordinal band keys ``styx.readouts.eta_ordinal`` can return.
    assert set(ETA_BANDS) == {"lt30", "30_60", "1_2h", "gt2h", "unclear"}


def test_archetype_patterns_carry_no_raw_enum() -> None:
    # (6g) One lay "Pattern" label per archetype; the snake_case raw enum must not survive in it.
    assert set(ARCHETYPE_PATTERNS) == {a.value for a in Archetype}
    for value, label in ARCHETYPE_PATTERNS.items():
        assert label.strip() and "_" not in label, f"raw enum leaks into {value!r}: {label!r}"


def test_condition_relabelled_not_copd() -> None:
    # The condition is acute respiratory infection, not COPD — forward-looking source carries no
    # bare "COPD" (only explicit "not COPD" disclaimers are allowed).
    assert "copd" not in CONDITION.lower()
    for py in _STYX.rglob("*.py"):
        for ln in py.read_text(encoding="utf-8").splitlines():
            if "copd" in ln.lower():
                assert "not" in ln.lower(), f"bare COPD in {py.name}: {ln.strip()}"
