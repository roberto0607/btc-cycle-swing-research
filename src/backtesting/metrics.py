"""
Performance metrics from a portfolio value series (RESEARCH_SPEC.md
section 21). Pass 1 covered return/risk/risk-adjusted/trade count. Pass
2 adds: Sortino (downside-only risk-adjusted return), Calmar (return per
unit of max drawdown), average exposure (BTC-specific: how invested the
strategy was on average), and total fees paid.

Deliberately still NOT included: per-exit event analysis and explicit
upside-missed/downside-avoided accounting (RESEARCH_SPEC.md sections 21,
53-55) -- those need trade-by-trade attribution against a benchmark path,
which belongs with Phase 7's event-based analysis, not this comparison
table. Running buy-and-hold as one of the benchmarks in the same table
gives a first-order view of that tradeoff (strategy CAGR/drawdown next to
buy-and-hold's) without building the full event log yet.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 365


def compute_metrics(
    portfolio_values: pd.Series,
    n_trades: int,
    allocation_series: pd.Series | None = None,
    total_fees_paid: float = 0.0,
) -> dict:
    values = portfolio_values.dropna()
    if len(values) < 2:
        return {}

    returns = values.pct_change().dropna()
    n_days = len(values)
    n_years = n_days / TRADING_DAYS_PER_YEAR

    total_return = values.iloc[-1] / values.iloc[0] - 1
    cagr = (values.iloc[-1] / values.iloc[0]) ** (1 / n_years) - 1 if n_years > 0 else float("nan")
    ann_vol = returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)

    running_max = values.cummax()
    drawdown = (values - running_max) / running_max
    max_drawdown = drawdown.min()

    sharpe = (returns.mean() * TRADING_DAYS_PER_YEAR) / ann_vol if ann_vol > 0 else float("nan")

    downside_returns = returns[returns < 0]
    downside_dev = downside_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR) if len(downside_returns) > 0 else float("nan")
    sortino = (returns.mean() * TRADING_DAYS_PER_YEAR) / downside_dev if downside_dev and downside_dev > 0 else float("nan")

    calmar = cagr / abs(max_drawdown) if max_drawdown != 0 else float("nan")

    result = {
        "start_value": values.iloc[0],
        "end_value": values.iloc[-1],
        "n_days": n_days,
        "n_years": round(n_years, 2),
        "total_return": total_return,
        "cagr": cagr,
        "annualized_volatility": ann_vol,
        "max_drawdown": max_drawdown,
        "sharpe": sharpe,
        "sortino": sortino,
        "calmar": calmar,
        "n_trades": n_trades,
        "total_fees_paid": total_fees_paid,
    }

    if allocation_series is not None:
        alloc = allocation_series.dropna()
        result["avg_exposure"] = alloc.mean()
        result["pct_days_fully_out"] = (alloc <= 1e-9).mean()

    return result
