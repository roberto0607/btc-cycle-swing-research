"""
Chart for the regime-conditional extension-vs-pullback table
(analysis.regime_conditional_extension_pullback).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_regime_conditional_pullback_rates(
    table: pd.DataFrame, out_path: Path, extension_label: str, pullback_label: str
) -> Path:
    """`table` is the output of regime_conditional_extension_pullback."""
    regimes = [r for r in table["regime"].unique() if r != "ALL"]
    if hasattr(table["extension_bucket"], "cat"):
        buckets = list(table["extension_bucket"].cat.categories)
    else:
        # pd.unique() preserves first-appearance order, which -- because
        # analysis.py's groupby iterates an ordered Categorical (Low,
        # Mid, High) before the result is collected into plain dict rows
        # -- already reflects the intended Low->Mid->High order, unlike
        # sorted() which would alphabetize to High/Low/Mid.
        buckets = list(pd.unique(table["extension_bucket"]))

    fig, ax = plt.subplots(figsize=(max(8, len(regimes) * 1.3), 5))
    width = 0.8 / max(len(buckets), 1)
    x = np.arange(len(regimes) + 1)  # +1 for the ALL baseline group
    labels = ["ALL"] + regimes

    for i, bucket in enumerate(buckets):
        heights = []
        for label in labels:
            row = table[(table["regime"] == label) & (table["extension_bucket"] == bucket)]
            heights.append(row["pullback_rate"].iloc[0] * 100 if not row.empty else np.nan)
        ax.bar(x + i * width, heights, width=width, label=str(bucket))

    ax.set_xticks(x + width * (len(buckets) - 1) / 2)
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylabel(f"{pullback_label} rate (%)")
    ax.set_title(f"{pullback_label} rate by {extension_label} bucket, per regime")
    ax.legend(title=extension_label)
    ax.grid(True, alpha=0.3, axis="y")

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path
