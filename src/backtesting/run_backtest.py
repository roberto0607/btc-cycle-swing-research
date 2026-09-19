"""
Milestone 9 (pass 1) entrypoint: run a 100% buy-and-hold backtest and
verify the engine's output against an independently hand-computed
expected value. This is the sanity check RESEARCH_SPEC.md's own coding
instructions call for before trusting the engine with a real strategy.

Usage:
    python -m src.backtesting.run_backtest

Reads:
    data/labels/coinbase_btc_usd_1d_strategy_signal.parquet
Writes:
    reports/backtest_sanity_check.md
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.backtesting.benchmarks import buy_and_hold_allocation
from src.backtesting.costs import get_cost_model
from src.backtesting.engine import run_backtest
from src.backtesting.metrics import compute_metrics

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SIGNAL_PATH = PROJECT_ROOT / "data" / "labels" / "coinbase_btc_usd_1d_strategy_signal.parquet"
REPORTS_DIR = PROJECT_ROOT / "reports"

INITIAL_CAPITAL = 10_000.0


def independent_expected_value(df: pd.DataFrame, costs, initial_capital: float) -> float:
    """
    Hand-computed expected end value for 100% buy-and-hold, built
    independently of engine.py's own logic (different code path, same
    math worked out by hand) -- if this doesn't match run_backtest's
    output, the engine has a real bug, not just a style difference.

    A single BUY at day 1's open (day 0 has no prior decision yet, per
    engine.py's timing), held to the end, mark-to-market at the final
    close.
    """
    first_open = df["open"].iloc[1]
    last_close = df["close"].iloc[-1]

    impact = costs.total_price_impact_bps / 10_000.0
    fill_price = first_open * (1 + impact)  # buying: worse (higher) price
    fee = initial_capital * (costs.fee_bps / 10_000.0)
    btc_bought = (initial_capital - fee) / fill_price

    return btc_bought * last_close


def main() -> None:
    if not SIGNAL_PATH.exists():
        raise FileNotFoundError(
            f"{SIGNAL_PATH} not found -- run Milestone 8 first "
            f"(python -m src.strategies.run_strategy)."
        )

    df = pd.read_parquet(SIGNAL_PATH).sort_values("timestamp").reset_index(drop=True)
    df["bh_allocation"] = buy_and_hold_allocation(df)

    costs = get_cost_model("baseline")
    result = run_backtest(df, allocation_col="bh_allocation", costs=costs, initial_capital=INITIAL_CAPITAL)

    engine_end_value = result.portfolio_values[-1]
    expected_end_value = independent_expected_value(df, costs, INITIAL_CAPITAL)
    diff = abs(engine_end_value - expected_end_value)
    diff_pct = diff / expected_end_value

    metrics = compute_metrics(result.to_series(), n_trades=len(result.portfolio.trades))

    passed = diff_pct < 1e-6
    status = "PASS" if passed else "FAIL"

    lines = ["# Backtest Engine Sanity Check", ""]
    lines.append(
        "100% buy-and-hold is the trivial case: one BUY, held forever. "
        "The engine's simulated end value is compared against an "
        "independently hand-computed expected value using the same cost "
        "assumptions but different code."
    )
    lines.append("")
    lines.append(f"- Engine end value: ${engine_end_value:,.2f}")
    lines.append(f"- Independently expected end value: ${expected_end_value:,.2f}")
    lines.append(f"- Difference: ${diff:,.4f} ({diff_pct:.8%})")
    lines.append(f"- **{status}** (threshold: 0.0001% relative difference)")
    lines.append("")
    lines.append("## Buy-and-hold metrics (baseline cost scenario)")
    for k, v in metrics.items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append(f"- Number of trades executed: {len(result.portfolio.trades)} (expect exactly 1 -- a single entry, never rebalanced since allocation never changes)")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "backtest_sanity_check.md").write_text("\n".join(lines) + "\n")

    print(f"Engine end value:       ${engine_end_value:,.2f}")
    print(f"Expected end value:     ${expected_end_value:,.2f}")
    print(f"Relative difference:    {diff_pct:.8%}")
    print(f"Status: {status}")
    print(f"Trades executed: {len(result.portfolio.trades)}")
    print(f"\nReport written to reports/backtest_sanity_check.md")

    if not passed:
        raise AssertionError(
            f"Sanity check FAILED: engine end value ${engine_end_value:,.2f} != "
            f"expected ${expected_end_value:,.2f} (diff {diff_pct:.6%})"
        )


if __name__ == "__main__":
    main()
