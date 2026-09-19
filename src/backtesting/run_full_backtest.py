"""
Milestone 9 (pass 2) entrypoint: run the actual cycle+swing strategy
(Milestone 8's total_allocation) against all four benchmarks
(RESEARCH_SPEC.md section 20), across all four cost scenarios
(section 19), and write a comparison report + equity curve chart.

Usage:
    python -m src.backtesting.run_full_backtest

Reads:
    data/labels/coinbase_btc_usd_1d_strategy_signal.parquet
Writes:
    reports/backtest_comparison.md
    reports/figures/equity_curves.png

No single "best strategy" score is produced (section 22) -- the report
is a table across scenarios; interpretation is left explicit rather than
collapsed into one number.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.backtesting.benchmarks import (
    buy_and_hold_allocation,
    cash_allocation,
    cycle_only_allocation,
    simple_ma_trend_allocation,
)
from src.backtesting.charts import plot_equity_curves
from src.backtesting.costs import COST_SCENARIOS
from src.backtesting.engine import run_backtest
from src.backtesting.metrics import compute_metrics

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SIGNAL_PATH = PROJECT_ROOT / "data" / "labels" / "coinbase_btc_usd_1d_strategy_signal.parquet"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

INITIAL_CAPITAL = 10_000.0

STRATEGIES = {
    "Buy & Hold": buy_and_hold_allocation,
    "Cash": cash_allocation,
    "Simple MA Trend": simple_ma_trend_allocation,
    "Cycle Only": cycle_only_allocation,
    "Cycle + Swing (the strategy)": lambda df: df["total_allocation"],
}

METRIC_COLS = [
    "total_return", "cagr", "annualized_volatility", "max_drawdown",
    "sharpe", "sortino", "calmar", "avg_exposure", "n_trades", "total_fees_paid",
]


def _render_md_table(df: pd.DataFrame, float_fmt: str = "{:.4f}") -> str:
    if df.empty:
        return "(no data)"

    def fmt(v):
        if isinstance(v, float):
            return float_fmt.format(v)
        return str(v)

    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    sep = "|" + "|".join(["---"] * len(cols)) + "|"
    rows = ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([header, sep] + rows)


def main() -> None:
    if not SIGNAL_PATH.exists():
        raise FileNotFoundError(
            f"{SIGNAL_PATH} not found -- run Milestone 8 first "
            f"(python -m src.strategies.run_strategy)."
        )

    df = pd.read_parquet(SIGNAL_PATH).sort_values("timestamp").reset_index(drop=True)

    allocations: dict[str, pd.Series] = {name: fn(df) for name, fn in STRATEGIES.items()}

    baseline_curves: dict[str, pd.Series] = {}
    all_rows = []

    for scenario_name, cost_model in COST_SCENARIOS.items():
        for strat_name, alloc_series in allocations.items():
            df_run = df.copy()
            df_run["_alloc"] = alloc_series
            result = run_backtest(df_run, allocation_col="_alloc", costs=cost_model, initial_capital=INITIAL_CAPITAL)
            values = result.to_series()
            total_fees = sum(t.fee_paid for t in result.portfolio.trades)
            metrics = compute_metrics(
                values, n_trades=len(result.portfolio.trades),
                allocation_series=alloc_series, total_fees_paid=total_fees,
            )
            row = {"scenario": scenario_name, "strategy": strat_name, **{k: metrics.get(k) for k in METRIC_COLS}}
            all_rows.append(row)

            if scenario_name == "baseline":
                baseline_curves[strat_name] = values

    comparison = pd.DataFrame(all_rows)

    plot_equity_curves(baseline_curves, FIGURES_DIR / "equity_curves.png")

    lines = ["# Phase 6 Backtest Comparison", ""]
    lines.append(
        "Milestone 8's cycle+swing strategy vs. four benchmarks "
        "(RESEARCH_SPEC.md section 20), across four cost scenarios "
        "(section 19). No single composite score -- compare rows "
        "directly. `Cycle Only` vs `Cycle + Swing` isolates whether the "
        "tactical swing layer earns its complexity over the core "
        "allocation alone."
    )
    lines.append("")
    for scenario_name in COST_SCENARIOS:
        lines.append(f"\n## {scenario_name} costs")
        subset = comparison[comparison["scenario"] == scenario_name].drop(columns=["scenario"])
        lines.append(_render_md_table(subset.round(4)))

    lines.append("\n## Equity curves (baseline costs)")
    lines.append("![Equity curves](figures/equity_curves.png)")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "backtest_comparison.md").write_text("\n".join(lines) + "\n")

    print(comparison[comparison["scenario"] == "baseline"].drop(columns=["scenario"]).to_string(index=False))
    print(f"\nReport written to reports/backtest_comparison.md")
    print(f"Chart written to reports/figures/equity_curves.png")


if __name__ == "__main__":
    main()
