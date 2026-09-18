"""
Tests for Milestone 4 feature engineering.

Two kinds of test here matter differently:
- Correctness tests check a feature's value against a hand-computed
  expectation on a tiny synthetic series.
- Leakage tests (test_*_is_causal / test_no_lookahead_bias) check that no
  feature's value at row t changes when rows AFTER t are altered or
  removed. This is the single most important property in the project
  (master spec Section 3) and gets a dedicated, general-purpose test
  rather than relying on each feature's own correctness test to catch it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.features.momentum import add_momentum_features
from src.features.pipeline import build_features
from src.features.price import add_price_features
from src.features.structure import add_structure_features
from src.features.volatility import add_volatility_features
from src.features.volume import add_volume_features


def _synthetic_ohlcv(n: int = 400, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2023-01-01", periods=n, freq="D", tz="UTC")
    close = 40000 + np.cumsum(rng.normal(0, 200, size=n))
    high = close + rng.uniform(50, 300, size=n)
    low = close - rng.uniform(50, 300, size=n)
    open_ = close + rng.normal(0, 50, size=n)
    volume = rng.uniform(500, 2000, size=n)
    return pd.DataFrame(
        {
            "timestamp": dates,
            "source": "test",
            "symbol": "BTC-USD",
            "timeframe": "1d",
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


# ---------------------------------------------------------------------
# Correctness
# ---------------------------------------------------------------------

def test_price_features_return_and_sma_hand_computed():
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=5, freq="D", tz="UTC"),
            "close": [100.0, 110.0, 121.0, 108.9, 119.79],
        }
    )
    out = add_price_features(df)

    assert out["return_1d"].iloc[1] == pytest.approx(0.10, rel=1e-6)
    assert out["return_1d"].iloc[2] == pytest.approx(0.10, rel=1e-6)

    # SMA20 requires 20 observations -- with only 5 rows, all NaN.
    assert out["sma_20"].isnull().all()


def test_rsi_is_100_for_straight_up_move():
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=20, freq="D", tz="UTC"),
            "close": np.arange(100, 120, dtype=float),  # strictly increasing
        }
    )
    out = add_momentum_features(df)
    # Every gain, no losses -> avg_loss is 0 -> RSI defined as 100.
    assert out["rsi_14"].iloc[-1] == pytest.approx(100.0)


def test_rsi_is_neutral_for_flat_price():
    """
    Regression test: a completely flat price series has zero gains AND
    zero losses. An earlier version of _rsi conflated this with the
    "all gains, no losses" case and incorrectly reported RSI=100 for a
    market that isn't moving at all -- caught via a smoke test where
    synthetic data hit a clipping floor and went flat. RSI should be a
    neutral 50 here, not a maximal-momentum 100.
    """
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=20, freq="D", tz="UTC"),
            "close": np.full(20, 100.0),  # perfectly flat
        }
    )
    out = add_momentum_features(df)
    assert out["rsi_14"].iloc[-1] == pytest.approx(50.0)


def test_breakout_up_flags_new_high():
    n = 25
    close = np.full(n, 100.0)
    close[-1] = 200.0  # obvious breakout on the last day
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC"),
            "open": close,
            "high": close,
            "low": close,
            "close": close,
        }
    )
    out = add_structure_features(df, window=20)
    assert bool(out["breakout_up_20d"].iloc[-1]) is True
    assert bool(out["breakout_up_20d"].iloc[-2]) is False


def test_volume_ratio_hand_computed():
    n = 25
    volume = np.full(n, 100.0)
    volume[-1] = 300.0  # spike on the last day
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC"),
            "volume": volume,
        }
    )
    out = add_volume_features(df)
    # The 20-day MA is inclusive of today (rolling windows include the
    # current row), so it's (19*100 + 300) / 20 = 110, not a flat 100.
    expected_ratio = 300.0 / 110.0
    assert out["volume_ratio_20"].iloc[-1] == pytest.approx(expected_ratio, rel=1e-6)


# ---------------------------------------------------------------------
# No-look-ahead-bias (leakage) regression tests
# ---------------------------------------------------------------------

def test_full_pipeline_is_causal_under_truncation():
    """
    The core leakage test: build features on the full series, then build
    features again on a truncated prefix of the same series. Every row
    that exists in both outputs must have IDENTICAL feature values. If any
    feature secretly used future data, truncating the future would change
    a past row's value.
    """
    df = _synthetic_ohlcv(n=400)
    full = build_features(df)

    truncate_at = 350
    truncated = build_features(df.iloc[:truncate_at].reset_index(drop=True))

    numeric_cols = [
        c for c in truncated.columns
        if pd.api.types.is_numeric_dtype(truncated[c]) and c not in ("open", "high", "low", "close", "volume")
    ]

    overlap_full = full.iloc[:truncate_at].reset_index(drop=True)
    for col in numeric_cols:
        pd.testing.assert_series_equal(
            overlap_full[col], truncated[col], check_names=False, obj=f"column {col}"
        )


def test_full_pipeline_is_causal_under_future_value_change():
    """
    Complementary leakage test: change a value far in the FUTURE relative
    to an early row, and confirm the early row's features are byte-for-byte
    unchanged. Catches leakage that truncation alone might miss (e.g. a
    global normalization step fit across the whole series).
    """
    df = _synthetic_ohlcv(n=400)
    features_a = build_features(df)

    df_mutated = df.copy()
    df_mutated.loc[399, "close"] *= 5.0  # wildly different last-day close

    features_b = build_features(df_mutated)

    check_through = 300  # well before the mutated row, clear of any
                          # rolling window used in this module (max window 365,
                          # but the mutation is 99 rows after this point, and
                          # every feature here only looks BACKWARD, so nothing
                          # before row 300 can see row 399 regardless of window)
    numeric_cols = [
        c for c in features_a.columns
        if pd.api.types.is_numeric_dtype(features_a[c]) and c not in ("open", "high", "low", "close", "volume")
    ]
    for col in numeric_cols:
        pd.testing.assert_series_equal(
            features_a[col].iloc[:check_through],
            features_b[col].iloc[:check_through],
            check_names=False,
            obj=f"column {col}",
        )


def test_volatility_features_dont_leak_across_truncation():
    """Same idea as the pipeline-level test, scoped to volatility alone,
    since ATR/realized-vol/Bollinger are the features most likely to
    accidentally reference a centered or global window."""
    df = _synthetic_ohlcv(n=400)
    full = add_volatility_features(df)
    truncated = add_volatility_features(df.iloc[:350].reset_index(drop=True))

    for col in ["atr_14", "atr_pct_14", "realized_vol_14d", "bollinger_width_20"]:
        pd.testing.assert_series_equal(
            full[col].iloc[:350].reset_index(drop=True),
            truncated[col],
            check_names=False,
            obj=f"column {col}",
        )
