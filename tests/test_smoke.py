"""S0 smoke test — package imports and the core constants are wired (no gate logic)."""

import styx
from styx.config import SEED, VITALS


def test_package_imports() -> None:
    assert styx.__version__


def test_seed_is_42() -> None:
    assert SEED == 42  # DET-1


def test_vitals_is_sig1_tight_set() -> None:
    assert len(VITALS) == 5  # SIG-1: RR, SpO2, HR, temp + one labs proxy
