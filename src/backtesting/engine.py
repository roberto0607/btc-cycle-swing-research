"""
Backtest engine (RESEARCH_SPEC.md Phase 6). Ties execution.py,
portfolio.py, and costs.py together into a single day-by-day simulation.

TIMING, explicitly (this is the part most backtests get wrong by
accident, per section 18): a target allocation value in df[allocation_col]
at row t is information available BY THE CLOSE of day t (it was computed
from features/regime that only use data up to and including day t). Under
the default NEXT_OPEN execution model, that decision cannot fill until
day t+1's open -- the earliest real price at which a trade could occur.

Consequently:
    - portfolio value is recorded at each day's CLOSE (mark-to-market)
    - a trade decided from day t's target fills at day t+1's OPEN
    - day 0 has no prior decision to act on, so it starts and stays in
      cash until the first fill on day 1

A NaN target_allocation (Milestone 4/8's feature warmup period) is
treated as "no new decision yet" -- the engine holds whatever target was
last known (or stays in cash if none yet), rather than inventing a 0 or
forward-filling blindly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from src.backtesting.costs import CostModel
from src.backtesting.execution import DEFAULT_EXECUTION_MODEL, ExecutionModel
from src.backtesting.portfolio import Portfolio


@dataclass
class BacktestResult:
    portfolio_values: list[float] = field(default_factory=list)
    timestamps: list[object] = field(default_factory=list)
    portfolio: Portfolio | None = None

    def to_series(self) -> pd.Series:
        return pd.Series(self.portfolio_values, index=pd.Index(self.timestamps, name="timestamp"), name="portfolio_value")


def run_backtest(
    df: pd.DataFrame,
    allocation_col: str,
    costs: CostModel,
    initial_capital: float = 10_000.0,
    execution_model: ExecutionModel = DEFAULT_EXECUTION_MODEL,
    price_col: str = "close",
    open_col: str = "open",
    timestamp_col: str = "timestamp",
) -> BacktestResult:
    if execution_model != ExecutionModel.NEXT_OPEN:
        # SAME_CLOSE is supported for explicit, labeled comparison only
        # (execution.py docstring) -- implemented as a straight
        # same-day-close fill, one line different from the main loop.
        return _run_same_close(df, allocation_col, costs, initial_capital, price_col, timestamp_col)

    portfolio = Portfolio(cash=initial_capital)
    result = BacktestResult(portfolio=portfolio)

    pending_target: float | None = None
    n = len(df)

    for t in range(n):
        open_price = df[open_col].iloc[t]
        close_price = df[price_col].iloc[t]
        timestamp = df[timestamp_col].iloc[t]

        # Fill any pending decision from yesterday at TODAY's open.
        if pending_target is not None and pd.notna(open_price):
            portfolio.rebalance_to_target(pending_target, open_price, costs, timestamp=timestamp)

        # Mark to market at today's close.
        value = portfolio.total_value(close_price) if pd.notna(close_price) else portfolio.cash
        result.portfolio_values.append(value)
        result.timestamps.append(timestamp)

        # Today's target becomes tomorrow's pending decision.
        today_target = df[allocation_col].iloc[t]
        if pd.notna(today_target):
            pending_target = today_target
        # else: NaN -> keep whatever pending_target already was (hold last known decision)

    return result


def _run_same_close(
    df: pd.DataFrame,
    allocation_col: str,
    costs: CostModel,
    initial_capital: float,
    price_col: str,
    timestamp_col: str,
) -> BacktestResult:
    """UNREALISTIC comparison-only path -- see execution.py docstring."""
    portfolio = Portfolio(cash=initial_capital)
    result = BacktestResult(portfolio=portfolio)

    for t in range(len(df)):
        close_price = df[price_col].iloc[t]
        timestamp = df[timestamp_col].iloc[t]
        target = df[allocation_col].iloc[t]

        if pd.notna(target) and pd.notna(close_price):
            portfolio.rebalance_to_target(target, close_price, costs, timestamp=timestamp)

        value = portfolio.total_value(close_price) if pd.notna(close_price) else portfolio.cash
        result.portfolio_values.append(value)
        result.timestamps.append(timestamp)

    return result
