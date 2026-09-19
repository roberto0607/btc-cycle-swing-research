"""
Milestone 15 entrypoint: the final locked holdout test on the most
recent 6 months of data, comparing the FROZEN Cycle Only strategy
against Buy & Hold, Cash, and Simple MA Trend.

Usage:
    python -m src.backtesting.run_locked_holdout

Reads:
    data/labels/coinbase_btc_usd_1d_strategy_signal.parquet
Writes:
    reports/locked_holdout_summary.md
    reports/figures/locked_holdout_equity_curves.png

This is a ONE-TIME check. Per the honesty note in locked_holdout.py,
re-running this after tweaking the strategy based on its result defeats
its purpose -- the strategy is frozen as of this run.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.backtesting.benchmarks import (
    buy_and_hold_allocation,
    cash_allocation,
    cycle_only_allocation,
    simple_ma_trend_allocation,
)
from src.backtesting.costs import get_cost_model
from src.backtesting.engine import run_backtest
from src.backtesting.locked_holdout import DEFAULT_HOLDOUT_MONTHS, define_holdout, run_locked_holdout

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SIGNAL_PATH = PROJECT_ROOT / "data" / "labels" / "coinbase_btc_usd_1d_strategy_signal.parquet"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"


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


def _plot_equity_curves(df: pd.DataFrame, allocations: dict, months: int, out_path: Path) -> None:
    start, end = define_holdout(df, months=months)
    mask = (df["timestamp"] >= start) & (df["timestamp"] <= end)
    holdout_df = df.loc[mask].reset_index(drop=True)
    costs = get_cost_model("baseline")

    fig, ax = plt.subplots(figsize=(11, 5))
    for name, alloc in allocations.items():
        segment = holdout_df.copy()
        segment["_alloc"] = alloc.loc[mask].reset_index(drop=True)
        result = run_backtest(segment, allocation_col="_alloc", costs=costs, initial_capital=10_000.0)
        series = result.to_series()
        ax.plot(series.index, series / series.iloc[0] * 100, label=name, linewidth=1.2)

    ax.set_ylabel("Portfolio value (indexed to 100)")
    ax.set_title(f"Locked holdout ({months} months): {start.date()} \u2192 {end.date()}")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def main() -> None:
    if not SIGNAL_PATH.exists():
        raise FileNotFoundError(f"{SIGNAL_PATH} not found -- run earlier milestones first.")

    df = pd.read_parquet(SIGNAL_PATH).sort_values("timestamp").reset_index(drop=True)

    allocations = {
        "Cycle Only (frozen strategy)": cycle_only_allocation(df),
        "Buy & Hold": buy_and_hold_allocation(df),
        "Cash": cash_allocation(df),
        "Simple MA Trend": simple_ma_trend_allocation(df),
    }

    results = run_locked_holdout(df, allocations, months=DEFAULT_HOLDOUT_MONTHS)
    _plot_equity_curves(df, allocations, DEFAULT_HOLDOUT_MONTHS, FIGURES_DIR / "locked_holdout_equity_curves.png")

    start, end = define_holdout(df, months=DEFAULT_HOLDOUT_MONTHS)
    display_cols = ["strategy", "n_days", "total_return", "cagr", "max_drawdown", "sharpe", "sortino", "n_trades"]
    display = results[display_cols].copy()
    numeric_cols = display.select_dtypes(include="number").columns
    display[numeric_cols] = display[numeric_cols].round(4)

    lines = ["# Locked Holdout Test -- Final Gate Before Paper Deployment", ""]
    lines.append(
        f"Holdout window: **{start.date()} \u2192 {end.date()}** ({DEFAULT_HOLDOUT_MONTHS} months, "
        f"the most recent data available). Baseline cost scenario, fresh capital."
    )
    lines.append("")
    lines.append(
        "**Honesty note:** this is not a statistically clean never-seen "
        "holdout -- these days were part of the full-history data used to "
        "select Cycle Only over Cycle + Swing (Milestone 9). Its value is "
        "as a discipline commitment: the strategy is FROZEN as of this "
        "run. No further tuning based on this result. See "
        "src/backtesting/locked_holdout.py for the full caveat."
    )
    lines.append("")
    lines.append("## Results")
    lines.append(_render_md_table(display))
    lines.append("")
    lines.append("## Equity curves")
    lines.append("![Locked holdout equity curves](figures/locked_holdout_equity_curves.png)")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "locked_holdout_summary.md").write_text("\n".join(lines) + "\n")

    print(f"Holdout: {start.date()} -> {end.date()}")
    print(display.to_string(index=False))
    print(f"\nReport written to reports/locked_holdout_summary.md")


if __name__ == "__main__":
    main()
