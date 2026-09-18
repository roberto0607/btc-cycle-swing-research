"""
Milestone 7 entrypoint: build the full PULLBACK(threshold, horizon) label
grid, classify regimes, and run the regime-conditional extension-vs-
pullback analysis -- the central RESEARCH_SPEC.md question, finally
properly conditioned by regime.

Usage:
    python -m src.research.pullbacks.run_pullback_research

Reads:
    data/features/coinbase_btc_usd_1d_features.parquet
Writes:
    data/labels/coinbase_btc_usd_1d_labeled.parquet   (features + regime +
                                                         full pullback label grid)
    reports/pullback_research_summary.md
    reports/figures/pullback_rate_{ext}_{pullback}.png
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.regimes.classifier import classify_regime
from src.research.pullbacks.analysis import regime_conditional_extension_pullback
from src.research.pullbacks.charts import plot_regime_conditional_pullback_rates
from src.research.pullbacks.labels import DEFAULT_HORIZONS, DEFAULT_THRESHOLDS, add_pullback_labels

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FEATURES_PATH = PROJECT_ROOT / "data" / "features" / "coinbase_btc_usd_1d_features.parquet"
LABELS_PATH = PROJECT_ROOT / "data" / "labels" / "coinbase_btc_usd_1d_labeled.parquet"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# What actually goes in the printed report: the full 42-combination grid
# is built and saved to data/labels/ for later milestones, but reporting
# all of it here would be unreadable. This subset is representative --
# RESEARCH_SPEC.md's own suggested starting point (10%/30D) plus a
# shorter and longer horizon for context.
REPORT_EXTENSION_COLS = ["rsi_14", "dist_from_sma_50", "runup_from_low_365d"]
REPORT_PULLBACK_COLS = ["pullback_10pct_14d", "pullback_10pct_30d", "pullback_10pct_90d"]


def _render_md_table(df: pd.DataFrame, float_fmt: str = "{:.4f}") -> str:
    if df.empty:
        return "(no data -- likely insufficient sample size per regime/bucket)"

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
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(
            f"{FEATURES_PATH} not found -- run Milestone 4 first "
            f"(python -m src.features.run_features)."
        )

    df = pd.read_parquet(FEATURES_PATH).sort_values("timestamp").reset_index(drop=True)
    df = classify_regime(df)
    df = add_pullback_labels(df, thresholds=DEFAULT_THRESHOLDS, horizons=DEFAULT_HORIZONS)

    LABELS_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(LABELS_PATH, index=False)

    n_label_cols = len(DEFAULT_THRESHOLDS) * len(DEFAULT_HORIZONS)
    print(f"Built {n_label_cols} pullback label columns across {len(df)} rows.")
    print(f"Labeled dataset written to {LABELS_PATH}")

    lines = ["# Phase 4 Pullback Research", ""]
    lines.append(
        "Full PULLBACK(threshold, horizon) grid "
        f"({len(DEFAULT_THRESHOLDS)} thresholds x {len(DEFAULT_HORIZONS)} horizons = "
        f"{n_label_cols} labels) is in `data/labels/coinbase_btc_usd_1d_labeled.parquet`. "
        "This report shows a representative subset for readability."
    )
    lines.append("")
    lines.append(
        "## The central question, properly conditioned\n\n"
        "Milestone 5's extension-vs-forward-return table was unconditional "
        "and showed the OPPOSITE of the swing hypothesis (extension looked "
        "bullish). RESEARCH_SPEC.md section 12 said that's expected if the "
        "relationship depends on regime and wasn't being isolated. Compare "
        "each regime's bucket rates below against the 'ALL' row: if High "
        "extension shows a meaningfully higher pullback_rate than Low "
        "extension WITHIN a regime (especially BULL/LATE_BULL, where "
        "Milestone 5's unconditional view was dominated by 'up mostly goes "
        "up'), that's the swing signal Milestone 5 couldn't isolate. "
        "Buckets with n below the minimum sample size are omitted rather "
        "than shown with an unreliable rate."
    )

    for pullback_col in REPORT_PULLBACK_COLS:
        for ext_col in REPORT_EXTENSION_COLS:
            table = regime_conditional_extension_pullback(df, ext_col, pullback_col)
            fig_path = FIGURES_DIR / f"pullback_rate_{ext_col}_{pullback_col}.png"
            if not table.empty:
                plot_regime_conditional_pullback_rates(
                    table, fig_path, extension_label=ext_col, pullback_label=pullback_col
                )
            lines.append(f"\n### {pullback_col} by {ext_col} bucket, per regime")
            lines.append(_render_md_table(table.round(4)))
            if not table.empty:
                lines.append(f"![{ext_col} vs {pullback_col}]({fig_path.relative_to(REPORTS_DIR)})")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "pullback_research_summary.md").write_text("\n".join(lines) + "\n")

    print(f"\nReport written to reports/pullback_research_summary.md")
    print(f"Charts written to reports/figures/")


if __name__ == "__main__":
    main()
