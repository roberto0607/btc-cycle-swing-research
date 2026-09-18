"""
Price-with-regime chart (RESEARCH_SPEC.md section 45: "BTC price +
background regime"). Kept in src/regimes/ rather than
src/research/statistics/charts.py because it depends on the `regime`
column classifier.py produces -- src/research/statistics/ stays regime-
agnostic.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.regimes.definitions import REGIME_ORDER

REGIME_COLORS = {
    "BEAR": "#8b0000",
    "ACCUMULATION": "#d4a017",
    "RECOVERY": "#4682b4",
    "BULL": "#2e8b57",
    "LATE_BULL": "#98fb98",
    "DISTRIBUTION": "#ff8c00",
}


def plot_price_with_regimes(df: pd.DataFrame, out_path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(df["timestamp"], df["close"], color="black", linewidth=0.6, zorder=3)
    ax.set_yscale("log")
    ax.set_ylabel("Close (log scale)")
    ax.set_title("BTC-USD close price with classified regime background")

    d = df.dropna(subset=["regime"]).reset_index(drop=True)
    if not d.empty:
        d["segment_id"] = (d["regime"] != d["regime"].shift()).cumsum()
        for _, seg in d.groupby("segment_id"):
            regime = seg["regime"].iloc[0]
            ax.axvspan(
                seg["timestamp"].iloc[0],
                seg["timestamp"].iloc[-1],
                color=REGIME_COLORS.get(regime, "gray"),
                alpha=0.25,
                zorder=1,
            )

    handles = [plt.Rectangle((0, 0), 1, 1, color=REGIME_COLORS[r], alpha=0.5) for r in REGIME_ORDER]
    ax.legend(handles, REGIME_ORDER, loc="upper left", fontsize=8, ncol=3)
    ax.grid(True, alpha=0.3, zorder=0)

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path
