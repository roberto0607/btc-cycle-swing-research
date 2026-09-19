"""
Tests for Milestone 15: locked holdout window definition and evaluation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.backtesting.locked_holdout import define_holdout, run_locked_holdout


def _synthetic_df(n: int = 1000, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2023-01-01", periods=n, freq="D", tz="UTC")
    close = 100 * np.cumprod(1 + rng.normal(0, 0.02, n))
    return pd.DataFrame({"timestamp": dates, "open": close, "close": close})


def test_define_holdout_returns_correct_length():
    df = _synthetic_df()
    start, end = define_holdout(df, months=6)
    assert end == df["timestamp"].max()
    days = (end - start).days
    assert 175 <= days <= 190  # ~6 months


def test_define_holdout_clamps_to_available_data():
    """If the dataset is shorter than the requested holdout, start
    should clamp to the earliest available date rather than go negative."""
    df = _synthetic_df(n=60)  # only 60 days of data
    start, end = define_holdout(df, months=6)
    assert start == df["timestamp"].min()


def test_run_locked_holdout_one_row_per_strategy():
    df = _synthetic_df()
    allocations = {
        "A": pd.Series(1.0, index=df.index),
        "B": pd.Series(0.0, index=df.index),
    }
    results = run_locked_holdout(df, allocations, months=3)
    assert len(results) == 2
    assert set(results["strategy"]) == {"A", "B"}


def test_run_locked_holdout_cash_strategy_has_zero_return():
    df = _synthetic_df()
    allocations = {"Cash": pd.Series(0.0, index=df.index)}
    results = run_locked_holdout(df, allocations, months=3)
    assert results.iloc[0]["total_return"] == pytest.approx(0.0, abs=1e-9)
    assert results.iloc[0]["n_trades"] == 0


def test_run_locked_holdout_restricts_to_window_only():
    """A strategy with wildly different behavior outside the holdout
    window must not affect the holdout result -- confirms the function
    actually restricts to the window rather than running on full history."""
    n = 1000
    dates = pd.date_range("2023-01-01", periods=n, freq="D", tz="UTC")
    # Explosive growth in the first 900 days, flat for the last 100.
    close = np.concatenate([100 * np.linspace(1, 50, 900), np.full(100, 5000.0)])
    df = pd.DataFrame({"timestamp": dates, "open": close, "close": close})

    allocations = {"Full": pd.Series(1.0, index=df.index)}
    # ~100 days holdout -> should only see the flat tail, not the 50x run-up.
    results = run_locked_holdout(df, allocations, months=100 / 30.44)
    assert results.iloc[0]["total_return"] < 0.05  # roughly flat, not 50x
