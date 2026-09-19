"""
Tests for Milestone 10: parameter perturbation, execution degradation,
and per-cycle breakdown.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.backtesting.robustness import (
    execution_model_comparison,
    parameter_perturbation,
    per_cycle_metrics,
    scaled_cycle_allocation,
)
from src.strategies.cycle import CORE_ALLOCATION


def _multi_cycle_df(n_bull: int = 400, n_crash: int = 150, seed: int = 5) -> pd.DataFrame:
    """Two full bull/bear cycles where each cycle's peak exceeds the
    previous cycle's peak (as real BTC cycles have historically done),
    so per_cycle_metrics has two genuine, independent peak-to-peak
    segments to find -- not just one big unresolved drawdown."""
    rng = np.random.default_rng(seed)
    segments_close = []
    segments_regime = []
    price = 100.0
    for _ in range(2):
        bull = price * (1.006 ** np.arange(n_bull))
        crash = bull[-1] * (0.985 ** np.arange(n_crash))
        segments_close.append(bull)
        segments_regime.extend(["BULL"] * n_bull)
        segments_close.append(crash)
        segments_regime.extend(["BEAR"] * n_crash)
        price = crash[-1]
    close = np.concatenate(segments_close) * (1 + rng.normal(0, 0.005, (n_bull + n_crash) * 2))
    close = np.maximum(close, 1.0)
    n = len(close)
    dates = pd.date_range("2018-01-01", periods=n, freq="D", tz="UTC")
    running_max = pd.Series(close).cummax()
    drawdown_from_ath = (close - running_max) / running_max
    return pd.DataFrame(
        {
            "timestamp": dates,
            "open": close * (1 + rng.normal(0, 0.002, n)),
            "close": close,
            "regime": segments_regime,
            "drawdown_from_ath": drawdown_from_ath,
        }
    )


# ---------------------------------------------------------------------
# Parameter perturbation
# ---------------------------------------------------------------------

def test_scaled_cycle_allocation_at_scale_one_matches_original_table():
    df = pd.DataFrame({"regime": ["BULL", "BEAR", "DISTRIBUTION"]})
    scaled = scaled_cycle_allocation(df, scale=1.0)
    assert scaled.iloc[0] == pytest.approx(CORE_ALLOCATION["BULL"])
    assert scaled.iloc[1] == pytest.approx(CORE_ALLOCATION["BEAR"])
    assert scaled.iloc[2] == pytest.approx(CORE_ALLOCATION["DISTRIBUTION"])


def test_scaled_cycle_allocation_clips_to_valid_range():
    df = pd.DataFrame({"regime": ["BULL"] * 3})
    scaled_high = scaled_cycle_allocation(df, scale=5.0)  # would exceed 1.0 unclipped
    assert (scaled_high <= 1.0).all()

    scaled_negative_direction = scaled_cycle_allocation(df, scale=0.0)
    assert (scaled_negative_direction >= 0.0).all()


def test_parameter_perturbation_scale_zero_means_zero_trading():
    """scale=0.0 -> every regime's allocation is 0% -> the strategy never
    buys anything, so CAGR should be ~0 (net of the fact no trade even
    happens) and n_trades should be 0."""
    df = _multi_cycle_df()
    table = parameter_perturbation(df, scale_factors=(0.0, 1.0))
    zero_row = table[table["scale_factor"] == 0.0].iloc[0]
    assert zero_row["n_trades"] == 0
    assert zero_row["cagr"] == pytest.approx(0.0, abs=1e-6)


def test_parameter_perturbation_returns_one_row_per_scale_factor():
    df = _multi_cycle_df()
    factors = (0.5, 1.0, 1.5)
    table = parameter_perturbation(df, scale_factors=factors)
    assert len(table) == len(factors)
    assert set(table["scale_factor"]) == set(factors)


# ---------------------------------------------------------------------
# Execution model comparison
# ---------------------------------------------------------------------

def test_execution_model_comparison_returns_both_models():
    df = _multi_cycle_df()
    df["alloc"] = 0.5
    table = execution_model_comparison(df, allocation_col="alloc")
    assert set(table["execution_model"]) == {"next_open", "same_close"}


def test_execution_model_comparison_differs_when_open_and_close_diverge():
    """A dataset with a large, consistent gap between close and next
    open should show NEXT_OPEN and SAME_CLOSE producing different
    results -- if they were identical, the execution model parameter
    wouldn't be doing anything."""
    n = 100
    dates = pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC")
    close = np.full(n, 100.0)
    open_ = np.full(n, 150.0)  # big, consistent gap
    df = pd.DataFrame({"timestamp": dates, "open": open_, "close": close, "alloc": [1.0] * n})

    table = execution_model_comparison(df, allocation_col="alloc")
    next_open_cagr = table[table["execution_model"] == "next_open"]["cagr"].iloc[0]
    same_close_cagr = table[table["execution_model"] == "same_close"]["cagr"].iloc[0]
    assert next_open_cagr != pytest.approx(same_close_cagr, rel=1e-6)


# ---------------------------------------------------------------------
# Per-cycle breakdown
# ---------------------------------------------------------------------

def test_per_cycle_metrics_finds_multiple_segments():
    df = _multi_cycle_df()
    df["alloc"] = scaled_cycle_allocation(df, scale=1.0)
    table = per_cycle_metrics(df, allocation_col="alloc")
    assert len(table) >= 2  # two engineered bull/bear cycles should yield at least 2 segments


def test_per_cycle_metrics_segments_are_chronologically_ordered():
    df = _multi_cycle_df()
    df["alloc"] = scaled_cycle_allocation(df, scale=1.0)
    table = per_cycle_metrics(df, allocation_col="alloc")
    starts = table["cycle_start"].tolist()
    assert starts == sorted(starts)
