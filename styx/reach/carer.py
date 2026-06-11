"""R4 HERMES — a lay-language renderer over the existing CALLIOPE top-k (carer/patient register).

A *floor reach*, audience extension only: it relabels CALLIOPE's real top-k risk decomposition into
a patient-safe register and **preserves rank** — it never re-derives the explanation (single source:
``styx.rationale.explain`` produces the ranked, exactly-additive ``top_k``; this module only renames).
No predictive claim, no raw score, no σ.

The contract is *faithfulness*: the lay headline must point at the **same primary driver** as the
clinician one. Because HERMES reads ``top_k[0]`` directly (regime-independent — CALLIOPE keeps
``top_k`` ranked pre- and post-breach) and the register is injective, the lay top-1's underlying
factor is the clinician top-1 by construction. If the register ever collapsed two factors onto one
phrase, the lay headline would no longer name a unique driver — ``lay_explain`` raises rather than
ship that. Enforced by tests/test_reach_carer.py.

Reach isolation (LYR-1): imports core (``styx.rationale``, ``styx.explain``); core never imports
reach. Pure, deterministic, no module-level RNG, no Streamlit, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass

from styx.explain import CARER_NAMES, CARER_STATUS
from styx.rationale import Rationale
from styx.rationale.calliope import _STABLE_EPS

#: Lay headline when no single factor dominates the risk (CALLIOPE's stable template) — calm, not
#: an "all clear" (the scope line already says no alert ≠ safe).
STABLE_HEADLINE: str = "no single thing is standing out right now"


@dataclass(frozen=True)
class LayRationale:
    """A patient-safe relabelling of a CALLIOPE ``Rationale`` — rank preserved, nothing recomputed."""

    headline: str  # the lay top-1 phrase (the primary driver, in the carer register)
    primary_factor: str  # the underlying CALLIOPE factor id the lay headline names (faithfulness key)
    factors: tuple[tuple[str, str], ...]  # (lay phrase, underlying factor id) in CALLIOPE top-k rank
    regime: str  # passed through from the Rationale — not recomputed


@dataclass(frozen=True)
class LayStatus:
    """A patient-safe *status* for the carer page — calm, score-free, derived from the CALLIOPE regime."""

    status: str  # the carer-facing status phrase (from CARER_STATUS)
    state: str  # the underlying state key ("steady" | "watching" | "involved") — for tests/styling
    regime: str  # passed through from the Rationale — not recomputed


def lay_explain(rationale: Rationale) -> LayRationale:
    """Relabel a CALLIOPE rationale's top-k into the patient-safe register, preserving rank.

    Reads ``rationale.top_k`` as given (already ranked, exactly-additive); maps each factor through
    ``CARER_NAMES``. Raises ``ValueError`` if the register is non-injective over the factors present
    (a collapsed phrase cannot faithfully name a unique driver) or names a factor outside the map.
    """
    factors = tuple((_lay_phrase(factor), factor) for factor, _ in rationale.top_k)
    _guard_unambiguous(factors)

    primary_factor = rationale.top_k[0][0]
    dominant = rationale.top_k[0][1] >= _STABLE_EPS
    headline = _lay_phrase(primary_factor) if dominant else STABLE_HEADLINE
    return LayRationale(headline, primary_factor, factors, rationale.regime)


def lay_status(rationale: Rationale) -> LayStatus:
    """Map a CALLIOPE rationale to a calm, score-free carer status (regime + dominance only).

    Reads ``rationale.regime`` and ``rationale.top_k[0]`` as given — no recompute, no threshold maths.
    ``crossed`` → the team is already involved; otherwise a dominant top-1 → watching more closely,
    else steady. Pure, deterministic, imports core only (mirrors ``lay_explain``'s dominance test).
    """
    if rationale.regime == "crossed":
        state = "involved"
    elif rationale.top_k and rationale.top_k[0][1] >= _STABLE_EPS:
        state = "watching"
    else:
        state = "steady"
    return LayStatus(CARER_STATUS[state], state, rationale.regime)


def _lay_phrase(factor: str) -> str:
    """The patient-safe phrase for a CALLIOPE factor id — fail loud if the factor is unmapped."""
    try:
        return CARER_NAMES[factor]
    except KeyError as exc:  # a factor with no register entry must never silently vanish
        raise ValueError(f"no patient-safe register entry for factor {factor!r}") from exc


def _guard_unambiguous(factors: tuple[tuple[str, str], ...]) -> None:
    """Reject a relabelling where two distinct factors share a lay phrase (ambiguous headline)."""
    phrase_to_factor: dict[str, str] = {}
    for phrase, factor in factors:
        clash = phrase_to_factor.get(phrase)
        if clash is not None and clash != factor:
            raise ValueError(
                f"register collapses factors {clash!r} and {factor!r} onto one phrase {phrase!r}"
            )
        phrase_to_factor[phrase] = factor
