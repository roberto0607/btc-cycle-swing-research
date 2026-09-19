"""
Phase 7 robustness testing (RESEARCH_SPEC.md Phase 7, "DESTROY THE
STRATEGY"), scoped to Cycle Only -- the strategy that survived Milestone
9's backtest comparison (see RESEARCH_SPEC.md section 12.5).

Three checks:
1. Parameter perturbation: scale the entire CORE_ALLOCATION table by a
   range of factors and see whether performance holds up across a region
   (a plateau) or only works at the exact chosen values (an isolated
   peak) -- section 49's explicit instruction.
2. Execution degradation: compare the default NEXT_OPEN fill assumption
   against the unrealistic SAME_CLOSE one -- if the strategy only "works"
   under the lenient assumption, that's a red flag, not a footnote.
3. Per-cycle breakdown: performance measured independently within each
   major historical peak-to-peak cycle, so one spectacular period can't
   single-handedly carry the aggregate number (section 53, "do not allow
   one spectacular period to dominate the conclusion").

Cost-scenario robustness (optimistic/baseline/pessimistic/stress) is NOT
re-implemented here -- Milestone 9 pass 2's run_full_backtest.py already
covers it for every strategy including Cycle Only.
"""

from __future__ import annotations

import pandas as pd

from src.backtesting.costs import CostModel, get_cost_model
from src.backtesting.engine import run_backtest
from src.backtesting.execution import ExecutionModel
from src.backtesting.metrics import compute_metrics
from src.research.statistics.exploratory import find_drawdown_episodes
from src.strategies.cycle import CORE_ALLOCATION

SCALE_FACTORS = (0.5, 0.7, 0.85, 1.0, 1.15, 1.3, 1.5)


def scaled_cycle_allocation(df: pd.DataFrame, scale: float, regime_col: str = "regime") -> pd.Series:
    """Cycle Only's core allocation table, every regime's value scaled by
    `scale` and clipped to [0, 1]. scale=1.0 reproduces the original
    unperturbed allocation exactly."""
    scaled_table = {regime: min(max(alloc * scale, 0.0), 1.0) for regime, alloc in CORE_ALLOCATION.items()}

    def _lookup(regime):
        if regime is None or (isinstance(regime, float) and pd.isna(regime)):
            return float("nan")
        return scaled_table.get(regime, float("nan"))

    return df[regime_col].apply(_lookup)


def parameter_perturbation(
    df: pd.DataFrame, scale_factors: tuple[float, ...] = SCALE_FACTORS, cost_scenario: str = "baseline"
) -> pd.DataFrame:
    costs = get_cost_model(cost_scenario)
    rows = []
    for scale in scale_factors:
        df_run = df.copy()
        df_run["_alloc"] = scaled_cycle_allocation(df, scale)
        result = run_backtest(df_run, allocation_col="_alloc", costs=costs, initial_capital=10_000.0)
        metrics = compute_metrics(
            result.to_series(), n_trades=len(result.portfolio.trades), allocation_series=df_run["_alloc"]
        )
        rows.append({"scale_factor": scale, **{k: metrics.get(k) for k in ("cagr", "max_drawdown", "sharpe", "calmar", "n_trades")}})
    return pd.DataFrame(rows)


def execution_model_comparison(df: pd.DataFrame, allocation_col: str, cost_scenario: str = "baseline") -> pd.DataFrame:
    costs = get_cost_model(cost_scenario)
    rows = []
    for model in (ExecutionModel.NEXT_OPEN, ExecutionModel.SAME_CLOSE):
        result = run_backtest(df, allocation_col=allocation_col, costs=costs, initial_capital=10_000.0, execution_model=model)
        metrics = compute_metrics(result.to_series(), n_trades=len(result.portfolio.trades))
        rows.append({"execution_model": model.value, **{k: metrics.get(k) for k in ("cagr", "max_drawdown", "sharpe")}})
    return pd.DataFrame(rows)


def per_cycle_metrics(df: pd.DataFrame, allocation_col: str, cost_scenario: str = "baseline") -> pd.DataFrame:
    """
    Splits the series into peak-to-peak segments using Milestone 5's
    drawdown-episode detector (each episode's peak_date to the next
    episode's peak_date is one "cycle"), then runs a fresh backtest
    WITHIN each segment independently -- so a strategy that only looks
    good because of one giant bull run can't hide behind the aggregate.
    """
    episodes = find_drawdown_episodes(df)
    if len(episodes) < 2:
        return pd.DataFrame(columns=["cycle_start", "cycle_end", "n_days", "cagr", "max_drawdown", "sharpe"])

    peak_dates = [e.peak_date for e in episodes]
    boundaries = peak_dates + [df["timestamp"].iloc[-1]]

    costs = get_cost_model(cost_scenario)
    rows = []
    for i in range(len(boundaries) - 1):
        start, end = boundaries[i], boundaries[i + 1]
        segment = df[(df["timestamp"] >= start) & (df["timestamp"] <= end)].reset_index(drop=True)
        if len(segment) < 30:  # too short to mean anything
            continue
        result = run_backtest(segment, allocation_col=allocation_col, costs=costs, initial_capital=10_000.0)
        metrics = compute_metrics(result.to_series(), n_trades=len(result.portfolio.trades))
        if not metrics:
            continue
        rows.append(
            {
                "cycle_start": start,
                "cycle_end": end,
                "n_days": len(segment),
                "cagr": metrics.get("cagr"),
                "max_drawdown": metrics.get("max_drawdown"),
                "sharpe": metrics.get("sharpe"),
            }
        )
    return pd.DataFrame(rows)
