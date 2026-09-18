"""
Candidate regime definitions (RESEARCH_SPEC.md section 5).

These are a FIRST-PASS RESEARCH HYPOTHESIS, not assumed ground truth --
the whole point of Milestone 6 is to test whether this particular
regime scheme actually carries information (see analysis.py). If it
doesn't, the right conclusion is "this regime definition didn't help",
not "force it to matter."

All inputs are already-causal features from Milestone 4
(sma_50, sma_200, drawdown_from_ath, rsi_14) -- nothing here looks at
future data. See classifier.py for how these thresholds combine into a
label.

CORRECTED 2026-09-18: the original single RECOVERY label (close > sma_50,
close < sma_200) turned out to conflate two very different situations, as
the Milestone 6 regime-conditional report showed once real data was run
through it -- RECOVERY's median 90-day forward return was NEGATIVE (-11.7%)
despite a positive mean (+13.4%), and it had the highest 20%+-pullback odds
of any regime (55.9%). That combination (mean >> median, high downside
tail) is the fingerprint of a "dead-cat bounce" pattern getting averaged
together with genuine bottoms into one label. Split on drawdown_from_ath,
which distinguishes "still deep in a bear market, bouncing" from "close to
actually reclaiming the old highs":

Rule table (first match wins, evaluated in this order):

| Order | Regime         | Condition                                                              |
|-------|----------------|-------------------------------------------------------------------------|
| 1     | LATE_BULL      | close > sma_50 > 0, close > sma_200, rsi_14 >= 75, drawdown_from_ath >= -15% |
| 2     | BULL           | close > sma_50, close > sma_200 (and not LATE_BULL)                    |
| 3     | DISTRIBUTION   | close < sma_50, close > sma_200                                        |
| 4     | BEAR           | close < sma_50, close < sma_200, drawdown_from_ath <= -35%              |
| 5     | EARLY_RECOVERY | close > sma_50, close < sma_200, drawdown_from_ath <= -50%              |
| 6     | LATE_RECOVERY  | close > sma_50, close < sma_200, drawdown_from_ath > -50%               |
| 7     | ACCUMULATION   | close < sma_50, close < sma_200, drawdown_from_ath > -35% (fallback)    |

EARLY_RECOVERY_MAX_DRAWDOWN (-50%) is itself a guess, stated as one --
per RESEARCH_SPEC.md section 49, this is a parameter region to search
later against an actual backtest, not a value to treat as settled. If the
regime-conditional report doesn't show a clean separation between
EARLY_RECOVERY and LATE_RECOVERY at -50%, try -40% or -60% by hand before
building any formal sweep.

Rows where sma_50, sma_200, rsi_14, or drawdown_from_ath is NaN (the
Milestone 4 rolling-window warmup period) are unclassified (regime=None),
not silently assigned a default.
"""

from __future__ import annotations

LATE_BULL_RSI_THRESHOLD = 75.0
LATE_BULL_MAX_DRAWDOWN = -0.15  # drawdown must be shallower than this (closer to 0)
BEAR_MAX_DRAWDOWN = -0.35  # drawdown must be at or below this (deeper) to count as BEAR
EARLY_RECOVERY_MAX_DRAWDOWN = -0.50  # drawdown must be at or below this to count as EARLY (still deep)

REGIME_ORDER = [
    "BEAR",
    "ACCUMULATION",
    "EARLY_RECOVERY",
    "LATE_RECOVERY",
    "BULL",
    "LATE_BULL",
    "DISTRIBUTION",
]

REQUIRED_COLUMNS = ["close", "sma_50", "sma_200", "drawdown_from_ath", "rsi_14"]
