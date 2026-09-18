"""
PULLBACK(threshold, horizon) label construction (RESEARCH_SPEC.md section
6): "Starting from the decision timestamp with reference price P, did the
future intraperiod low fall to <= P x (1 - threshold) at any point within
the next `horizon` days?"

RESEARCH-ONLY, like src/research/statistics/exploratory.py's
add_forward_return_for_research and src/regimes/analysis.py's
forward_min_return_for_research: these labels look at future data on
purpose (they ARE the future data). Never use a PULLBACK label as a
feature -- it's a training target, and only a target.

Two label variants are built, per RESEARCH_SPEC.md section 24's explicit
distinction:
  - intraperiod low (uses the `low` column): the formal PULLBACK
    definition -- did price ever trade down to the threshold, even
    briefly.
  - close-to-close (uses the `close` column): a stricter, less noisy
    variant -- did the market actually settle that low on some day's
    close, not just wick through it intraday.
Both are kept, distinctly named, never conflated (section 24's explicit
warning).
"""

from __future__ import annotations

import pandas as pd

DEFAULT_THRESHOLDS = (0.05, 0.075, 0.10, 0.125, 0.15, 0.20, 0.25)
DEFAULT_HORIZONS = (3, 7, 14, 30, 60, 90)


def forward_min_low_return(close: pd.Series, low: pd.Series, horizon: int) -> pd.Series:
    """
    For each row t, the return from close[t] to the LOWEST `low` observed
    over the next `horizon` days (t+1..t+horizon inclusive) -- the
    intraperiod worst-case, matching the formal PULLBACK definition.
    """
    future_low = low.shift(-1)
    reversed_future = future_low.iloc[::-1]
    rolling_min_reversed = reversed_future.rolling(horizon, min_periods=horizon).min()
    fwd_min_low = rolling_min_reversed.iloc[::-1]
    return fwd_min_low / close - 1


def forward_min_close_return(close: pd.Series, horizon: int) -> pd.Series:
    """
    Same idea, but using `close` instead of `low` -- the stricter
    close-to-close variant (section 24).
    """
    future_close = close.shift(-1)
    reversed_future = future_close.iloc[::-1]
    rolling_min_reversed = reversed_future.rolling(horizon, min_periods=horizon).min()
    fwd_min_close = rolling_min_reversed.iloc[::-1]
    return fwd_min_close / close - 1


def add_pullback_labels(
    df: pd.DataFrame,
    thresholds: tuple[float, ...] = DEFAULT_THRESHOLDS,
    horizons: tuple[int, ...] = DEFAULT_HORIZONS,
    variant: str = "intraperiod_low",
) -> pd.DataFrame:
    """
    Adds one boolean column per (threshold, horizon) combination, named
    `pullback_{threshold%}pct_{horizon}d`, e.g. `pullback_10pct_30d`.
    Also keeps the underlying forward-min-return column for each horizon
    (`_fwd_min_return_{horizon}d_{variant}`), since Milestone 8 (strategy)
    and later analysis may want the continuous value, not just the
    boolean.

    `variant`: "intraperiod_low" (default, the formal definition) or
    "close_to_close" (the stricter variant). Building both at once for
    the full threshold/horizon grid would double the column count for a
    distinction only a few analyses need -- call this twice with each
    variant if both are needed side by side.
    """
    if variant not in ("intraperiod_low", "close_to_close"):
        raise ValueError(f"Unknown variant: {variant!r}")

    out = df.copy()
    for horizon in horizons:
        if variant == "intraperiod_low":
            fwd_min_ret = forward_min_low_return(out["close"], out["low"], horizon)
        else:
            fwd_min_ret = forward_min_close_return(out["close"], horizon)

        fwd_col = f"_fwd_min_return_{horizon}d_{variant}"
        out[fwd_col] = fwd_min_ret

        for threshold in thresholds:
            label_col = f"pullback_{int(threshold * 100)}pct_{horizon}d"
            # `fwd_min_ret <= -threshold` on a NaN row silently evaluates
            # to False in plain bool comparison -- which would mislabel
            # "we don't have enough future data yet" as "no pullback
            # happened". Use the nullable boolean dtype and explicitly
            # mask those rows back to NA instead.
            label = (fwd_min_ret <= -threshold).astype("boolean")
            label = label.mask(fwd_min_ret.isna())
            out[label_col] = label

    return out
