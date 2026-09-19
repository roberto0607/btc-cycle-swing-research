"""
Benchmark allocation series (RESEARCH_SPEC.md section 20). Only
buy-and-hold for this first pass -- it's the trivial, hand-verifiable
case used to sanity-check the engine itself. The other three benchmarks
(100% cash, simple MA trend, cycle-only) are Milestone 9's second pass.
"""

from __future__ import annotations

import pandas as pd


def buy_and_hold_allocation(df: pd.DataFrame) -> pd.Series:
    """100% BTC from the first row onward -- a constant target of 1.0."""
    return pd.Series(1.0, index=df.index, name="buy_and_hold_allocation")
