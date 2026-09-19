"""
Benchmark allocation series (RESEARCH_SPEC.md section 20).

- buy_and_hold_allocation: 100% BTC always. The trivial case pass 1 used
  to sanity-check the engine itself.
- cash_allocation: 0% BTC always. The other trivial case -- a strategy
  that can't beat sitting in cash isn't worth the complexity.
- simple_ma_trend_allocation: the classic trend-following baseline
  (close > sma_200 -> 100% BTC, else 0%) -- uses Milestone 4's existing
  sma_200 feature, no new causal computation needed. This is what
  RESEARCH_SPEC.md section 20 calls Benchmark 3.
- cycle_only_allocation: Milestone 8's core allocation (cycle.py) WITHOUT
  the swing/tactical overlay -- Benchmark 4, "cycle allocation only".
  Isolates whether the tactical layer is earning its complexity, per the
  project's own "ML must earn its place" principle applied to the swing
  engine instead.

The actual strategy under test (cycle + swing combined) is Milestone 8's
`total_allocation` column -- not reproduced here, since it already exists
in the labeled signal file.
"""

from __future__ import annotations

import pandas as pd

from src.strategies.cycle import add_core_allocation


def buy_and_hold_allocation(df: pd.DataFrame) -> pd.Series:
    """100% BTC from the first row onward -- a constant target of 1.0."""
    return pd.Series(1.0, index=df.index, name="buy_and_hold_allocation")


def cash_allocation(df: pd.DataFrame) -> pd.Series:
    """0% BTC always -- the other trivial baseline."""
    return pd.Series(0.0, index=df.index, name="cash_allocation")


def simple_ma_trend_allocation(df: pd.DataFrame, price_col: str = "close", sma_col: str = "sma_200") -> pd.Series:
    """100% BTC when price is above its 200-day SMA, else 0% -- the
    textbook trend-following benchmark. NaN where sma_200 itself is NaN
    (Milestone 4 warmup), not defaulted to either side."""
    signal = (df[price_col] > df[sma_col]).astype(float)
    return signal.where(df[sma_col].notna()).rename("simple_ma_trend_allocation")


def cycle_only_allocation(df: pd.DataFrame, regime_col: str = "regime") -> pd.Series:
    """Milestone 8's core allocation by regime, with no tactical overlay."""
    return add_core_allocation(df, regime_col=regime_col)["core_allocation"].rename("cycle_only_allocation")
