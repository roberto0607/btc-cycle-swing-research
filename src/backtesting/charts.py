"""Equity curve chart (RESEARCH_SPEC.md section 45: "Strategy equity
curve: Buy & Hold vs Cycle vs Cycle + Swing")."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def plot_equity_curves(curves: dict[str, pd.Series], out_path: Path) -> Path:
    """`curves` maps a label to a portfolio-value Series (same index).
    Each is normalized to start at 100 so they're comparable regardless
    of initial capital."""
    fig, ax = plt.subplots(figsize=(13, 6))

    for label, series in curves.items():
        normalized = series / series.iloc[0] * 100
        ax.plot(series.index, normalized, label=label, linewidth=1.0)

    ax.set_yscale("log")
    ax.set_ylabel("Portfolio value (indexed to 100, log scale)")
    ax.set_title("Strategy vs benchmarks -- equity curves (baseline cost scenario)")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path
