"""
Price/trend features: returns, moving-average distance, drawdown from
rolling all-time-high, run-up from rolling low. See RESEARCH_SPEC.md
section 4 for the feature family definition.
"""

from __future__ import annotations

import pandas as pd

from src.features.common import log_return, simple_return

SMA_WINDOWS = (20, 50, 100, 200)
RUNUP_WINDOWS = (30, 60, 90, 180, 365)


def add_price_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a copy of `df` with price/trend feature columns added. `df`
    must have a `close` column and be sorted ascending by timestamp.
    """
    out = df.copy()
    close = out["close"]

    out["return_1d"] = simple_return(close, 1)
    out["log_return_1d"] = log_return(close, 1)

    for w in SMA_WINDOWS:
        sma = close.rolling(w, min_periods=w).mean()
        out[f"sma_{w}"] = sma
        out[f"dist_from_sma_{w}"] = (close - sma) / sma

    # Drawdown from the running all-time high observed up to and
    # including row t (expanding, not full-series -- causal).
    running_ath = close.expanding(min_periods=1).max()
    out["drawdown_from_ath"] = (close - running_ath) / running_ath

    # Run-up from the rolling low over each lookback window.
    for w in RUNUP_WINDOWS:
        rolling_low = close.rolling(w, min_periods=w).min()
        out[f"runup_from_low_{w}d"] = (close - rolling_low) / rolling_low

    return out
