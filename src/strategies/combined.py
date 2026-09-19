"""
Combines the cycle (core) and swing (tactical) engines into a single
total target allocation per day (RESEARCH_SPEC.md section 7, 52):

    total_allocation = core_allocation(regime) + tactical_allocation

Capped at 1.0 (100% BTC) as a sanity bound, though with the current
CORE_ALLOCATION (max 0.70) and TACTICAL_MAX (0.20) constants the sum
never actually approaches that cap.

This is a PORTFOLIO TARGET, not an executed trade -- Milestone 9
(backtester) is what turns a sequence of these targets into simulated
orders, fills, and realized performance under transaction costs.
"""

from __future__ import annotations

import pandas as pd

from src.strategies.cycle import add_core_allocation
from src.strategies.swing import run_swing_engine


def run_combined_strategy(df: pd.DataFrame, regime_col: str = "regime") -> pd.DataFrame:
    out = add_core_allocation(df, regime_col=regime_col)
    out = run_swing_engine(out, regime_col=regime_col)
    out["total_allocation"] = (out["core_allocation"] + out["tactical_allocation"]).clip(upper=1.0)
    return out
