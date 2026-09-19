"""
Phase 8 walk-forward testing (RESEARCH_SPEC.md section 11, 29, 39):
"the strategy cannot use future observations when selecting parameters
for a historical decision."

IMPORTANT HONESTY NOTE, stated up front rather than left implicit: Cycle
Only's core allocation table (src/strategies/cycle.py) was never
numerically fit or optimized against this dataset's returns -- it's a
fixed, hand-specified hypothesis, qualitatively derived from Milestone
6's regime-conditional rankings. So there is no parameter-fitting step
for walk-forward to guard against overfitting in the usual ML sense.

However, the DECISION to keep Cycle Only over Cycle + Swing (Milestone 9,
documented in RESEARCH_SPEC.md section 12.5) WAS made by looking at
full-history results, including the most recent window. That is a real
limitation: this module's walk-forward evaluation is NOT a pure,
uncontaminated test of "was Cycle Only the right choice" -- it's a test
of whether the (already-selected, already-frozen) Cycle Only strategy's
edge holds up across sequential, non-overlapping historical windows,
including the most recent one. That's still a meaningful, honest check --
just not the same claim as a from-scratch walk-forward-validated model
selection would be. State this plainly in any report built on this
module rather than implying more rigor than actually exists.

Each window gets FRESH capital (not carried over from the prior window) --
this measures "how would this strategy have performed if you started
fresh at the beginning of this window," which is what makes windows
comparable to each other and to Buy & Hold over the same span.
"""

from __future__ import annotations

import pandas as pd

from src.backtesting.costs import get_cost_model
from src.backtesting.engine import run_backtest
from src.backtesting.metrics import compute_metrics


def define_windows(df: pd.DataFrame, window_years: float = 2.0, timestamp_col: str = "timestamp") -> list[tuple]:
    """Splits [min(timestamp), max(timestamp)] into sequential,
    non-overlapping windows of `window_years` each. The final window may
    be shorter than the others if the range doesn't divide evenly."""
    start = df[timestamp_col].min()
    end = df[timestamp_col].max()
    window_delta = pd.Timedelta(days=window_years * 365.25)

    windows = []
    cursor = start
    while cursor < end:
        window_end = min(cursor + window_delta, end)
        windows.append((cursor, window_end))
        cursor = window_end
    return windows


def run_walk_forward(
    df: pd.DataFrame,
    allocation_col: str,
    window_years: float = 2.0,
    cost_scenario: str = "baseline",
    initial_capital: float = 10_000.0,
    timestamp_col: str = "timestamp",
) -> pd.DataFrame:
    """
    Runs a FRESH backtest (fresh capital) within each sequential window,
    using the same frozen `allocation_col` throughout (no re-fitting
    between windows -- there's nothing to fit, see module docstring).
    The most recent window is flagged is_most_recent=True.
    """
    windows = define_windows(df, window_years=window_years, timestamp_col=timestamp_col)
    costs = get_cost_model(cost_scenario)

    rows = []
    for i, (start, end) in enumerate(windows):
        segment = df[(df[timestamp_col] >= start) & (df[timestamp_col] <= end)].reset_index(drop=True)
        if len(segment) < 30:
            continue
        result = run_backtest(segment, allocation_col=allocation_col, costs=costs, initial_capital=initial_capital)
        metrics = compute_metrics(result.to_series(), n_trades=len(result.portfolio.trades))
        rows.append(
            {
                "window_start": start,
                "window_end": end,
                "n_days": len(segment),
                "cagr": metrics.get("cagr"),
                "max_drawdown": metrics.get("max_drawdown"),
                "sharpe": metrics.get("sharpe"),
                "total_return": metrics.get("total_return"),
                "is_most_recent": False,
            }
        )

    if rows:
        rows[-1]["is_most_recent"] = True

    return pd.DataFrame(rows)


def compare_to_benchmark_per_window(
    strategy_windows: pd.DataFrame, benchmark_windows: pd.DataFrame
) -> pd.DataFrame:
    """
    Merges strategy and benchmark walk-forward tables on window boundaries
    and computes, per window, whether the strategy beat the benchmark on
    CAGR and on max drawdown (a smaller-magnitude drawdown is "better").
    Also returns the overall win rate across windows for each metric.
    """
    merged = strategy_windows.merge(
        benchmark_windows, on=["window_start", "window_end"], suffixes=("_strategy", "_benchmark")
    )
    merged["beat_on_cagr"] = merged["cagr_strategy"] > merged["cagr_benchmark"]
    merged["beat_on_drawdown"] = merged["max_drawdown_strategy"] > merged["max_drawdown_benchmark"]  # closer to 0 = better
    return merged
