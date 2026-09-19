"""
Tactical swing engine (RESEARCH_SPEC.md section 25-26, 52). Built
directly on the Milestone 7 finding: runup_from_low_365d was the most
reliable extension signal, and its relationship to pullback odds was
strongest and most consistent (agreed on by RSI, SMA-distance, AND
run-up together) specifically in LATE_BULL, with real (if noisier)
signal in BULL and DISTRIBUTION too.

CAUSALITY NOTE: Milestone 7's regime-conditional extension buckets were
computed with quantile cutoffs fit on the WHOLE dataset (including
future rows relative to any given day) -- correct for research
description, but not usable directly as a live signal (section 3, "no
look-ahead bias"). This module instead builds a rolling, POINT-IN-TIME
percentile: "how extended is today's runup_from_low_365d relative only
to its own trailing 365-day history" -- using
src/features/common.rolling_percentile_rank, the same causal building
block Milestone 4 used for volatility/volume percentiles.

State machine (per regime-day, only within TACTICAL_ELIGIBLE_REGIMES):
    FULL -> REDUCED   when extension_percentile >= EXTENSION_TRIGGER_PERCENTILE
    REDUCED -> FULL   when extension_percentile <= EXTENSION_REENTRY_PERCENTILE
                       (section 26: require the extension to have actually
                       normalized -- "stabilization" -- not just an
                       immediate re-entry on the first down day)
    Leaving a tactical-eligible regime entirely (e.g. BULL -> BEAR) forces
    the state back to FULL, since the reduction logic only makes sense
    while still in a regime where extension was shown to matter -- BEAR/
    ACCUMULATION/RECOVERY already have low core allocation from cycle.py,
    so there's no tactical layer to reduce there anyway.

EXTENSION_TRIGGER_PERCENTILE (0.80) and EXTENSION_REENTRY_PERCENTILE
(0.50) are stated guesses, not optimized values -- Phase 7 territory,
same caveat as cycle.py's CORE_ALLOCATION.
"""

from __future__ import annotations

import pandas as pd

from src.features.common import rolling_percentile_rank

EXTENSION_SOURCE_COL = "runup_from_low_365d"
EXTENSION_WINDOW = 365
EXTENSION_TRIGGER_PERCENTILE = 0.80
EXTENSION_REENTRY_PERCENTILE = 0.50
TACTICAL_MAX = 0.20
TACTICAL_ELIGIBLE_REGIMES = {"BULL", "LATE_BULL", "DISTRIBUTION"}


def add_extension_percentile(df: pd.DataFrame, source_col: str = EXTENSION_SOURCE_COL) -> pd.DataFrame:
    out = df.copy()
    out["extension_percentile"] = rolling_percentile_rank(out[source_col], EXTENSION_WINDOW)
    return out


def run_swing_engine(df: pd.DataFrame, regime_col: str = "regime") -> pd.DataFrame:
    """
    Sequential, stateful pass over the (already sorted ascending) rows.
    Adds `swing_state` ("FULL" or "REDUCED") and `tactical_allocation`
    (0.0 or TACTICAL_MAX, 0.0 outside TACTICAL_ELIGIBLE_REGIMES).

    A Python loop, not a vectorized operation -- deliberately, per
    RESEARCH_SPEC.md section 17's preference for an auditable, obviously-
    correct engine over cleverness, for a piece of logic that genuinely
    has state (unlike every prior milestone's feature/label columns,
    which were all pure functions of a row's own history).
    """
    out = add_extension_percentile(df)
    regimes = out[regime_col].tolist()
    extension = out["extension_percentile"].tolist()

    states: list[str | None] = []
    tactical: list[float] = []
    state = "FULL"

    for regime, ext in zip(regimes, extension):
        if regime is None or (isinstance(regime, float) and pd.isna(regime)) or pd.isna(ext):
            states.append(None)
            tactical.append(float("nan"))
            continue

        eligible = regime in TACTICAL_ELIGIBLE_REGIMES
        if not eligible:
            state = "FULL"  # leaving an eligible regime resets the tactical state
            states.append(state)
            tactical.append(0.0)
            continue

        if state == "FULL" and ext >= EXTENSION_TRIGGER_PERCENTILE:
            state = "REDUCED"
        elif state == "REDUCED" and ext <= EXTENSION_REENTRY_PERCENTILE:
            state = "FULL"

        states.append(state)
        tactical.append(0.0 if state == "REDUCED" else TACTICAL_MAX)

    out["swing_state"] = states
    out["tactical_allocation"] = tactical
    return out
