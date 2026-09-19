"""
Milestone 12 entrypoint: does the ML baseline (logistic regression,
walk-forward fit) beat Cycle Only out-of-sample? RESEARCH_SPEC.md
section 36: "The key experiment: Deterministic Strategy vs. ML-Enhanced
Strategy using locked out-of-sample periods." Section 37: ML is retained
ONLY if it produces a meaningful, persistent improvement on unseen data
-- rejection is a valid, complete result, not a failure.

Usage:
    python -m src.ml.run_ml_comparison

Reads:
    data/labels/coinbase_btc_usd_1d_strategy_signal.parquet
    (must already have Milestone 7's pullback_10pct_30d column and
    Milestone 6's regime column)
Writes:
    reports/ml_comparison_summary.md
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.backtesting.benchmarks import cycle_only_allocation
from src.backtesting.walk_forward import run_walk_forward
from src.ml.walk_forward_ml import run_ml_walk_forward

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SIGNAL_PATH = PROJECT_ROOT / "data" / "labels" / "coinbase_btc_usd_1d_strategy_signal.parquet"
REPORTS_DIR = PROJECT_ROOT / "reports"

TARGET_COL = "pullback_10pct_30d"
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
        raise FileNotFoundError(f"{SIGNAL_PATH} not found -- run Milestone 7/8 first.")

    df = pd.read_parquet(SIGNAL_PATH).sort_values("timestamp").reset_index(drop=True)
    if TARGET_COL not in df.columns:
        raise ValueError(f"{TARGET_COL} not found -- run Milestone 7 (pullback labels) first.")

    df["cycle_only_alloc"] = cycle_only_allocation(df)

    ml_results = run_ml_walk_forward(df, target_col=TARGET_COL, window_years=WINDOW_YEARS)
    baseline_results = run_walk_forward(df, allocation_col="cycle_only_alloc", window_years=WINDOW_YEARS)

    merged = ml_results.merge(
        baseline_results[["window_start", "window_end", "cagr", "max_drawdown", "sharpe"]],
        on=["window_start", "window_end"],
        suffixes=("_ml", "_baseline"),
    )
    evaluated = merged[~merged["skipped"]].copy()

    if evaluated.empty:
        verdict = "INCONCLUSIVE -- no window had enough training data to evaluate."
    else:
        evaluated["ml_beats_on_sharpe"] = evaluated["sharpe_ml"] > evaluated["sharpe_baseline"]
        evaluated["ml_beats_on_cagr"] = evaluated["cagr_ml"] > evaluated["cagr_baseline"]
        sharpe_win_rate = evaluated["ml_beats_on_sharpe"].mean()
        cagr_win_rate = evaluated["ml_beats_on_cagr"].mean()
        mean_auc = evaluated["roc_auc"].dropna().mean()

        if sharpe_win_rate >= 0.6 and mean_auc > 0.55:
            verdict = (
                f"RETAIN (tentatively) -- ML beat Cycle Only on Sharpe in "
                f"{sharpe_win_rate:.0%} of evaluated windows, mean out-of-sample "
                f"ROC-AUC {mean_auc:.3f}. Worth further validation before trusting fully."
            )
        else:
            verdict = (
                f"REJECT -- ML beat Cycle Only on Sharpe in only "
                f"{sharpe_win_rate:.0%} of evaluated windows (CAGR: {cagr_win_rate:.0%}), "
                f"mean out-of-sample ROC-AUC {mean_auc:.3f}. Per RESEARCH_SPEC.md "
                f"section 37, this is a valid, complete result -- the deterministic "
                f"Cycle Only baseline stands."
            )

    lines = ["# Phase 9 ML Baseline vs Deterministic Baseline", ""]
    lines.append(
        f"Target: `{TARGET_COL}` (10% pullback within 30 days). Model: "
        f"logistic regression, expanding-window walk-forward (fit only on "
        f"data strictly before each window, per RESEARCH_SPEC.md section "
        f"39). Compared against Cycle Only (RESEARCH_SPEC.md section 12.5) "
        f"on the SAME window boundaries as Milestone 11."
    )
    lines.append("")
    lines.append(f"## Verdict\n\n**{verdict}**")
    lines.append("")
    lines.append("## Window-by-window comparison")
    display_cols = [
        "window_start", "window_end", "n_train", "skipped",
        "base_rate", "accuracy", "roc_auc",
        "cagr_ml", "cagr_baseline", "sharpe_ml", "sharpe_baseline",
        "max_drawdown_ml", "max_drawdown_baseline",
    ]
    display = merged[display_cols].copy()
    numeric_cols = display.select_dtypes(include="number").columns
    display[numeric_cols] = display[numeric_cols].round(4)
    lines.append(_render_md_table(display))

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "ml_comparison_summary.md").write_text("\n".join(lines) + "\n")

    print(display.to_string(index=False))
    print(f"\nVerdict: {verdict}")
    print(f"\nReport written to reports/ml_comparison_summary.md")


if __name__ == "__main__":
    main()
