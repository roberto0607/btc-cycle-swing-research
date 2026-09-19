"""Chart for the Milestone 8 strategy signal: price with total allocation
overlaid, so it's visually obvious whether the strategy is actually
reducing exposure around the extended/topping periods it's supposed to."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def plot_price_and_allocation(df: pd.DataFrame, out_path: Path) -> Path:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), sharex=True, gridspec_kw={"height_ratios": [2, 1]})

    ax1.plot(df["timestamp"], df["close"], color="black", linewidth=0.6)
    ax1.set_yscale("log")
    ax1.set_ylabel("Close (log scale)")
    ax1.set_title("BTC-USD close price and Milestone 8 strategy total allocation")
    ax1.grid(True, alpha=0.3)

    ax2.fill_between(df["timestamp"], df["total_allocation"] * 100, 0, color="tab:green", alpha=0.5, step="post")
    ax2.set_ylabel("Total allocation (%)")
    ax2.set_ylim(0, 100)
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path
