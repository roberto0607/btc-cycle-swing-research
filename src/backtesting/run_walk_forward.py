"""
Milestone 11 entrypoint: Phase 8 walk-forward evaluation of Cycle Only
against Buy & Hold across sequential, non-overlapping windows.

Usage:
    python -m src.backtesting.run_walk_forward

Reads:
    data/labels/coinbase_btc_usd_1d_strategy_signal.parquet
Writes:
    reports/walk_forward_summary.md
    reports/figures/walk_forward_windows.png
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.backtesting.benchmarks import buy_and_hold_allocation, cycle_only_allocation
from src.backtesting.walk_forward import compare_to_benchmark_per_window, run_walk_forward
from src.backtesting.walk_forward_charts import plot_walk_forward_windows

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SIGNAL_PATH = PROJECT_ROOT / "data" / "labels" / "coinbase_btc_usd_1d_strategy_signal.parquet"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

WINDOW_YEARS = 2.0


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
    df["cycle_only_alloc"] = cycle_only_allocation(df)
    df["bh_alloc"] = buy_and_hold_allocation(df)

    strategy_windows = run_walk_forward(df, allocation_col="cycle_only_alloc", window_years=WINDOW_YEARS)
    benchmark_windows = run_walk_forward(df, allocation_col="bh_alloc", window_years=WINDOW_YEARS)
    merged = compare_to_benchmark_per_window(strategy_windows, benchmark_windows)

    win_rate_cagr = merged["beat_on_cagr"].mean()
    win_rate_drawdown = merged["beat_on_drawdown"].mean()
    most_recent = merged[merged["is_most_recent_strategy"]].iloc[0]

    plot_walk_forward_windows(merged, FIGURES_DIR / "walk_forward_windows.png")

    display_cols = [
        "window_start", "window_end", "n_days_strategy",
        "cagr_strategy", "cagr_benchmark", "beat_on_cagr",
        "max_drawdown_strategy", "max_drawdown_benchmark", "beat_on_drawdown",
    ]

    lines = ["# Phase 8 Walk-Forward Evaluation -- Cycle Only vs Buy & Hold", ""]
    lines.append(
        "**Honesty note (read this before the numbers):** Cycle Only's "
        "allocation table was never numerically fit to this dataset -- "
        "it's a fixed hypothesis from Milestone 6's qualitative regime "
        "ranking, not an optimized parameter set, so there's no "
        "parameter-fitting leakage for walk-forward to catch in the usual "
        "ML sense. However, the DECISION to keep Cycle Only over Cycle + "
        "Swing (Milestone 9) was made using full-history results, "
        "including the most recent window below. This is therefore a "
        "test of whether the already-chosen, frozen strategy's edge holds "
        "up window by window -- not an uncontaminated test of whether it "
        "was the right strategy to choose in the first place. See "
        "RESEARCH_SPEC.md section 12.5 and src/backtesting/walk_forward.py "
        "for the full caveat."
    )
    lines.append("")
    lines.append(f"- Windows where strategy beat Buy & Hold on CAGR: {win_rate_cagr:.0%}")
    lines.append(f"- Windows where strategy beat Buy & Hold on max drawdown: {win_rate_drawdown:.0%}")
    lines.append(
        f"- **Most recent window** ({most_recent['window_start'].date()} \u2192 "
        f"{most_recent['window_end'].date()}): strategy CAGR "
        f"{most_recent['cagr_strategy']:.2%} vs Buy & Hold "
        f"{most_recent['cagr_benchmark']:.2%} "
        f"({'beat' if most_recent['beat_on_cagr'] else 'did NOT beat'} benchmark)"
    )
    lines.append("")
    lines.append("## Window-by-window comparison")
    merged_display = merged[display_cols].copy()
    numeric_cols = merged_display.select_dtypes(include="number").columns
    merged_display[numeric_cols] = merged_display[numeric_cols].round(4)
    lines.append(_render_md_table(merged_display))
    lines.append("")
    lines.append("## Chart")
    lines.append("![Walk-forward windows](figures/walk_forward_windows.png)")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "walk_forward_summary.md").write_text("\n".join(lines) + "\n")

    print(merged[display_cols].to_string(index=False))
    print(f"\nWin rate on CAGR: {win_rate_cagr:.0%}")
    print(f"Win rate on max drawdown: {win_rate_drawdown:.0%}")
    print(f"\nReport written to reports/walk_forward_summary.md")


if __name__ == "__main__":
    main()
