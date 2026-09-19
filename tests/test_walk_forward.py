"""
Tests for Milestone 11: walk-forward window construction and evaluation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.backtesting.walk_forward import compare_to_benchmark_per_window, define_windows, run_walk_forward


def test_define_windows_covers_full_range_without_gaps_or_overlap():
    df = pd.DataFrame({"timestamp": pd.date_range("2015-01-01", periods=365 * 6, freq="D", tz="UTC")})
    windows = define_windows(df, window_years=2.0)

    assert windows[0][0] == df["timestamp"].min()
    assert windows[-1][1] == df["timestamp"].max()
    for i in range(len(windows) - 1):
        assert windows[i][1] == windows[i + 1][0]  # no gap, no overlap


def test_define_windows_last_window_may_be_shorter():
    # 5 years of data, 2-year windows -> windows of 2, 2, 1 years
    df = pd.DataFrame({"timestamp": pd.date_range("2015-01-01", periods=int(365.25 * 5), freq="D", tz="UTC")})
    windows = define_windows(df, window_years=2.0)
    assert len(windows) == 3
    last_window_days = (windows[-1][1] - windows[-1][0]).days
    assert last_window_days < 365 * 2  # shorter than a full window


def test_run_walk_forward_resets_capital_each_window():
    """
    The core property this milestone exists to guarantee: window 2 must
    NOT inherit window 1's ending value. Construct a price series that
    goes way up in window 1 then flat in window 2 with a constant
    allocation, and confirm window 2's own CAGR reflects only window 2's
    (flat) price action, not window 1's gains carried forward.
    """
    n_per_window = 400
    dates = pd.date_range("2015-01-01", periods=n_per_window * 2, freq="D", tz="UTC")
    # Window 1: price rises 10x. Window 2: price flat.
    window1_close = 100 * np.linspace(1, 10, n_per_window)
    window2_close = np.full(n_per_window, window1_close[-1])
    close = np.concatenate([window1_close, window2_close])
    df = pd.DataFrame({"timestamp": dates, "open": close, "close": close, "alloc": [1.0] * len(close)})

    windows = run_walk_forward(df, allocation_col="alloc", window_years=(n_per_window / 365.25))
    # Window 2 should show ~0% return (net of the single entry trade's
    # small baseline cost, a few bps) since price is flat within it --
    # NOT the huge multiple it would show if window 1's 10x gain had
    # carried over.
    window2_row = windows.iloc[1]
    assert window2_row["total_return"] == pytest.approx(0.0, abs=0.01)


def test_run_walk_forward_flags_only_last_window_as_most_recent():
    dates = pd.date_range("2015-01-01", periods=365 * 6, freq="D", tz="UTC")
    close = 100 * np.cumprod(1 + np.random.default_rng(0).normal(0, 0.01, len(dates)))
    df = pd.DataFrame({"timestamp": dates, "open": close, "close": close, "alloc": [0.5] * len(close)})

    windows = run_walk_forward(df, allocation_col="alloc", window_years=2.0)
    assert windows["is_most_recent"].sum() == 1
    assert windows.iloc[-1]["is_most_recent"] == True  # noqa: E712


def test_compare_to_benchmark_per_window_suffixes_overlapping_columns():
    """
    Regression test for a real bug caught by the end-to-end CLI run:
    n_days exists in both strategy and benchmark window tables, so after
    the merge it must become n_days_strategy / n_days_benchmark (pandas'
    default suffixing), not a bare 'n_days' -- code downstream that
    assumed the unsuffixed name crashed with a KeyError.
    """
    strategy = pd.DataFrame(
        {
            "window_start": pd.to_datetime(["2015-01-01"], utc=True),
            "window_end": pd.to_datetime(["2017-01-01"], utc=True),
            "n_days": [700],
            "cagr": [0.5],
            "max_drawdown": [-0.2],
            "is_most_recent": [True],
        }
    )
    benchmark = strategy.copy()
    merged = compare_to_benchmark_per_window(strategy, benchmark)
    assert "n_days_strategy" in merged.columns
    assert "n_days_benchmark" in merged.columns
    assert "n_days" not in merged.columns


def test_compare_to_benchmark_per_window_hand_computed():
    strategy = pd.DataFrame(
        {
            "window_start": pd.to_datetime(["2015-01-01", "2017-01-01"], utc=True),
            "window_end": pd.to_datetime(["2017-01-01", "2019-01-01"], utc=True),
            "cagr": [0.5, 0.1],
            "max_drawdown": [-0.2, -0.5],
            "is_most_recent": [False, True],
        }
    )
    benchmark = pd.DataFrame(
        {
            "window_start": pd.to_datetime(["2015-01-01", "2017-01-01"], utc=True),
            "window_end": pd.to_datetime(["2017-01-01", "2019-01-01"], utc=True),
            "cagr": [0.3, 0.3],
            "max_drawdown": [-0.4, -0.4],
            "is_most_recent": [False, True],
        }
    )
    merged = compare_to_benchmark_per_window(strategy, benchmark)
    # Window 1: strategy beats on both cagr (0.5>0.3) and drawdown (-0.2>-0.4).
    assert merged.iloc[0]["beat_on_cagr"] == True  # noqa: E712
    assert merged.iloc[0]["beat_on_drawdown"] == True  # noqa: E712
    # Window 2: strategy LOSES on cagr (0.1<0.3) but wins on drawdown (-0.5<-0.4 is worse).
    assert merged.iloc[1]["beat_on_cagr"] == False  # noqa: E712
    assert merged.iloc[1]["beat_on_drawdown"] == False  # noqa: E712
