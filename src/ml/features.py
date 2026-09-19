"""
Feature matrix construction for the Milestone 12 ML baseline
(RESEARCH_SPEC.md section 32, "start with interpretable features").

Reuses columns already present in the Milestone 4/7 labeled dataset --
nothing new is computed here, this module only selects and encodes.
Every column selected is a Milestone 4 causal feature (no future data),
plus the Milestone 6 regime label (also causal -- computed from only
past/present data at each row).
"""

from __future__ import annotations

import pandas as pd

NUMERIC_FEATURE_COLS = [
    "rsi_14",
    "dist_from_sma_50",
    "dist_from_sma_200",
    "atr_pct_14",
    "realized_vol_30d",
    "runup_from_low_365d",
    "volume_ratio_20",
    "drawdown_from_ath",
]

REGIME_CATEGORIES = ["BEAR", "ACCUMULATION", "EARLY_RECOVERY", "LATE_RECOVERY", "BULL", "LATE_BULL", "DISTRIBUTION"]


def build_feature_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Returns (X, feature_names). X has one column per NUMERIC_FEATURE_COLS
    entry plus one one-hot column per regime category
    (`regime_is_<REGIME>`). Rows where regime is null get all-zero regime
    columns (no category selected) -- those rows should be dropped by the
    caller before fitting anyway (Milestone 4 warmup), this just avoids a
    KeyError rather than silently guessing a regime.
    """
    X = df[NUMERIC_FEATURE_COLS].copy()

    for regime in REGIME_CATEGORIES:
        X[f"regime_is_{regime}"] = (df["regime"] == regime).astype(float)

    feature_names = NUMERIC_FEATURE_COLS + [f"regime_is_{r}" for r in REGIME_CATEGORIES]
    return X, feature_names
