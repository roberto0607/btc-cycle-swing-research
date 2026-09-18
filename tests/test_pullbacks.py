"""
Tests for Milestone 7: PULLBACK label construction and regime-conditional
extension-vs-pullback analysis.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.research.pullbacks.analysis import regime_conditional_extension_pullback
from src.research.pullbacks.labels import (
    add_pullback_labels,
    forward_min_close_return,
    forward_min_low_return,
)


def test_forward_min_low_return_hand_computed():
    close = pd.Series([100.0, 100.0, 100.0, 100.0])
    low = pd.Series([100.0, 95.0, 80.0, 90.0])
    fwd = forward_min_low_return(close, low, horizon=2)
    # At t=0: min(low[1], low[2]) = min(95, 80) = 80 -> 80/100 - 1 = -0.20
    assert fwd.iloc[0] == pytest.approx(-0.20, rel=1e-6)


def test_forward_min_close_return_hand_computed():
    close = pd.Series([100.0, 90.0, 80.0, 120.0])
    fwd = forward_min_close_return(close, horizon=2)
    # At t=0: min(close[1], close[2]) = min(90, 80) = 80 -> -0.20
    assert fwd.iloc[0] == pytest.approx(-0.20, rel=1e-6)


def test_add_pullback_labels_boolean_correctness():
    n = 10
    close = pd.Series([100.0] * n)
    low = close.copy()
    low.iloc[5] = 85.0  # a 15% intraperiod dip on day 5
    df = pd.DataFrame({"close": close, "low": low})

    out = add_pullback_labels(df, thresholds=(0.10, 0.20), horizons=(5,))

    # A day whose next-5-day window includes day 5's 85 low should show
    # a 10% pullback but NOT a 20% pullback.
    assert bool(out["pullback_10pct_5d"].iloc[0]) is True
    assert bool(out["pullback_20pct_5d"].iloc[0]) is False


def test_add_pullback_labels_does_not_mislabel_missing_future_as_no_pullback():
    """
    Regression test for a real bug caught before this shipped: comparing
    NaN <= -threshold silently evaluates to False in plain pandas boolean
    comparison, which would mislabel "we don't have enough future data
    yet" (end of series) as "confirmed no pullback happened". The label
    for those rows must be NA, not False.
    """
    n = 10
    df = pd.DataFrame({"close": [100.0] * n, "low": [100.0] * n})
    out = add_pullback_labels(df, thresholds=(0.10,), horizons=(5,))

    # The last 5 rows don't have a full 5-day forward window -> must be NA.
    tail_labels = out["pullback_10pct_5d"].iloc[-5:]
    assert tail_labels.isna().all()

    # Rows WITH a full forward window and no actual dip must be False, not NA.
    head_labels = out["pullback_10pct_5d"].iloc[:5]
    assert (head_labels == False).all()  # noqa: E712 (nullable boolean, not plain bool)
    assert not head_labels.isna().any()


def test_add_pullback_labels_column_naming():
    df = pd.DataFrame({"close": [100.0] * 20, "low": [100.0] * 20})
    out = add_pullback_labels(df, thresholds=(0.05, 0.10), horizons=(7, 14))

    for col in ["pullback_5pct_7d", "pullback_10pct_7d", "pullback_5pct_14d", "pullback_10pct_14d"]:
        assert col in out.columns


def test_add_pullback_labels_is_causal_under_truncation():
    """
    Truncation-based no-look-ahead check, adapted for a FORWARD-looking
    label (unlike Milestones 4/5's backward-looking features): rows more
    than `horizon` days before the truncation point must be identical,
    since their forward window is entirely intact in both versions. Rows
    within `horizon` of the cut correctly lose data (their forward window
    got shorter) and are excluded from the comparison on purpose -- that
    NA change is correct behavior, not leakage.
    """
    n = 200
    horizon = 14
    rng = np.random.default_rng(0)
    close = 100 * np.cumprod(1 + rng.normal(0, 0.02, n))
    low = close * (1 - rng.uniform(0, 0.05, n))
    df = pd.DataFrame({"close": close, "low": low})

    truncate_at = 150
    full = add_pullback_labels(df, thresholds=(0.10,), horizons=(horizon,))
    truncated = add_pullback_labels(
        df.iloc[:truncate_at].reset_index(drop=True), thresholds=(0.10,), horizons=(horizon,)
    )

    safe_cutoff = truncate_at - horizon  # rows before this have a full, unaffected forward window
    pd.testing.assert_series_equal(
        full["pullback_10pct_14d"].iloc[:safe_cutoff].reset_index(drop=True),
        truncated["pullback_10pct_14d"].iloc[:safe_cutoff].reset_index(drop=True),
        check_names=False,
    )


def test_add_pullback_labels_unaffected_by_data_beyond_the_horizon_window():
    """
    The precise no-look-ahead-bias property for a bounded forward-looking
    label: mutating price data BEYOND row t's horizon window must never
    change row t's label. This is the direct analogue of Milestone 4's
    "future value change" leakage test.
    """
    n = 200
    horizon = 14
    rng = np.random.default_rng(1)
    close = 100 * np.cumprod(1 + rng.normal(0, 0.02, n))
    low = close * (1 - rng.uniform(0, 0.05, n))
    df = pd.DataFrame({"close": close, "low": low})

    labels_a = add_pullback_labels(df, thresholds=(0.10,), horizons=(horizon,))

    df_mutated = df.copy()
    df_mutated.loc[199, ["close", "low"]] *= 0.1  # a wild crash on the very last day

    labels_b = add_pullback_labels(df_mutated, thresholds=(0.10,), horizons=(horizon,))

    # Row 100's forward window is rows 101..114 -- row 199 is far outside
    # it, so row 100's label must be identical despite the mutation.
    check_through = 199 - horizon  # every row whose window ends before row 199
    pd.testing.assert_series_equal(
        labels_a["pullback_10pct_14d"].iloc[:check_through],
        labels_b["pullback_10pct_14d"].iloc[:check_through],
        check_names=False,
    )


def test_regime_conditional_extension_pullback_separates_by_bucket():
    """
    Design a series where higher extension mechanically means a higher
    pullback rate WITHIN one regime, and confirm the bucketed table
    reflects that (High bucket's pullback_rate > Low bucket's), while a
    second regime with the opposite designed relationship shows the
    reverse -- validating that bucketing happens per-regime, not globally.
    """
    n = 600
    rng = np.random.default_rng(3)
    regime = np.where(np.arange(n) < n // 2, "REGIME_A", "REGIME_B")
    extension = rng.uniform(0, 1, n)

    # REGIME_A: high extension -> more likely to pull back.
    # REGIME_B: high extension -> less likely to pull back.
    prob_pullback = np.where(regime == "REGIME_A", extension, 1 - extension)
    pullback = rng.uniform(0, 1, n) < prob_pullback

    df = pd.DataFrame({"extension": extension, "pullback": pullback, "regime": regime})
    table = regime_conditional_extension_pullback(df, "extension", "pullback", n_buckets=3)

    a_low = table[(table["regime"] == "REGIME_A") & (table["extension_bucket"] == "Low")]["pullback_rate"].iloc[0]
    a_high = table[(table["regime"] == "REGIME_A") & (table["extension_bucket"] == "High")]["pullback_rate"].iloc[0]
    b_low = table[(table["regime"] == "REGIME_B") & (table["extension_bucket"] == "Low")]["pullback_rate"].iloc[0]
    b_high = table[(table["regime"] == "REGIME_B") & (table["extension_bucket"] == "High")]["pullback_rate"].iloc[0]

    assert a_high > a_low
    assert b_high < b_low


def test_regime_conditional_extension_pullback_includes_all_baseline():
    n = 300
    rng = np.random.default_rng(4)
    df = pd.DataFrame(
        {
            "extension": rng.uniform(0, 1, n),
            "pullback": rng.uniform(0, 1, n) < 0.3,
            "regime": rng.choice(["X", "Y"], n),
        }
    )
    table = regime_conditional_extension_pullback(df, "extension", "pullback", n_buckets=3)
    assert "ALL" in table["regime"].values


def test_regime_conditional_extension_pullback_skips_undersized_regime():
    """A regime with too few rows to form reliable buckets should be
    silently omitted, not crash or report a misleadingly precise rate."""
    n = 100
    rng = np.random.default_rng(6)
    regime = ["TINY"] * 5 + ["BIG"] * (n - 5)
    df = pd.DataFrame(
        {
            "extension": rng.uniform(0, 1, n),
            "pullback": rng.uniform(0, 1, n) < 0.3,
            "regime": regime,
        }
    )
    table = regime_conditional_extension_pullback(df, "extension", "pullback", n_buckets=3)
    assert "TINY" not in table["regime"].values
    assert "BIG" in table["regime"].values
