"""Chart for robustness.parameter_perturbation -- CAGR and max drawdown
across the allocation-scale sweep, so a plateau vs. an isolated peak is
visible at a glance."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def plot_parameter_perturbation(table: pd.DataFrame, out_path: Path) -> Path:
    fig, ax1 = plt.subplots(figsize=(9, 5))

    ax1.plot(table["scale_factor"], table["cagr"] * 100, marker="o", color="tab:blue", label="CAGR (%)")
    ax1.set_xlabel("Core allocation scale factor (1.0 = unperturbed)")
    ax1.set_ylabel("CAGR (%)", color="tab:blue")
    ax1.axvline(1.0, color="gray", linestyle="--", linewidth=0.8)
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(table["scale_factor"], table["max_drawdown"] * 100, marker="s", color="tab:red", label="Max Drawdown (%)")
    ax2.set_ylabel("Max Drawdown (%)", color="tab:red")

    ax1.set_title("Parameter perturbation: does performance hold across a region?")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path
