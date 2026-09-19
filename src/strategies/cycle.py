"""
Cycle allocation engine (RESEARCH_SPEC.md section 27, 52): maps the
current regime (Milestone 6) to a target CORE BTC allocation -- the
persistent, non-tactical portion of exposure.

These targets are a FIRST-PASS RESEARCH HYPOTHESIS, derived qualitatively
from the Milestone 6 regime-conditional forward-return/pullback-odds
ranking, NOT an optimized or backtested parameter set. Per
RESEARCH_SPEC.md section 49, treat CORE_ALLOCATION as a parameter region
to sweep in Phase 7 (robustness), not a locked-in value -- Milestone 9
(backtester) is what will actually tell us if these numbers are any good.

Ranking logic (higher core = regime showed better mean/median forward
returns and lower pullback odds in the Milestone 6 report):
    BEAR            0%  -- worst regime by every metric in the M6 report
    ACCUMULATION   40%  -- basing after a decline, unconfirmed
    EARLY_RECOVERY 30%  -- M6 finding: still elevated pullback risk despite the bounce
    LATE_RECOVERY  60%  -- closer to reclaiming highs, better odds in M6 (with the
                           sample-concentration caveat noted in that report)
    BULL           70%  -- healthy uptrend, core exposure
    LATE_BULL      70%  -- same core as BULL; M7 showed LATE_BULL's *tactical* risk
                           is real, so the reduction happens via swing.py, not here
    DISTRIBUTION   50%  -- rolling over, reduce core ahead of confirmed downtrend
"""

from __future__ import annotations

import pandas as pd

CORE_ALLOCATION: dict[str, float] = {
    "BEAR": 0.0,
    "ACCUMULATION": 0.40,
    "EARLY_RECOVERY": 0.30,
    "LATE_RECOVERY": 0.60,
    "BULL": 0.70,
    "LATE_BULL": 0.70,
    "DISTRIBUTION": 0.50,
}


def core_allocation_for_regime(regime: str | None) -> float:
    """Returns NaN for an unclassified (None/NaN) regime -- the Milestone
    4 feature warmup period -- rather than defaulting to some allocation
    with no basis."""
    if regime is None or (isinstance(regime, float) and pd.isna(regime)):
        return float("nan")
    if regime not in CORE_ALLOCATION:
        raise ValueError(f"Unknown regime: {regime!r}")
    return CORE_ALLOCATION[regime]


def add_core_allocation(df: pd.DataFrame, regime_col: str = "regime") -> pd.DataFrame:
    out = df.copy()
    out["core_allocation"] = out[regime_col].apply(core_allocation_for_regime)
    return out
