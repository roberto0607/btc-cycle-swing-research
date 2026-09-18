"""
Descriptive statistics for Phase 2 exploratory research (RESEARCH_SPEC.md
Phase 2: "investigate BTC behavior... generate charts and statistical
summaries. Do not optimize strategy parameters yet.").

Nothing here fits a model or picks a strategy parameter -- it only
describes what the data looks like. Everything operates on the feature
table from Milestone 4 (data/features/coinbase_btc_usd_1d_features.parquet),
which is already causal, so no additional leakage risk is introduced by
these read-only descriptive functions -- but note some of them (e.g.
drawdown episode detection) look at data AFTER a given point in time on
purpose, which is fine for research description but must never be fed
back in as a live-decision feature (see RESEARCH_SPEC.md section 27-28 on
research-only vs live-decision use of future information).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 365  # BTC trades every calendar day


def summarize_returns(df: pd.DataFrame) -> dict:
    """
    Whole-series descriptive stats on daily returns and the running
    drawdown-from-ATH series already computed in Milestone 4.
    """
    returns = df["return_1d"].dropna()
    close = df["close"]
    n_days = len(df)
    n_years = n_days / TRADING_DAYS_PER_YEAR

    total_return = close.iloc[-1] / close.iloc[0] - 1
    cagr = (close.iloc[-1] / close.iloc[0]) ** (1 / n_years) - 1 if n_years > 0 else float("nan")
    ann_vol = returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    max_drawdown = df["drawdown_from_ath"].min()

    return {
        "start_date": df["timestamp"].iloc[0],
        "end_date": df["timestamp"].iloc[-1],
        "n_days": n_days,
        "n_years": round(n_years, 2),
        "total_return": total_return,
        "cagr": cagr,
        "annualized_volatility": ann_vol,
        "max_drawdown": max_drawdown,
        "best_day": returns.max(),
        "worst_day": returns.min(),
        "skew": returns.skew(),
        "kurtosis": returns.kurt(),
    }


def yearly_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Per-calendar-year return, annualized volatility, and max drawdown
    (drawdown computed fresh within each year, not the whole-series
    running drawdown -- a year's own worst point relative to its own
    start, for readability)."""
    d = df.copy()
    d["year"] = pd.to_datetime(d["timestamp"]).dt.year

    rows = []
    for year, g in d.groupby("year"):
        year_start = g["close"].iloc[0]
        year_end = g["close"].iloc[-1]
        year_return = year_end / year_start - 1
        ann_vol = g["return_1d"].dropna().std() * np.sqrt(TRADING_DAYS_PER_YEAR)
        running_max = g["close"].cummax()
        year_dd = ((g["close"] - running_max) / running_max).min()
        rows.append(
            {
                "year": year,
                "return": year_return,
                "annualized_volatility": ann_vol,
                "max_drawdown_within_year": year_dd,
            }
        )
    return pd.DataFrame(rows)


@dataclass
class DrawdownEpisode:
    peak_date: pd.Timestamp
    trough_date: pd.Timestamp
    recovery_date: pd.Timestamp | None  # None = still underwater as of last row
    depth: float  # most negative value, e.g. -0.83
    days_peak_to_trough: int
    days_trough_to_recovery: int | None


def find_drawdown_episodes(df: pd.DataFrame) -> list[DrawdownEpisode]:
    """
    Identifies every drawdown episode using the already-computed
    `drawdown_from_ath` column (Milestone 4). A "peak" is any row where
    drawdown_from_ath == 0 (today's close is a new running all-time high,
    by construction of that causal expanding-max feature). Between
    consecutive peaks, the trough is the row with the most negative
    drawdown; recovery is the next peak (drawdown returns to exactly 0).
    The final episode (from the last peak to the end of the series) has
    recovery_date=None if the series ends still underwater.
    """
    dd = df["drawdown_from_ath"].to_numpy()
    dates = pd.to_datetime(df["timestamp"]).to_numpy()

    peak_idx = np.where(dd >= -1e-12)[0]
    if len(peak_idx) < 1:
        return []

    episodes: list[DrawdownEpisode] = []
    for i in range(len(peak_idx)):
        start = peak_idx[i]
        end = peak_idx[i + 1] if i + 1 < len(peak_idx) else len(dd) - 1
        segment = dd[start:end + 1]
        if len(segment) <= 1:
            continue  # no drawdown occurred before the next peak

        trough_offset = int(np.argmin(segment))
        trough_idx = start + trough_offset
        depth = float(segment[trough_offset])
        if depth >= -1e-12:
            continue  # never actually went negative in this window

        is_last_segment = i + 1 >= len(peak_idx)
        recovered = not is_last_segment  # if there's a next peak, we recovered by definition

        episodes.append(
            DrawdownEpisode(
                peak_date=pd.Timestamp(dates[start]),
                trough_date=pd.Timestamp(dates[trough_idx]),
                recovery_date=pd.Timestamp(dates[end]) if recovered else None,
                depth=depth,
                days_peak_to_trough=int(trough_idx - start),
                days_trough_to_recovery=int(end - trough_idx) if recovered else None,
            )
        )
    return episodes


def top_drawdowns(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    episodes = find_drawdown_episodes(df)
    rows = [
        {
            "peak_date": e.peak_date,
            "trough_date": e.trough_date,
            "recovery_date": e.recovery_date if e.recovery_date is not None else "ONGOING",
            "depth": e.depth,
            "days_peak_to_trough": e.days_peak_to_trough,
            "days_trough_to_recovery": e.days_trough_to_recovery
            if e.days_trough_to_recovery is not None
            else "N/A",
        }
        for e in episodes
    ]
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values("depth").head(n).reset_index(drop=True)


def add_forward_return_for_research(df: pd.DataFrame, horizon: int) -> pd.Series:
    """
    Forward N-day return: close[t+horizon] / close[t] - 1.

    DELIBERATELY NOT part of src/features/ -- this uses FUTURE data
    relative to row t and must never be used as a live-decision input.
    It exists only to answer research questions like "does today's
    extension predict what happens over the next N days" (RESEARCH_SPEC.md
    section 46). If this ever needs to become a model target rather than
    an EDA aid, it becomes a formal label under the PULLBACK(threshold,
    horizon) definition in RESEARCH_SPEC.md section 6, not this ad-hoc
    version -- keep the two uses (rough EDA vs formal ML target) visibly
    distinct so nobody accidentally trains on this helper's output later.
    """
    return df["close"].shift(-horizon) / df["close"] - 1


def extension_vs_forward_return(
    df: pd.DataFrame, extension_col: str, horizon_col: str
) -> pd.DataFrame:
    """
    Bins `extension_col` into deciles and reports the mean/median of
    `horizon_col` (a forward N-day return column, e.g. shifted appropriately
    upstream) within each decile. `horizon_col` must already be a
    forward-looking value if the caller wants a forward look -- this
    function does no shifting itself, it only aggregates, to keep the
    look-ahead-bias risk localized and explicit at the call site rather
    than hidden in a generic stats helper.
    """
    d = df[[extension_col, horizon_col]].dropna()
    if d.empty:
        return pd.DataFrame(columns=["decile", "extension_mean", "n", "return_mean", "return_median"])

    d = d.copy()
    d["decile"] = pd.qcut(d[extension_col], 10, labels=False, duplicates="drop")

    grouped = d.groupby("decile").agg(
        extension_mean=(extension_col, "mean"),
        n=(extension_col, "size"),
        return_mean=(horizon_col, "mean"),
        return_median=(horizon_col, "median"),
    ).reset_index()
    return grouped
