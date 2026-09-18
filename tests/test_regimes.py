"""
Tests for Milestone 6: regime classification and Phase 3 analysis.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.regimes.analysis import (
    forward_min_return_for_research,
    regime_conditional_stats,
    regime_segment_stats,
    regime_transition_matrix,
)
from src.regimes.classifier import classify_regime


def _row(close, sma_50, sma_200, drawdown, rsi_14):
    return {
        "close": close,
        "sma_50": sma_50,
        "sma_200": sma_200,
        "drawdown_from_ath": drawdown,
        "rsi_14": rsi_14,
    }


def _base_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.date_range("2024-01-01", periods=len(df), freq="D", tz="UTC")
    return df


# ---------------------------------------------------------------------
# Classifier: one test per rule branch
# ---------------------------------------------------------------------

def test_classify_late_bull():
    df = _base_df([_row(close=100, sma_50=90, sma_200=80, drawdown=-0.05, rsi_14=80)])
    out = classify_regime(df)
    assert out["regime"].iloc[0] == "LATE_BULL"


def test_classify_bull_not_late():
    # above both SMAs, low drawdown, but RSI below the late-bull threshold
    df = _base_df([_row(close=100, sma_50=90, sma_200=80, drawdown=-0.05, rsi_14=60)])
    out = classify_regime(df)
    assert out["regime"].iloc[0] == "BULL"


def test_classify_bull_not_late_due_to_deep_drawdown():
    # above both SMAs, high RSI, but drawdown too deep for LATE_BULL
    df = _base_df([_row(close=100, sma_50=90, sma_200=80, drawdown=-0.25, rsi_14=80)])
    out = classify_regime(df)
    assert out["regime"].iloc[0] == "BULL"


def test_classify_distribution():
    # below sma_50 but still above sma_200
    df = _base_df([_row(close=100, sma_50=105, sma_200=80, drawdown=-0.10, rsi_14=50)])
    out = classify_regime(df)
    assert out["regime"].iloc[0] == "DISTRIBUTION"


def test_classify_bear():
    # below both SMAs and deep drawdown
    df = _base_df([_row(close=50, sma_50=60, sma_200=80, drawdown=-0.50, rsi_14=30)])
    out = classify_regime(df)
    assert out["regime"].iloc[0] == "BEAR"


def test_classify_early_recovery():
    # above sma_50 but still below sma_200, AND still deep underwater
    df = _base_df([_row(close=70, sma_50=65, sma_200=80, drawdown=-0.60, rsi_14=55)])
    out = classify_regime(df)
    assert out["regime"].iloc[0] == "EARLY_RECOVERY"


def test_classify_late_recovery():
    # above sma_50 but still below sma_200, but drawdown has shrunk past the -50% cutoff
    df = _base_df([_row(close=70, sma_50=65, sma_200=80, drawdown=-0.30, rsi_14=55)])
    out = classify_regime(df)
    assert out["regime"].iloc[0] == "LATE_RECOVERY"


def test_classify_accumulation():
    # below both SMAs, but drawdown not deep enough for BEAR
    df = _base_df([_row(close=70, sma_50=75, sma_200=90, drawdown=-0.20, rsi_14=45)])
    out = classify_regime(df)
    assert out["regime"].iloc[0] == "ACCUMULATION"


def test_classify_exhaustive_no_nulls_when_inputs_complete():
    """Every combination of above/below SMA and drawdown depth must land
    in exactly one regime -- no row with complete inputs should end up
    unclassified."""
    rng = np.random.default_rng(0)
    n = 2000
    df = pd.DataFrame(
        {
            "close": rng.uniform(50, 150, n),
            "sma_50": rng.uniform(50, 150, n),
            "sma_200": rng.uniform(50, 150, n),
            "drawdown_from_ath": rng.uniform(-0.9, 0, n),
            "rsi_14": rng.uniform(0, 100, n),
        }
    )
    out = classify_regime(df)
    assert out["regime"].notnull().all()
    assert set(out["regime"].unique()) <= {
        "BEAR", "ACCUMULATION", "EARLY_RECOVERY", "LATE_RECOVERY", "BULL", "LATE_BULL", "DISTRIBUTION"
    }


def test_classify_null_when_inputs_missing():
    df = _base_df([_row(close=100, sma_50=np.nan, sma_200=80, drawdown=-0.05, rsi_14=80)])
    out = classify_regime(df)
    assert pd.isna(out["regime"].iloc[0])


# ---------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------

def test_forward_min_return_for_research_hand_computed():
    closes = pd.Series([100.0, 90.0, 80.0, 120.0, 110.0])
    fwd = forward_min_return_for_research(closes, horizon=2)
    # At t=0: min(close[1], close[2]) = min(90,80) = 80 -> 80/100 - 1 = -0.20
    assert fwd.iloc[0] == pytest.approx(-0.20, rel=1e-6)
    # At t=1: min(close[2], close[3]) = min(80,120) = 80 -> 80/90 - 1
    assert fwd.iloc[1] == pytest.approx(80 / 90 - 1, rel=1e-6)


def test_regime_segment_stats_counts_contiguous_runs():
    regimes = ["BULL"] * 5 + ["BEAR"] * 3 + ["BULL"] * 2
    df = _base_df([_row(100, 90, 80, -0.05, 60)] * len(regimes))
    df["regime"] = regimes

    stats = regime_segment_stats(df)
    bull_row = stats[stats["regime"] == "BULL"].iloc[0]
    bear_row = stats[stats["regime"] == "BEAR"].iloc[0]

    assert bull_row["n_segments"] == 2
    assert bull_row["total_days"] == 7
    assert bear_row["n_segments"] == 1
    assert bear_row["total_days"] == 3


def test_regime_transition_matrix_rows_sum_to_one():
    regimes = ["BULL"] * 5 + ["BEAR"] * 3 + ["ACCUMULATION"] * 4
    df = _base_df([_row(100, 90, 80, -0.05, 60)] * len(regimes))
    df["regime"] = regimes

    matrix = regime_transition_matrix(df)
    row_sums = matrix.sum(axis=1)
    for regime, total in row_sums.items():
        if total > 0:  # regimes that never occurred as "from" have an all-zero row
            assert total == pytest.approx(1.0, rel=1e-6)


def test_regime_conditional_stats_includes_all_baseline_and_regime_rows():
    n = 400
    rng = np.random.default_rng(1)
    df = pd.DataFrame(
        {
            "close": 100 * np.cumprod(1 + rng.normal(0, 0.01, n)),
            "timestamp": pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC"),
            "regime": rng.choice(["BULL", "BEAR"], size=n),
        }
    )
    stats = regime_conditional_stats(df, horizon=14)
    assert "ALL" in stats["regime"].values
    assert set(stats["regime"]) >= {"ALL", "BULL", "BEAR"}
    # n for ALL should equal the sum of n for the regime-specific rows
    all_n = stats.loc[stats["regime"] == "ALL", "n"].iloc[0]
    regime_n_sum = stats.loc[stats["regime"] != "ALL", "n"].sum()
    assert all_n == regime_n_sum


def test_early_vs_late_recovery_split_separates_designed_risk_difference():
    """
    Validates the mechanism behind the EARLY/LATE_RECOVERY split (not a
    live-data claim): construct a series where deep-drawdown ("early")
    bounces are, by design, more likely to roll over into a further
    decline than shallow-drawdown ("late") bounces, and confirm
    classify_regime + regime_conditional_stats actually reflects that
    difference -- i.e. the split doesn't just rename RECOVERY, it
    genuinely separates rows with different forward outcomes.
    """
    rng = np.random.default_rng(5)
    n = 600
    dates = pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC")

    # Half the series: deep drawdown ("early") bounces that mostly fail.
    # Half: shallow drawdown ("late") bounces that mostly hold.
    is_early = np.arange(n) < n // 2
    drawdown = np.where(is_early, rng.uniform(-0.80, -0.55, n), rng.uniform(-0.45, -0.20, n))

    # Forward drift designed to differ: early bounces drift down, late ones up.
    drift = np.where(is_early, -0.002, 0.002)
    close = 100 * np.cumprod(1 + drift + rng.normal(0, 0.01, n))

    df = pd.DataFrame(
        {
            "timestamp": dates,
            "close": close,
            "sma_50": close * 0.95,  # keep close > sma_50 throughout (recovery zone)
            "sma_200": close * 1.5,  # keep close < sma_200 throughout (recovery zone)
            "drawdown_from_ath": drawdown,
            "rsi_14": 50.0,
        }
    )
    classified = classify_regime(df)
    assert set(classified["regime"].dropna().unique()) <= {"EARLY_RECOVERY", "LATE_RECOVERY"}

    stats = regime_conditional_stats(classified, horizon=30)
    early_row = stats[stats["regime"] == "EARLY_RECOVERY"]
    late_row = stats[stats["regime"] == "LATE_RECOVERY"]
    assert not early_row.empty and not late_row.empty
    assert early_row["mean_forward_return"].iloc[0] < late_row["mean_forward_return"].iloc[0]
