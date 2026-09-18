"""
Phase 3 analysis: does the regime label from classifier.py actually carry
information? (RESEARCH_SPEC.md section 27, "Does knowing the current
regime provide useful information?")

Three things are checked here, deliberately in this order:
1. Persistence (regime_segment_stats) -- if regimes flip every few days,
   the label is noise, not a market state, regardless of what the
   forward-return numbers say.
2. Transition structure (regime_transition_matrix) -- a sanity check on
   how "sticky" each regime is day to day.
3. The actual question (regime_conditional_stats) -- forward return and
   pullback-probability statistics broken out BY regime, with an 'ALL'
   (unconditional) row included for direct comparison. This is what
   Milestone 5's flat, unconditional extension-vs-return table was
   missing.

forward_min_return_for_research below is, like Milestone 5's
add_forward_return_for_research, RESEARCH-ONLY: it looks at future data
on purpose to describe what happened, and must never be used as a live
feature. Kept in this module rather than src/regimes/classifier.py to
keep that boundary visible.
"""

from __future__ import annotations

import pandas as pd

from src.regimes.definitions import REGIME_ORDER
from src.research.statistics.exploratory import add_forward_return_for_research


def forward_min_return_for_research(close: pd.Series, horizon: int) -> pd.Series:
    """
    For each row t, the return to the LOWEST close over the next
    `horizon` days (t+1 .. t+horizon inclusive), i.e. the worst-case
    forward drawdown an entry at t would have experienced within that
    window. Research-only -- see module docstring.
    """
    future = close.shift(-1)
    reversed_future = future.iloc[::-1]
    rolling_min_reversed = reversed_future.rolling(horizon, min_periods=horizon).min()
    forward_min_close = rolling_min_reversed.iloc[::-1]
    return forward_min_close / close - 1


def regime_segment_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Groups consecutive same-regime rows into segments and summarizes
    persistence per regime: how many segments, how long they typically
    last, and what fraction of all classified days each regime covers.
    Rows with regime=None (warmup) are excluded first.
    """
    d = df.dropna(subset=["regime"]).copy()
    if d.empty:
        return pd.DataFrame(
            columns=["regime", "n_segments", "avg_duration_days", "median_duration_days", "total_days", "pct_of_classified_days"]
        )

    d["segment_id"] = (d["regime"] != d["regime"].shift()).cumsum()
    segments = d.groupby("segment_id").agg(regime=("regime", "first"), n_days=("regime", "size"))

    summary = segments.groupby("regime").agg(
        n_segments=("n_days", "count"),
        avg_duration_days=("n_days", "mean"),
        median_duration_days=("n_days", "median"),
        total_days=("n_days", "sum"),
    )
    summary["pct_of_classified_days"] = summary["total_days"] / summary["total_days"].sum()
    summary = summary.reindex(REGIME_ORDER).dropna(how="all").reset_index().rename(columns={"index": "regime"})
    return summary


def regime_transition_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Day-to-day transition probabilities: P(regime[t+1] = col | regime[t] = row).
    A high diagonal value means that regime is sticky (persists day to
    day); a low diagonal value means the label is flickering.
    """
    d = df.dropna(subset=["regime"]).copy()
    d["next_regime"] = d["regime"].shift(-1)
    d = d.dropna(subset=["next_regime"])

    if d.empty:
        return pd.DataFrame(index=REGIME_ORDER, columns=REGIME_ORDER)

    counts = d.groupby(["regime", "next_regime"]).size().unstack(fill_value=0)
    counts = counts.reindex(index=REGIME_ORDER, columns=REGIME_ORDER, fill_value=0)
    row_sums = counts.sum(axis=1)
    probs = counts.div(row_sums.where(row_sums != 0, 1), axis=0)
    return probs


def regime_conditional_stats(
    df: pd.DataFrame, horizon: int, pullback_thresholds: tuple[float, ...] = (0.10, 0.20)
) -> pd.DataFrame:
    """
    The core Phase 3 output: for each regime (plus an 'ALL' unconditional
    baseline row), the mean/median/std forward return over `horizon` days
    and the fraction of observations that saw at least a
    `pullback_thresholds`-sized decline within that window.

    This is what should be compared against Milestone 5's flat,
    unconditional extension-vs-forward-return table: if a regime's row
    here looks meaningfully different from 'ALL', the regime label is
    adding information Milestone 5's unconditional view couldn't see.
    """
    d = df.copy()
    fwd_ret_col = f"_fwd_return_{horizon}d"
    fwd_min_col = f"_fwd_min_return_{horizon}d"
    d[fwd_ret_col] = add_forward_return_for_research(d, horizon)
    d[fwd_min_col] = forward_min_return_for_research(d["close"], horizon)

    d = d.dropna(subset=["regime", fwd_ret_col, fwd_min_col])

    groups = [("ALL", d)] + list(d.groupby("regime"))
    rows = []
    for label, group in groups:
        row = {
            "regime": label,
            "n": len(group),
            "mean_forward_return": group[fwd_ret_col].mean(),
            "median_forward_return": group[fwd_ret_col].median(),
            "std_forward_return": group[fwd_ret_col].std(),
        }
        for th in pullback_thresholds:
            row[f"pct_with_pullback_ge_{int(th * 100)}pct"] = (group[fwd_min_col] <= -th).mean()
        rows.append(row)

    return pd.DataFrame(rows)
