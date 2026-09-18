"""
Chart generation for Phase 2 exploratory research (RESEARCH_SPEC.md
section 45). Every function takes a DataFrame and an output path, saves a
PNG, and returns the path -- no interactive display (headless Agg
backend), since this runs from a script/CI context, not a notebook
kernel.

Per RESEARCH_SPEC.md section 45: "Avoid charts that merely make the
strategy look good. Visualization should be used for analysis." None of
these charts involve a strategy at all yet (Phase 2 precedes any strategy
logic) -- they describe the raw data and the preliminary extension/
pullback relationship only.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def plot_price_and_drawdown(df: pd.DataFrame, out_path: Path) -> Path:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True, gridspec_kw={"height_ratios": [2, 1]})

    ax1.plot(df["timestamp"], df["close"], linewidth=0.8, color="tab:blue")
    ax1.set_yscale("log")
    ax1.set_ylabel("Close (log scale)")
    ax1.set_title("BTC-USD close price and drawdown from running all-time-high")
    ax1.grid(True, alpha=0.3)

    ax2.fill_between(df["timestamp"], df["drawdown_from_ath"] * 100, 0, color="tab:red", alpha=0.5)
    ax2.set_ylabel("Drawdown from ATH (%)")
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def plot_rolling_volatility(df: pd.DataFrame, out_path: Path, col: str = "realized_vol_30d") -> Path:
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(df["timestamp"], df[col] * 100, linewidth=0.8, color="tab:purple")
    ax.set_ylabel(f"{col} (annualized, %)")
    ax.set_title(f"Rolling realized volatility ({col})")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def plot_return_distribution(df: pd.DataFrame, out_path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 5))
    returns = df["return_1d"].dropna() * 100
    ax.hist(returns, bins=100, color="tab:blue", alpha=0.8)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Daily return (%)")
    ax.set_ylabel("Count")
    ax.set_title("Distribution of daily returns")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def plot_extension_vs_forward_return(
    binned: pd.DataFrame, out_path: Path, extension_label: str, horizon_label: str
) -> Path:
    """`binned` is the output of exploratory.extension_vs_forward_return."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(binned["decile"], binned["return_mean"] * 100, color="tab:orange", alpha=0.85)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel(f"{extension_label} decile (0=lowest, 9=highest)")
    ax.set_ylabel(f"Mean {horizon_label} (%)")
    ax.set_title(f"{horizon_label} by {extension_label} decile")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path
