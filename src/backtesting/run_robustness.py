"""
Milestone 10 entrypoint: Phase 7 robustness testing on Cycle Only, the
strategy that survived Milestone 9's comparison (RESEARCH_SPEC.md section
12.5).

Usage:
    python -m src.backtesting.run_robustness

Reads:
    data/labels/coinbase_btc_usd_1d_strategy_signal.parquet
Writes:
    reports/robustness_summary.md
    reports/figures/parameter_perturbation.png
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.backtesting.benchmarks import cycle_only_allocation
from src.backtesting.robustness import execution_model_comparison, parameter_perturbation, per_cycle_metrics
from src.backtesting.robustness_charts import plot_parameter_perturbation

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


def main() -> None:
    if not SIGNAL_PATH.exists():
        raise FileNotFoundError(
            f"{SIGNAL_PATH} not found -- run Milestone 8 first "
            f"(python -m src.strategies.run_strategy)."
        )

    df = pd.read_parquet(SIGNAL_PATH).sort_values("timestamp").reset_index(drop=True)
    df["cycle_only_alloc"] = cycle_only_allocation(df)

    perturbation = parameter_perturbation(df)
    execution = execution_model_comparison(df, allocation_col="cycle_only_alloc")
    per_cycle = per_cycle_metrics(df, allocation_col="cycle_only_alloc")

    plot_parameter_perturbation(perturbation, FIGURES_DIR / "parameter_perturbation.png")

    lines = ["# Phase 7 Robustness Testing -- Cycle Only", ""]
    lines.append(
        "Scoped to Cycle Only (RESEARCH_SPEC.md section 12.5 -- the swing "
        "layer was dropped after Milestone 9). Three checks: does "
        "performance hold across a region of the core-allocation "
        "parameters (not just the exact chosen values), does it survive a "
        "worse execution assumption, and does it hold up cycle-by-cycle "
        "rather than being carried by one spectacular period."
    )
    lines.append("")
    lines.append(
        "## 1. Parameter perturbation\n\n"
        "Every regime's core allocation scaled by a factor (1.0 = the "
        "unperturbed table). Look for a stable plateau around 1.0, not an "
        "isolated spike."
    )
    lines.append(_render_md_table(perturbation.round(4)))
    lines.append("![Parameter perturbation](figures/parameter_perturbation.png)")
    lines.append("")
    lines.append("## 2. Execution model degradation\n\nNEXT_OPEN (realistic default) vs SAME_CLOSE (unrealistic, comparison-only).")
    lines.append(_render_md_table(execution.round(4)))
    lines.append("")
    lines.append(
        "## 3. Per-cycle breakdown\n\n"
        "Performance measured independently within each major historical "
        "peak-to-peak cycle (boundaries from Milestone 5's drawdown-"
        "episode detector)."
    )
    per_cycle_display = per_cycle.copy()
    numeric_cols = per_cycle_display.select_dtypes(include="number").columns
    per_cycle_display[numeric_cols] = per_cycle_display[numeric_cols].round(4)
    lines.append(_render_md_table(per_cycle_display))

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "robustness_summary.md").write_text("\n".join(lines) + "\n")

    print("Parameter perturbation:")
    print(perturbation.to_string(index=False))
    print("\nExecution model comparison:")
    print(execution.to_string(index=False))
    print("\nPer-cycle breakdown:")
    print(per_cycle.to_string(index=False))
    print(f"\nReport written to reports/robustness_summary.md")


if __name__ == "__main__":
    main()
