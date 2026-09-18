"""
Shared helpers for feature engineering. Every function here is causal by
construction: a value at row t is computed only from rows <= t. This is
the single most important property in the whole project (master spec
Section 3, "NO LOOK-AHEAD BIAS") -- get it wrong here and every downstream
regime label, pullback probability, and backtest result is silently
invalid, so keep all "future-looking" logic (shift(-n), lookahead windows)
OUT of this module entirely.

Callers must pass a DataFrame already sorted ascending by timestamp (true
of everything written by src/data/ingestion/schema.write_raw).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def simple_return(close: pd.Series, n: int = 1) -> pd.Series:
    """n-period simple return: (close_t / close_{t-n}) - 1."""
    return close.pct_change(n)


def log_return(close: pd.Series, n: int = 1) -> pd.Series:
    """n-period log return: ln(close_t / close_{t-n})."""
    return np.log(close / close.shift(n))


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """
    Wilder's True Range: the largest of
        high - low
        abs(high - previous close)
        abs(low - previous close)
    Uses close.shift(1), i.e. yesterday's close -- causal.
    """
    prev_close = close.shift(1)
    ranges = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    )
    return ranges.max(axis=1)


def rolling_percentile_rank(series: pd.Series, window: int) -> pd.Series:
    """
    For each row t, the percentile rank (0-1) of series[t] within the
    trailing `window` observations ending at and including t. Causal:
    only uses data up to and including t.
    """
    return series.rolling(window, min_periods=window).apply(
        lambda x: (x <= x.iloc[-1]).sum() / len(x), raw=False
    )
