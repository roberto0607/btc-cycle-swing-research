"""
Milestone 8 entrypoint: run the deterministic cycle + swing strategy
against the Milestone 7 labeled dataset and write a signal file + report.

Usage:
    python -m src.strategies.run_strategy

Reads:
    data/labels/coinbase_btc_usd_1d_labeled.parquet
Writes:
    data/labels/coinbase_btc_usd_1d_strategy_signal.parquet
    reports/strategy_signal_summary.md
    reports/figures/strategy_price_and_allocation.png

NO backtest happens here -- this produces target allocations only. See
RESEARCH_SPEC.md Phase 5 vs Phase 6: the strategy must exist and be
fully deterministic BEFORE any backtesting engine touches it.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.strategies.charts import plot_price_and_allocation
from src.strategies.combined import run_combined_strategy

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LABELED_PATH = PROJECT_ROOT / "data" / "labels" / "coinbase_btc_usd_1d_labeled.parquet"
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


def main() -> None:
    if not LABELED_PATH.exists():
        raise FileNotFoundError(
            f"{LABELED_PATH} not found -- run Milestone 7 first "
            f"(python -m src.research.pullbacks.run_pullback_research)."
        )

    df = pd.read_parquet(LABELED_PATH).sort_values("timestamp").reset_index(drop=True)
    df = run_combined_strategy(df)

    SIGNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(SIGNAL_PATH, index=False)

    classified = df.dropna(subset=["regime"])
    by_regime = classified.groupby("regime").agg(
        n_days=("regime", "size"),
        avg_core=("core_allocation", "mean"),
        avg_tactical=("tactical_allocation", "mean"),
        avg_total=("total_allocation", "mean"),
    ).reset_index()

    reduced_segments = classified[classified["swing_state"] == "REDUCED"].copy()
    reduced_segments["segment_id"] = (
        classified["swing_state"] != classified["swing_state"].shift()
    ).cumsum().loc[reduced_segments.index]
    n_reductions = reduced_segments["segment_id"].nunique()
    pct_time_reduced = (classified["swing_state"] == "REDUCED").mean()

    plot_price_and_allocation(df, FIGURES_DIR / "strategy_price_and_allocation.png")

    lines = ["# Phase 5 Deterministic Strategy Signal", ""]
    lines.append(
        "Core allocation by regime (src/strategies/cycle.py) and tactical "
        "swing overlay (src/strategies/swing.py) -- both first-pass "
        "hypotheses per their module docstrings, not optimized parameters. "
        "No backtest yet; this is target allocation only (Phase 5, before "
        "Phase 6's backtester)."
    )
    lines.append("")
    lines.append("## Allocation by regime")
    lines.append(_render_md_table(by_regime.round(4)))
    lines.append("")
    lines.append(
        f"## Tactical reduction activity\n\n"
        f"- Number of distinct REDUCED episodes: {n_reductions}\n"
        f"- Fraction of classified days spent REDUCED: {pct_time_reduced:.2%}"
    )
    lines.append("")
    lines.append("## Chart")
    lines.append("![Price and allocation](figures/strategy_price_and_allocation.png)")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "strategy_signal_summary.md").write_text("\n".join(lines) + "\n")

    print("Allocation by regime:")
    print(by_regime.to_string(index=False))
    print(f"\nDistinct REDUCED episodes: {n_reductions}")
    print(f"Fraction of time REDUCED: {pct_time_reduced:.2%}")
    print(f"\nSignal file written to {SIGNAL_PATH}")
    print(f"Report written to reports/strategy_signal_summary.md")


if __name__ == "__main__":
    main()
