"""Chart for walk-forward results: CAGR per window, strategy vs benchmark,
with the most recent (least-tested) window visually flagged."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_walk_forward_windows(merged: pd.DataFrame, out_path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(12, 5))

    labels = [f"{r.window_start.date()}\n->{r.window_end.date()}" for r in merged.itertuples()]
    x = np.arange(len(merged))
    width = 0.35

    ax.bar(x - width / 2, merged["cagr_strategy"] * 100, width, label="Cycle Only", color="tab:blue")
    ax.bar(x + width / 2, merged["cagr_benchmark"] * 100, width, label="Buy & Hold", color="tab:orange")
    ax.axhline(0, color="black", linewidth=0.8)

    for i, is_recent in enumerate(merged["is_most_recent_strategy"]):
        if is_recent:
            ax.axvspan(i - 0.5, i + 0.5, color="red", alpha=0.08)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("CAGR (%)")
    ax.set_title("Walk-forward: CAGR per window (red shading = most recent window)")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path
