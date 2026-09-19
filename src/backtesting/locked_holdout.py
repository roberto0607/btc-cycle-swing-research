"""
Locked holdout test (RESEARCH_SPEC.md section 6 "Paper Validation" phase,
and the spirit of Phase 8's locked-test step).

HONESTY NOTE, same caveat as Milestone 11, restated because it matters
even more here: this is NOT a statistically clean, never-seen holdout.
Every day in this dataset -- including the days in this holdout window --
was part of the full-history data used to select Cycle Only over
Cycle + Swing (Milestone 9) and to design the regime rules (Milestone 6).
There is no slice of this dataset that was truly never looked at.

What THIS test actually provides is different from statistical purity:
it's a discipline commitment. The strategy configuration
(src/strategies/cycle.py's CORE_ALLOCATION table) is FROZEN as of this
test -- no further tuning, no threshold adjustments, no second-guessing
based on this result. Run once, report plainly, then either move to
paper trading or don't. That discipline is the actual value of a
"locked" test when a perfectly clean holdout isn't available: it
prevents the specific failure mode of re-running this check repeatedly
with small tweaks until it looks good (which would be indistinguishable
from overfitting to this window).
"""

from __future__ import annotations

import pandas as pd

from src.backtesting.costs import get_cost_model
from src.backtesting.engine import run_backtest
from src.backtesting.metrics import compute_metrics

DEFAULT_HOLDOUT_MONTHS = 6


def define_holdout(df: pd.DataFrame, months: int = DEFAULT_HOLDOUT_MONTHS, timestamp_col: str = "timestamp") -> tuple:
    """Returns (start, end) for the most recent `months` of the dataset."""
    end = df[timestamp_col].max()
    start = end - pd.Timedelta(days=months * 30.44)  # average month length
    start = max(start, df[timestamp_col].min())
    return start, end


def run_locked_holdout(
    df: pd.DataFrame,
    allocations: dict[str, pd.Series],
    months: int = DEFAULT_HOLDOUT_MONTHS,
    cost_scenario: str = "baseline",
    initial_capital: float = 10_000.0,
    timestamp_col: str = "timestamp",
) -> pd.DataFrame:
    """
    Runs every allocation series in `allocations` (name -> Series aligned
    to df's index) as a FRESH-capital backtest restricted to the holdout
    window only, under one cost scenario. One row per strategy.
    """
    start, end = define_holdout(df, months=months, timestamp_col=timestamp_col)
    mask = (df[timestamp_col] >= start) & (df[timestamp_col] <= end)
    holdout_df = df.loc[mask].reset_index(drop=True)
    costs = get_cost_model(cost_scenario)

    rows = []
    for name, alloc in allocations.items():
        segment = holdout_df.copy()
        segment["_alloc"] = alloc.loc[mask].reset_index(drop=True)
        result = run_backtest(segment, allocation_col="_alloc", costs=costs, initial_capital=initial_capital)
        metrics = compute_metrics(result.to_series(), n_trades=len(result.portfolio.trades))
        rows.append({"strategy": name, "holdout_start": start, "holdout_end": end, "n_days": len(segment), **metrics})

    return pd.DataFrame(rows)
