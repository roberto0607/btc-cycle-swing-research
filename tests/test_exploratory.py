"""
Tests for Milestone 5 exploratory statistics.

Correctness tests use small hand-computable synthetic series. The last
test (test_drawdown_detection_finds_a_known_bear_market) is a sanity
check, not a strict unit test: it builds a multi-cycle synthetic series
with an unmistakable, deliberately-injected 80% drawdown and confirms the
detector finds an episode of roughly that depth -- catching the kind of
"technically passes unit tests but produces nonsense on real data" bug
that small-fixture tests alone can miss.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.research.statistics.exploratory import (
    add_forward_return_for_research,
    extension_vs_forward_return,
    find_drawdown_episodes,
    summarize_returns,
    top_drawdowns,
    yearly_breakdown,
)


def _price_path(closes: list[float], start="2024-01-01") -> pd.DataFrame:
    n = len(closes)
    dates = pd.date_range(start, periods=n, freq="D", tz="UTC")
    df = pd.DataFrame({"timestamp": dates, "close": closes})
    df["return_1d"] = df["close"].pct_change()
    running_max = df["close"].cummax()
    df["drawdown_from_ath"] = (df["close"] - running_max) / running_max
    return df


def test_summarize_returns_hand_computed():
    # Exactly doubles over 365 days -> CAGR should be ~100%.
    closes = [100.0] + [100.0 * (2 ** (i / 364)) for i in range(1, 365)]
    df = _price_path(closes)
    summary = summarize_returns(df)

    assert summary["total_return"] == pytest.approx(1.0, rel=1e-2)
    assert summary["cagr"] == pytest.approx(1.0, rel=1e-2)
    assert summary["max_drawdown"] == pytest.approx(0.0, abs=1e-9)  # monotonic up, no drawdown


def test_yearly_breakdown_splits_correctly():
    closes = [100 + i for i in range(730)]  # 2 full years, straight line up
    df = _price_path(closes)
    yearly = yearly_breakdown(df)

    assert set(yearly["year"]) == {2024, 2025}
    assert (yearly["return"] > 0).all()


def test_find_drawdown_episodes_detects_single_dip():
    # Up to 100, down to 50 (50% drawdown), back up to a new high of 120.
    closes = [80, 90, 100, 90, 70, 50, 70, 90, 110, 120]
    df = _price_path(closes)

    episodes = find_drawdown_episodes(df)
    assert len(episodes) == 1
    ep = episodes[0]
    assert ep.depth == pytest.approx(-0.5, rel=1e-6)  # (50-100)/100
    assert ep.recovery_date is not None  # recovered by reaching 120 > 100


def test_find_drawdown_episodes_marks_ongoing_when_unrecovered():
    closes = [100, 110, 120, 100, 80, 90]  # ends underwater, never re-hits 120
    df = _price_path(closes)

    episodes = find_drawdown_episodes(df)
    assert len(episodes) == 1
    assert episodes[0].recovery_date is None


def test_top_drawdowns_sorted_deepest_first():
    # Two dips: a shallow one, then a deep one.
    closes = [100, 90, 100, 100, 40, 100]
    df = _price_path(closes)

    top = top_drawdowns(df, n=10)
    assert len(top) == 2
    assert top.iloc[0]["depth"] < top.iloc[1]["depth"]  # most negative first


def test_add_forward_return_for_research_is_shifted_correctly():
    closes = [100.0, 110.0, 121.0, 133.1]
    df = _price_path(closes)
    fwd_1d = add_forward_return_for_research(df, horizon=1)

    # fwd_1d[t] should equal close[t+1]/close[t] - 1
    assert fwd_1d.iloc[0] == pytest.approx(0.10, rel=1e-6)
    assert fwd_1d.iloc[1] == pytest.approx(0.10, rel=1e-6)
    assert pd.isna(fwd_1d.iloc[-1])  # no future data for the last row


def test_extension_vs_forward_return_deciles_are_monotonic_for_designed_relationship():
    """
    Construct a series where higher `extension` mechanically means lower
    forward return (by design), and confirm the binned decile means come
    out monotonically decreasing -- validates the binning/aggregation
    logic itself, independent of any real-market question.
    """
    n = 500
    rng = np.random.default_rng(0)
    extension = rng.uniform(0, 1, size=n)
    forward_return = -extension + rng.normal(0, 0.01, size=n)  # strong negative relationship
    df = pd.DataFrame({"extension": extension, "fwd": forward_return})

    binned = extension_vs_forward_return(df, "extension", "fwd")
    means = binned.sort_values("decile")["return_mean"].to_numpy()
    assert np.all(np.diff(means) < 0)  # strictly decreasing decile-to-decile


def test_drawdown_detection_finds_a_known_bear_market():
    """
    Sanity check, not a tight unit test: build a synthetic multi-year
    series with an unmistakable ~80% drawdown in the middle (roughly the
    depth of BTC's actual 2018 and 2022 bear markets) and confirm the
    detector finds an episode of comparable depth. This is the kind of
    check that catches "the code runs and unit tests pass but the output
    doesn't look like real BTC history" bugs that small fixtures miss.
    """
    rng = np.random.default_rng(7)
    n = 365 * 4
    # Bull run up, then a sharp ~80% crash, then partial recovery.
    bull = 100 * (1.003 ** np.arange(365))
    crash = bull[-1] * (0.994 ** np.arange(365))  # ~80% decline over a year
    recovery = crash[-1] * (1.002 ** np.arange(365 * 2))
    closes = np.concatenate([bull, crash, recovery])
    closes = closes * (1 + rng.normal(0, 0.01, size=len(closes)))  # daily noise
    closes = np.maximum(closes, 1.0)

    df = _price_path(list(closes))
    top = top_drawdowns(df, n=5)

    assert not top.empty
    deepest = top.iloc[0]["depth"]
    assert deepest < -0.5  # found a real, deep drawdown, not noise-level dips
