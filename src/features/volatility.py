"""
Volatility features: ATR/ATR%, realized volatility, volatility percentile,
Bollinger Band width. See RESEARCH_SPEC.md section 4.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.common import log_return, rolling_percentile_rank, true_range

ATR_WINDOW = 14
REALIZED_VOL_WINDOWS = (14, 30)
VOL_PERCENTILE_WINDOW = 365
BOLLINGER_WINDOW = 20
BOLLINGER_STD = 2


def add_volatility_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    close, high, low = out["close"], out["high"], out["low"]

    tr = true_range(high, low, close)
    atr = tr.rolling(ATR_WINDOW, min_periods=ATR_WINDOW).mean()
    out["atr_14"] = atr
    out["atr_pct_14"] = atr / close

    log_ret = log_return(close, 1)
    for w in REALIZED_VOL_WINDOWS:
        # Annualized realized volatility of daily log returns.
        out[f"realized_vol_{w}d"] = log_ret.rolling(w, min_periods=w).std() * np.sqrt(365)

    # Volatility percentile: where the shorter realized-vol window sits
    # within its own trailing-year distribution.
    out["vol_percentile_365d"] = rolling_percentile_rank(
        out[f"realized_vol_{REALIZED_VOL_WINDOWS[0]}d"], VOL_PERCENTILE_WINDOW
    )

    sma = close.rolling(BOLLINGER_WINDOW, min_periods=BOLLINGER_WINDOW).mean()
    std = close.rolling(BOLLINGER_WINDOW, min_periods=BOLLINGER_WINDOW).std()
    upper = sma + BOLLINGER_STD * std
    lower = sma - BOLLINGER_STD * std
    out["bollinger_width_20"] = (upper - lower) / sma

    return out
