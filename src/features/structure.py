"""
Market structure features: distance from recent swing high/low, and a
simple breakout-state flag. See RESEARCH_SPEC.md section 4.

FIRST-PASS DEFINITION, explicitly flagged as such: "swing high/low" here
means the rolling max/min of `high`/`low` over a fixed lookback window,
and "breakout" means today's close cleared the prior (not including
today) rolling extreme. This is a reasonable, fully causal starting
definition -- not a claim that it's the right one. Like the regime labels
in src/regimes/, whether this particular definition of structure carries
useful information is a Phase 2+ research question, not an assumption to
build on unquestioned.
"""

from __future__ import annotations

import pandas as pd

SWING_WINDOW = 20


def add_structure_features(df: pd.DataFrame, window: int = SWING_WINDOW) -> pd.DataFrame:
    out = df.copy()
    close, high, low = out["close"], out["high"], out["low"]

    # Rolling swing high/low INCLUDING today, for "distance from swing
    # extreme" -- causal, uses only data up to and including t.
    swing_high = high.rolling(window, min_periods=window).max()
    swing_low = low.rolling(window, min_periods=window).min()
    out[f"dist_from_swing_high_{window}d"] = (close - swing_high) / swing_high
    out[f"dist_from_swing_low_{window}d"] = (close - swing_low) / swing_low

    # Breakout flags compare today's close against the swing extreme of
    # the PRIOR `window` days (shift(1) before rolling, so today is
    # excluded from its own reference range) -- still causal, just a
    # stricter "did today clear yesterday's range" definition.
    prior_high = high.shift(1).rolling(window, min_periods=window).max()
    prior_low = low.shift(1).rolling(window, min_periods=window).min()
    out[f"breakout_up_{window}d"] = close > prior_high
    out[f"breakout_down_{window}d"] = close < prior_low

    return out
