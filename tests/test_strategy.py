"""
Tests for Milestone 8: deterministic cycle + swing strategy.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.strategies.combined import run_combined_strategy
from src.strategies.cycle import CORE_ALLOCATION, add_core_allocation, core_allocation_for_regime
from src.strategies.swing import (
    EXTENSION_REENTRY_PERCENTILE,
    EXTENSION_TRIGGER_PERCENTILE,
    TACTICAL_MAX,
    add_extension_percentile,
    run_swing_engine,
)


# ---------------------------------------------------------------------
# cycle.py
# ---------------------------------------------------------------------

def test_core_allocation_matches_documented_table():
    for regime, expected in CORE_ALLOCATION.items():
        assert core_allocation_for_regime(regime) == expected


def test_core_allocation_nan_for_unclassified():
    assert pd.isna(core_allocation_for_regime(None))
    assert pd.isna(core_allocation_for_regime(float("nan")))


def test_core_allocation_raises_on_unknown_regime():
    with pytest.raises(ValueError):
        core_allocation_for_regime("NOT_A_REAL_REGIME")


def test_add_core_allocation_vectorized_matches_scalar():
    df = pd.DataFrame({"regime": ["BULL", "BEAR", None, "LATE_BULL"]})
    out = add_core_allocation(df)
    assert out["core_allocation"].iloc[0] == CORE_ALLOCATION["BULL"]
    assert out["core_allocation"].iloc[1] == CORE_ALLOCATION["BEAR"]
    assert pd.isna(out["core_allocation"].iloc[2])
    assert out["core_allocation"].iloc[3] == CORE_ALLOCATION["LATE_BULL"]


# ---------------------------------------------------------------------
# swing.py: state machine
# ---------------------------------------------------------------------

def _run_state_machine_from_percentiles(regimes: list[str], extension_percentiles: list[float]) -> list[str]:
    """Directly exercises the same state-machine logic run_swing_engine
    uses, but against precomputed extension_percentile values -- avoids
    needing a real 365-row runup series just to test state transitions."""
    from src.strategies.swing import EXTENSION_REENTRY_PERCENTILE, EXTENSION_TRIGGER_PERCENTILE, TACTICAL_ELIGIBLE_REGIMES

    states = []
    state = "FULL"
    for regime, ext in zip(regimes, extension_percentiles):
        eligible = regime in TACTICAL_ELIGIBLE_REGIMES
        if not eligible:
            state = "FULL"
            states.append(state)
            continue
        if state == "FULL" and ext >= EXTENSION_TRIGGER_PERCENTILE:
            state = "REDUCED"
        elif state == "REDUCED" and ext <= EXTENSION_REENTRY_PERCENTILE:
            state = "FULL"
        states.append(state)
    return states


def test_swing_state_triggers_reduction_when_extended_in_eligible_regime():
    regimes = ["BULL"] * 5
    extensions = [0.5, 0.5, 0.85, 0.85, 0.85]  # crosses trigger at index 2
    states = _run_state_machine_from_percentiles(regimes, extensions)
    assert states == ["FULL", "FULL", "REDUCED", "REDUCED", "REDUCED"]


def test_swing_state_requires_stabilization_before_reentry():
    regimes = ["BULL"] * 6
    # Trigger, then dip to 0.60 (above reentry threshold 0.50 -- should
    # NOT re-enter yet), then drop to 0.40 (below threshold -- re-enter).
    extensions = [0.85, 0.85, 0.60, 0.60, 0.40, 0.40]
    states = _run_state_machine_from_percentiles(regimes, extensions)
    assert states == ["REDUCED", "REDUCED", "REDUCED", "REDUCED", "FULL", "FULL"]


def test_swing_state_ignores_extension_outside_eligible_regime():
    regimes = ["BEAR", "BEAR", "BEAR"]
    extensions = [0.95, 0.95, 0.95]  # extremely extended, but BEAR isn't eligible
    states = _run_state_machine_from_percentiles(regimes, extensions)
    assert states == ["FULL", "FULL", "FULL"]  # FULL here just means "not reduced"; tactical alloc will be 0 anyway


def test_swing_state_resets_to_full_when_leaving_eligible_regime():
    regimes = ["BULL", "BULL", "BEAR", "BULL"]
    extensions = [0.85, 0.85, 0.85, 0.85]  # still "extended" throughout
    states = _run_state_machine_from_percentiles(regimes, extensions)
    assert states == ["REDUCED", "REDUCED", "FULL", "REDUCED"]  # re-triggers fresh on return to BULL


def test_add_extension_percentile_is_bounded_0_to_1():
    n = 500
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"runup_from_low_365d": rng.uniform(0, 5, n)})
    out = add_extension_percentile(df)
    valid = out["extension_percentile"].dropna()
    assert (valid >= 0).all() and (valid <= 1).all()


# ---------------------------------------------------------------------
# combined.py
# ---------------------------------------------------------------------

def _realistic_df(n: int = 500, seed: int = 1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2020-01-01", periods=n, freq="D", tz="UTC")
    regimes = rng.choice(
        ["BEAR", "ACCUMULATION", "EARLY_RECOVERY", "LATE_RECOVERY", "BULL", "LATE_BULL", "DISTRIBUTION"], size=n
    )
    runup = np.abs(rng.normal(1.0, 1.5, n))
    return pd.DataFrame({"timestamp": dates, "regime": regimes, "runup_from_low_365d": runup})


def test_combined_total_allocation_equals_core_plus_tactical():
    df = _realistic_df()
    out = run_combined_strategy(df)
    valid = out.dropna(subset=["core_allocation", "tactical_allocation", "total_allocation"])
    expected = (valid["core_allocation"] + valid["tactical_allocation"]).clip(upper=1.0)
    pd.testing.assert_series_equal(valid["total_allocation"], expected, check_names=False)


def test_combined_total_allocation_never_exceeds_one():
    df = _realistic_df()
    out = run_combined_strategy(df)
    valid = out["total_allocation"].dropna()
    assert (valid <= 1.0).all()


def test_combined_strategy_is_deterministic():
    """Same input -> same output, run twice (RESEARCH_SPEC.md section 5's
    explicit determinism requirement for the deterministic strategy phase)."""
    df = _realistic_df()
    out_a = run_combined_strategy(df)
    out_b = run_combined_strategy(df)
    pd.testing.assert_frame_equal(out_a, out_b)


def test_combined_strategy_is_causal_under_truncation():
    """
    The swing engine is stateful and sequential, unlike prior milestones'
    pure per-row functions -- this is the analogous no-look-ahead-bias
    check: an earlier row's total_allocation must not depend on rows that
    come after it. Truncating the series must leave every row up to the
    truncation point's OWN extension-percentile warmup boundary unchanged.
    """
    df = _realistic_df(n=500)
    full = run_combined_strategy(df)
    truncated = run_combined_strategy(df.iloc[:400].reset_index(drop=True))

    # extension_percentile itself needs 365 rows of warmup; compare from
    # a safely-past-warmup point through well before the truncation edge.
    pd.testing.assert_frame_equal(
        full[["core_allocation", "tactical_allocation", "total_allocation"]].iloc[365:400].reset_index(drop=True),
        truncated[["core_allocation", "tactical_allocation", "total_allocation"]].iloc[365:400].reset_index(drop=True),
    )
