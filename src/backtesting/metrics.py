"""
Performance metrics from a portfolio value series (RESEARCH_SPEC.md
section 21). Only the core set for this first pass (return, risk,
risk-adjusted, trade count) -- the full metric list (Sortino, Calmar,
turnover, BTC-specific exposure stats) is Milestone 9's second pass, once
this engine is verified against the buy-and-hold sanity check.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 365


def compute_metrics(portfolio_values: pd.Series, n_trades: int) -> dict:
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

    return {
        "start_value": values.iloc[0],
        "end_value": values.iloc[-1],
        "n_days": n_days,
        "n_years": round(n_years, 2),
        "total_return": total_return,
        "cagr": cagr,
        "annualized_volatility": ann_vol,
        "max_drawdown": max_drawdown,
        "sharpe": sharpe,
        "n_trades": n_trades,
    }
