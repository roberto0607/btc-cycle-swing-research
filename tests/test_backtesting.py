"""
Tests for Milestone 9 (pass 1): portfolio accounting, execution timing,
and buy-and-hold engine sanity checks.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.backtesting.benchmarks import (
    buy_and_hold_allocation,
    cash_allocation,
    cycle_only_allocation,
    simple_ma_trend_allocation,
)
from src.backtesting.costs import CostModel, get_cost_model
from src.backtesting.engine import run_backtest
from src.backtesting.execution import ExecutionModel
from src.backtesting.metrics import compute_metrics
from src.backtesting.portfolio import Portfolio
from src.strategies.cycle import CORE_ALLOCATION

ZERO_COST = CostModel(fee_bps=0.0, spread_bps=0.0, slippage_bps=0.0)


# ---------------------------------------------------------------------
# Portfolio accounting
# ---------------------------------------------------------------------

def test_rebalance_zero_cost_buy_hand_computed():
    p = Portfolio(cash=10_000.0)
    p.rebalance_to_target(1.0, price=100.0, costs=ZERO_COST)
    assert p.cash == pytest.approx(0.0, abs=1e-6)
    assert p.btc == pytest.approx(100.0, rel=1e-9)  # 10000 / 100


def test_rebalance_applies_fee_on_buy():
    costs = CostModel(fee_bps=100.0, spread_bps=0.0, slippage_bps=0.0)  # 1% fee
    p = Portfolio(cash=10_000.0)
    p.rebalance_to_target(1.0, price=100.0, costs=costs)
    # 1% of 10000 = 100 fee; (10000-100)/100 = 99 BTC
    assert p.btc == pytest.approx(99.0, rel=1e-9)
    assert p.cash == pytest.approx(0.0, abs=1e-6)


def test_rebalance_applies_spread_and_slippage_on_buy():
    costs = CostModel(fee_bps=0.0, spread_bps=100.0, slippage_bps=0.0)  # 1% total impact
    p = Portfolio(cash=10_000.0)
    p.rebalance_to_target(1.0, price=100.0, costs=costs)
    # fill price = 100 * 1.01 = 101; btc = 10000/101
    assert p.btc == pytest.approx(10_000.0 / 101.0, rel=1e-9)


def test_rebalance_sell_reduces_btc_and_increases_cash():
    p = Portfolio(cash=0.0, btc=100.0)
    p.rebalance_to_target(0.5, price=100.0, costs=ZERO_COST)
    # value = 10000; target 50% = 5000 -> sell half the BTC
    assert p.btc == pytest.approx(50.0, rel=1e-9)
    assert p.cash == pytest.approx(5000.0, rel=1e-9)


def test_rebalance_no_op_when_already_at_target():
    p = Portfolio(cash=0.0, btc=100.0)
    p.rebalance_to_target(1.0, price=100.0, costs=ZERO_COST)  # already 100% BTC
    assert len(p.trades) == 0
    assert p.btc == pytest.approx(100.0)


def test_current_allocation_hand_computed():
    p = Portfolio(cash=5000.0, btc=50.0)  # 50 BTC at price 100 = 5000
    assert p.current_allocation(price=100.0) == pytest.approx(0.5, rel=1e-9)


# ---------------------------------------------------------------------
# Engine timing
# ---------------------------------------------------------------------

def test_engine_day_zero_has_no_trade_yet():
    """Under NEXT_OPEN, day 0 has no prior decision to fill -- portfolio
    must still be 100% cash at day 0's close."""
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=5, freq="D", tz="UTC"),
            "open": [100.0, 101.0, 102.0, 103.0, 104.0],
            "close": [100.5, 101.5, 102.5, 103.5, 104.5],
            "target": [1.0, 1.0, 1.0, 1.0, 1.0],
        }
    )
    result = run_backtest(df, allocation_col="target", costs=ZERO_COST, initial_capital=10_000.0)
    assert result.portfolio_values[0] == pytest.approx(10_000.0)  # still all cash


def test_engine_fills_at_next_open_not_same_close():
    """A decision known at day 0 (target=1.0) must fill at day 1's OPEN,
    not day 0's close -- the core no-look-ahead timing property."""
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=3, freq="D", tz="UTC"),
            "open": [100.0, 200.0, 300.0],  # day 1's open is 200, very different from day 0's close
            "close": [110.0, 210.0, 310.0],
            "target": [1.0, 1.0, 1.0],
        }
    )
    result = run_backtest(df, allocation_col="target", costs=ZERO_COST, initial_capital=10_000.0)
    # Fill happens at day 1's open (200), so btc = 10000/200 = 50
    assert result.portfolio.btc == pytest.approx(50.0, rel=1e-9)
    # Day 2's mark-to-market value = 50 * 310 = 15500
    assert result.portfolio_values[2] == pytest.approx(15_500.0, rel=1e-9)


def test_engine_holds_last_known_target_through_nan_rows():
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=4, freq="D", tz="UTC"),
            "open": [100.0, 100.0, 100.0, 100.0],
            "close": [100.0, 100.0, 100.0, 100.0],
            "target": [1.0, np.nan, np.nan, 1.0],
        }
    )
    result = run_backtest(df, allocation_col="target", costs=ZERO_COST, initial_capital=10_000.0)
    # Should have exactly one trade (the initial buy); NaN days don't
    # trigger a re-trade, and the repeated 1.0 at the end is a no-op
    # since we're already at target.
    assert len(result.portfolio.trades) == 1


def test_engine_never_trades_when_allocation_constant_and_unchanged():
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=10, freq="D", tz="UTC"),
            "open": [100.0] * 10,
            "close": [100.0] * 10,
            "target": [1.0] * 10,
        }
    )
    result = run_backtest(df, allocation_col="target", costs=ZERO_COST, initial_capital=10_000.0)
    assert len(result.portfolio.trades) == 1  # only the initial entry


def test_engine_does_not_retrade_on_price_drift_alone():
    """
    Regression test for a real bug caught only once this ran against
    real, moving prices (pass 1's flat-price tests masked it): a constant
    target allocation must produce exactly ONE trade even as price moves
    substantially day to day, since natural price-driven drift in the
    portfolio's actual BTC weight is not a new decision and must not
    trigger a re-trade every day to correct back to the unchanged target.
    """
    n = 200
    rng = np.random.default_rng(2)
    dates = pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC")
    close = 100 * np.cumprod(1 + rng.normal(0, 0.03, n))  # real day-to-day volatility
    open_ = close * (1 + rng.normal(0, 0.01, n))
    df = pd.DataFrame({"timestamp": dates, "open": open_, "close": close, "target": [0.7] * n})

    result = run_backtest(df, allocation_col="target", costs=get_cost_model("baseline"), initial_capital=10_000.0)
    assert len(result.portfolio.trades) == 1


# ---------------------------------------------------------------------
# Buy-and-hold cross-check against independent hand computation
# ---------------------------------------------------------------------

def test_buy_and_hold_matches_independent_hand_computation():
    """
    The actual sanity check this milestone exists to run, as a proper
    pytest test (not just the CLI script): build a realistic price path,
    run 100% buy-and-hold through the engine, and compare against a
    hand-computed expected value using a completely separate formula.
    """
    n = 200
    rng = np.random.default_rng(0)
    dates = pd.date_range("2020-01-01", periods=n, freq="D", tz="UTC")
    close = 100 * np.cumprod(1 + rng.normal(0, 0.02, n))
    open_ = close * (1 + rng.normal(0, 0.005, n))
    df = pd.DataFrame({"timestamp": dates, "open": open_, "close": close, "target": [1.0] * n})

    costs = get_cost_model("baseline")
    initial_capital = 10_000.0
    result = run_backtest(df, allocation_col="target", costs=costs, initial_capital=initial_capital)

    # Independent hand computation: single buy at day 1's open, held to the end.
    impact = costs.total_price_impact_bps / 10_000.0
    fill_price = df["open"].iloc[1] * (1 + impact)
    fee = initial_capital * (costs.fee_bps / 10_000.0)
    btc_bought = (initial_capital - fee) / fill_price
    expected_end_value = btc_bought * df["close"].iloc[-1]

    assert result.portfolio_values[-1] == pytest.approx(expected_end_value, rel=1e-9)
    assert len(result.portfolio.trades) == 1


def test_all_cost_scenarios_are_internally_consistent_ordering():
    """optimistic should always cost less than baseline < pessimistic <
    stress for the same trade -- a basic sanity check on the presets
    themselves, not just the engine."""
    scenarios = ["optimistic", "baseline", "pessimistic", "stress"]
    end_values = []
    for name in scenarios:
        costs = get_cost_model(name)
        p = Portfolio(cash=10_000.0)
        p.rebalance_to_target(1.0, price=100.0, costs=costs)
        end_values.append(p.total_value(100.0))
    # More expensive scenarios should leave less value immediately after the buy.
    assert end_values == sorted(end_values, reverse=True)


# ---------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------

def test_compute_metrics_hand_computed_total_return():
    values = pd.Series([100.0, 110.0, 121.0], index=pd.date_range("2024-01-01", periods=3, freq="D"))
    metrics = compute_metrics(values, n_trades=1)
    assert metrics["total_return"] == pytest.approx(0.21, rel=1e-6)


def test_compute_metrics_sortino_ignores_upside_volatility():
    """Two series with identical upside swings but one has zero downside
    days -- that one should have a much higher (or undefined-but-not-worse)
    Sortino than one with real downside volatility, even if their Sharpe
    ratios are similar."""
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    up_only = pd.Series([100, 105, 100, 106, 100, 107, 100, 108, 100, 109], index=dates, dtype=float)
    # up_only alternates but never actually goes below its start in a way
    # that creates negative returns every other day by construction below:
    mixed = pd.Series([100, 105, 95, 106, 94, 107, 93, 108, 92, 109], index=dates, dtype=float)

    m_up = compute_metrics(up_only, n_trades=1)
    m_mixed = compute_metrics(mixed, n_trades=1)
    # mixed has real negative-return days; up_only's down days are smaller
    # in magnitude relative to its up days than mixed's -- Sortino should
    # reflect mixed being riskier on the downside.
    assert m_mixed["sortino"] < m_up["sortino"]


def test_compute_metrics_calmar_hand_computed():
    # Straight-line 20% total gain, 10% max drawdown along the way.
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    values = pd.Series([100.0, 90.0, 100.0, 120.0], index=dates)  # dips to 90 (-10% from 100), ends at 120
    metrics = compute_metrics(values, n_trades=1)
    assert metrics["max_drawdown"] == pytest.approx(-0.10, rel=1e-6)
    assert metrics["calmar"] == pytest.approx(metrics["cagr"] / 0.10, rel=1e-6)


def test_compute_metrics_avg_exposure_and_fees():
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    values = pd.Series([100.0, 101.0, 102.0, 103.0], index=dates)
    alloc = pd.Series([1.0, 0.5, 0.0, 0.5], index=range(4))
    metrics = compute_metrics(values, n_trades=3, allocation_series=alloc, total_fees_paid=12.5)
    assert metrics["avg_exposure"] == pytest.approx(0.5, rel=1e-6)
    assert metrics["pct_days_fully_out"] == pytest.approx(0.25, rel=1e-6)
    assert metrics["total_fees_paid"] == pytest.approx(12.5)


# ---------------------------------------------------------------------
# Benchmarks (pass 2)
# ---------------------------------------------------------------------

def test_cash_allocation_is_always_zero():
    df = pd.DataFrame({"x": range(5)})
    alloc = cash_allocation(df)
    assert (alloc == 0.0).all()


def test_simple_ma_trend_allocation_hand_computed():
    df = pd.DataFrame(
        {
            "close": [100.0, 100.0, 100.0],
            "sma_200": [90.0, 110.0, float("nan")],
        }
    )
    alloc = simple_ma_trend_allocation(df)
    assert alloc.iloc[0] == 1.0  # close > sma_200
    assert alloc.iloc[1] == 0.0  # close < sma_200
    assert pd.isna(alloc.iloc[2])  # sma_200 itself unavailable


def test_cycle_only_allocation_matches_cycle_module():
    df = pd.DataFrame({"regime": ["BULL", "BEAR", "LATE_BULL"]})
    alloc = cycle_only_allocation(df)
    assert alloc.iloc[0] == CORE_ALLOCATION["BULL"]
    assert alloc.iloc[1] == CORE_ALLOCATION["BEAR"]
    assert alloc.iloc[2] == CORE_ALLOCATION["LATE_BULL"]


def test_all_benchmarks_and_strategy_run_through_engine_without_error():
    """Integration smoke test: every allocation series pass 2 defines
    must be a valid input to run_backtest -- catches shape/dtype
    mismatches between benchmarks.py's output and engine.py's
    expectations before they'd show up in the CLI."""
    n = 300
    rng = np.random.default_rng(9)
    dates = pd.date_range("2020-01-01", periods=n, freq="D", tz="UTC")
    close = 100 * np.cumprod(1 + rng.normal(0, 0.02, n))
    df = pd.DataFrame(
        {
            "timestamp": dates,
            "open": close * (1 + rng.normal(0, 0.005, n)),
            "close": close,
            "sma_200": pd.Series(close).rolling(200, min_periods=200).mean(),
            "regime": rng.choice(["BULL", "BEAR", "ACCUMULATION"], size=n),
            "total_allocation": rng.uniform(0, 0.9, n),
        }
    )

    allocations = {
        "bh": buy_and_hold_allocation(df),
        "cash": cash_allocation(df),
        "ma_trend": simple_ma_trend_allocation(df),
        "cycle_only": cycle_only_allocation(df),
        "strategy": df["total_allocation"],
    }
    costs = get_cost_model("baseline")
    for name, alloc in allocations.items():
        df_run = df.copy()
        df_run["_alloc"] = alloc
        result = run_backtest(df_run, allocation_col="_alloc", costs=costs, initial_capital=10_000.0)
        assert len(result.portfolio_values) == n
        assert all(v > 0 for v in result.portfolio_values)  # never blows up to zero/negative
