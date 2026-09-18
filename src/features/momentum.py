"""
Momentum features: RSI at multiple lookbacks, and N-day returns/rate of
change. See RESEARCH_SPEC.md section 4.

RSI note: uses Wilder's original simple-moving-average formulation of
average gain/loss (not the exponential smoothing variant) for
transparency -- an explicit, documented choice per the project's
methodology rule against silently changing assumptions. If a different
RSI variant turns out to matter for a specific research question later,
that's a deliberate follow-up experiment, not a silent swap here.
"""

from __future__ import annotations

import pandas as pd

from src.features.common import simple_return

RSI_WINDOWS = (7, 14, 21)
RETURN_WINDOWS = (1, 3, 7, 14, 30, 60, 90)


def _rsi(close: pd.Series, window: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window, min_periods=window).mean()
    avg_loss = loss.rolling(window, min_periods=window).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # Edge cases avg_loss==0 can't resolve through the rs=avg_gain/avg_loss
    # division alone:
    #   - all gains, zero losses  -> genuinely maximal momentum -> RSI = 100
    #   - zero gains AND zero losses (price didn't move at all) -> there is
    #     no momentum to measure either way -> neutral RSI = 50, not 100.
    # Order matters: apply the flat case first, then the all-gains case, so
    # the more specific flat condition doesn't get overwritten.
    rsi = rsi.where(~((avg_gain == 0) & (avg_loss == 0)), 50.0)
    rsi = rsi.where(~((avg_gain > 0) & (avg_loss == 0)), 100.0)
    return rsi


def add_momentum_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    close = out["close"]

    for w in RSI_WINDOWS:
        out[f"rsi_{w}"] = _rsi(close, w)

    for w in RETURN_WINDOWS:
        out[f"return_{w}d"] = simple_return(close, w)

    return out
