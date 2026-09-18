"""
Milestone 6 entrypoint: classify regimes on the Milestone 4 feature table,
then run the Phase 3 analysis (persistence, transitions, regime-
conditional forward returns) and write a report + chart.

Usage:
    python -m src.research.cycles.run_cycle_research

Reads:
    data/features/coinbase_btc_usd_1d_features.parquet
Writes:
    reports/cycle_research_summary.md
    reports/figures/price_with_regimes.png
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.regimes.analysis import (
    regime_conditional_stats,
    regime_segment_stats,
    regime_transition_matrix,
)
from src.regimes.charts import plot_price_with_regimes
from src.regimes.classifier import classify_regime

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FEATURES_PATH = PROJECT_ROOT / "data" / "features" / "coinbase_btc_usd_1d_features.parquet"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

HORIZONS = [14, 30, 90]


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
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(
            f"{FEATURES_PATH} not found -- run Milestone 4 first "
            f"(python -m src.features.run_features)."
        )

    df = pd.read_parquet(FEATURES_PATH).sort_values("timestamp").reset_index(drop=True)
    df = classify_regime(df)

    segment_stats = regime_segment_stats(df)
    transitions = regime_transition_matrix(df)

    plot_price_with_regimes(df, FIGURES_DIR / "price_with_regimes.png")

    lines = ["# Phase 3 Cycle / Regime Research", ""]
    lines.append(
        "Regime definitions are a first-pass research hypothesis "
        "(RESEARCH_SPEC.md section 5 / src/regimes/definitions.py) -- "
        "this report is exactly the test of whether they carry information."
    )
    lines.append("")
    lines.append("## Regime persistence")
    lines.append(
        "If a regime's avg_duration_days is only a few days, the label "
        "is flickering, not describing a real market state."
    )
    lines.append(_render_md_table(segment_stats.round(4)))
    lines.append("")
    lines.append("## Day-to-day transition matrix")
    lines.append("Rows = today's regime, columns = tomorrow's regime. Diagonal = stickiness.")
    lines.append(_render_md_table(transitions.reset_index().rename(columns={"regime": "from \\ to"}).round(3)))
    lines.append("")
    lines.append("## Chart")
    lines.append("![Price with regimes](figures/price_with_regimes.png)")
    lines.append("")
    lines.append(
        "## Regime-conditional forward returns and pullback probability\n\n"
        "Compare each regime's row against the 'ALL' (unconditional) row. "
        "If they don't look meaningfully different, this regime scheme "
        "isn't adding information over just looking at the whole series -- "
        "that's a valid, useful research conclusion, not a failure.\n\n"
        "**Confidence caveat:** `n_distinct_years` and `max_single_year_share` "
        "show how spread out each row's sample actually is. A regime/horizon "
        "combination with few distinct years, or a high max_single_year_share, "
        "is more likely reflecting one historical episode than a repeatable "
        "pattern (RESEARCH_SPEC.md section 47 -- BTC has few independent "
        "cycles). Rows flagged CONCENTRATED below have max_single_year_share "
        "\u2265 40%: read their numbers as a real but not-yet-confirmed lead, not "
        "an established result."
    )
    CONCENTRATION_THRESHOLD = 0.40
    for horizon in HORIZONS:
        stats = regime_conditional_stats(df, horizon)
        stats["confidence"] = stats["max_single_year_share"].apply(
            lambda x: "CONCENTRATED" if pd.notnull(x) and x >= CONCENTRATION_THRESHOLD else "ok"
        )
        lines.append(f"\n### {horizon}-day forward horizon")
        lines.append(_render_md_table(stats.round(4)))

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "cycle_research_summary.md").write_text("\n".join(lines) + "\n")

    print("Regime segment persistence:")
    print(segment_stats.to_string(index=False))
    print(f"\nReport written to reports/cycle_research_summary.md")
    print(f"Chart written to reports/figures/price_with_regimes.png")


if __name__ == "__main__":
    main()
