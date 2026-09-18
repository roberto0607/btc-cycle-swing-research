"""
Milestone 5 entrypoint: run Phase 2 exploratory analysis against the
Milestone 4 feature table and write a summary report + charts.

Usage:
    python -m src.research.statistics.run_exploratory

Reads:
    data/features/coinbase_btc_usd_1d_features.parquet
Writes:
    reports/exploratory_summary.md
    reports/figures/price_and_drawdown.png
    reports/figures/rolling_volatility.png
    reports/figures/return_distribution.png
    reports/figures/extension_vs_forward_return_{col}_{horizon}d.png

This is descriptive only -- no strategy logic, no parameter fitting (see
RESEARCH_SPEC.md Phase 2). The extension-vs-forward-return section is a
PRELIMINARY look at RESEARCH_SPEC.md's central question, not the formal
regime-conditional hypothesis test -- that's Milestone 6/7.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.research.statistics import charts
from src.research.statistics.exploratory import (
    add_forward_return_for_research,
    extension_vs_forward_return,
    summarize_returns,
    top_drawdowns,
    yearly_breakdown,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FEATURES_PATH = PROJECT_ROOT / "data" / "features" / "coinbase_btc_usd_1d_features.parquet"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# Preliminary extension-vs-pullback look: a couple of representative
# extension features x a couple of representative horizons, from the
# full grids in RESEARCH_SPEC.md section 10. Not exhaustive -- Milestone
# 7 (pullback research) covers the full label/feature grid properly.
EXTENSION_COLS = ["dist_from_sma_50", "rsi_14"]
FORWARD_HORIZONS = [14, 30]


def _render_md_table(df: pd.DataFrame, float_fmt: str = "{:.4f}") -> str:
    """Minimal DataFrame -> Markdown table renderer, avoiding a
    `tabulate` dependency for one report."""
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


def _fmt_pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def main() -> None:
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(
            f"{FEATURES_PATH} not found -- run Milestone 4 first "
            f"(python -m src.features.run_features)."
        )

    df = pd.read_parquet(FEATURES_PATH).sort_values("timestamp").reset_index(drop=True)

    summary = summarize_returns(df)
    yearly = yearly_breakdown(df)
    drawdowns = top_drawdowns(df, n=10)

    charts.plot_price_and_drawdown(df, FIGURES_DIR / "price_and_drawdown.png")
    charts.plot_rolling_volatility(df, FIGURES_DIR / "rolling_volatility.png")
    charts.plot_return_distribution(df, FIGURES_DIR / "return_distribution.png")

    extension_sections = []
    for ext_col in EXTENSION_COLS:
        for horizon in FORWARD_HORIZONS:
            fwd_col = f"_fwd_return_{horizon}d"
            df[fwd_col] = add_forward_return_for_research(df, horizon)
            binned = extension_vs_forward_return(df, ext_col, fwd_col)
            fig_path = FIGURES_DIR / f"extension_vs_forward_return_{ext_col}_{horizon}d.png"
            charts.plot_extension_vs_forward_return(
                binned, fig_path, extension_label=ext_col, horizon_label=f"{horizon}d forward return"
            )
            extension_sections.append((ext_col, horizon, binned, fig_path))

    # --- Markdown report ---
    lines = ["# Phase 2 Exploratory Analysis", ""]
    lines.append(f"Data: {summary['start_date']} \u2192 {summary['end_date']} "
                 f"({summary['n_days']} days, {summary['n_years']} years)")
    lines.append("")
    lines.append("## Whole-series summary")
    lines.append(f"- Total return: {_fmt_pct(summary['total_return'])}")
    lines.append(f"- CAGR: {_fmt_pct(summary['cagr'])}")
    lines.append(f"- Annualized volatility: {_fmt_pct(summary['annualized_volatility'])}")
    lines.append(f"- Max drawdown: {_fmt_pct(summary['max_drawdown'])}")
    lines.append(f"- Best day: {_fmt_pct(summary['best_day'])} / Worst day: {_fmt_pct(summary['worst_day'])}")
    lines.append(f"- Skew: {summary['skew']:.2f} / Kurtosis: {summary['kurtosis']:.2f}")
    lines.append("")
    lines.append("## Yearly breakdown")
    lines.append(_render_md_table(yearly.round(4)))
    lines.append("")
    lines.append("## Top 10 drawdowns")
    if drawdowns.empty:
        lines.append("(none found)")
    else:
        lines.append(_render_md_table(drawdowns))
    lines.append("")
    lines.append("## Charts")
    lines.append("![Price and drawdown](figures/price_and_drawdown.png)")
    lines.append("![Rolling volatility](figures/rolling_volatility.png)")
    lines.append("![Return distribution](figures/return_distribution.png)")
    lines.append("")
    lines.append("## Preliminary: extension vs. forward return (NOT the formal Phase 3/4 test)")
    for ext_col, horizon, binned, fig_path in extension_sections:
        lines.append(f"\n### {ext_col} vs. {horizon}-day forward return")
        lines.append(_render_md_table(binned.round(4)))
        lines.append(f"![{ext_col} vs {horizon}d forward return]({fig_path.relative_to(REPORTS_DIR)})")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "exploratory_summary.md").write_text("\n".join(lines) + "\n")

    print("Whole-series summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print(f"\nReport written to reports/exploratory_summary.md")
    print(f"Charts written to reports/figures/")


if __name__ == "__main__":
    main()
