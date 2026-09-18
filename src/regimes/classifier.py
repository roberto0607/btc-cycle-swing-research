"""
Applies the rule table from definitions.py to a feature DataFrame,
producing a `regime` column. Vectorized with numpy.select for an
exhaustive, deterministic, priority-ordered classification -- every row
with complete inputs gets exactly one label; every row with any required
input missing (warmup period) gets None.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.regimes.definitions import (
    BEAR_MAX_DRAWDOWN,
    LATE_BULL_MAX_DRAWDOWN,
    LATE_BULL_RSI_THRESHOLD,
    REQUIRED_COLUMNS,
)


def classify_regime(df: pd.DataFrame) -> pd.DataFrame:
    """Returns a copy of `df` with a `regime` column added."""
    out = df.copy()

    close, sma_50, sma_200 = out["close"], out["sma_50"], out["sma_200"]
    drawdown, rsi_14 = out["drawdown_from_ath"], out["rsi_14"]

    has_inputs = out[REQUIRED_COLUMNS].notnull().all(axis=1)

    above_50 = close > sma_50
    above_200 = close > sma_200

    is_late_bull = (
        above_50 & above_200 & (rsi_14 >= LATE_BULL_RSI_THRESHOLD) & (drawdown >= LATE_BULL_MAX_DRAWDOWN)
    )
    is_bull = above_50 & above_200 & ~is_late_bull
    is_distribution = ~above_50 & above_200
    is_bear = ~above_50 & ~above_200 & (drawdown <= BEAR_MAX_DRAWDOWN)
    is_recovery = above_50 & ~above_200
    is_accumulation = ~above_50 & ~above_200 & (drawdown > BEAR_MAX_DRAWDOWN)

    conditions = [is_late_bull, is_bull, is_distribution, is_bear, is_recovery, is_accumulation]
    choices = ["LATE_BULL", "BULL", "DISTRIBUTION", "BEAR", "RECOVERY", "ACCUMULATION"]

    regime = np.select(conditions, choices, default=None)
    regime = pd.Series(regime, index=out.index).where(has_inputs, None)

    out["regime"] = regime
    return out
