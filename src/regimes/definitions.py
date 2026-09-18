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

Rule table (first match wins, evaluated in this order):

| Order | Regime       | Condition                                                              |
|-------|--------------|-------------------------------------------------------------------------|
| 1     | LATE_BULL    | close > sma_50 > 0, close > sma_200, rsi_14 >= 75, drawdown_from_ath >= -15% |
| 2     | BULL         | close > sma_50, close > sma_200 (and not LATE_BULL)                    |
| 3     | DISTRIBUTION | close < sma_50, close > sma_200                                        |
| 4     | BEAR         | close < sma_50, close < sma_200, drawdown_from_ath <= -35%              |
| 5     | RECOVERY     | close > sma_50, close < sma_200                                        |
| 6     | ACCUMULATION | close < sma_50, close < sma_200, drawdown_from_ath > -35% (fallback)    |

Rows where sma_50, sma_200, rsi_14, or drawdown_from_ath is NaN (the
Milestone 4 rolling-window warmup period) are unclassified (regime=None),
not silently assigned a default.
"""

from __future__ import annotations

LATE_BULL_RSI_THRESHOLD = 75.0
LATE_BULL_MAX_DRAWDOWN = -0.15  # drawdown must be shallower than this (closer to 0)
BEAR_MAX_DRAWDOWN = -0.35  # drawdown must be at or below this (deeper) to count as BEAR

REGIME_ORDER = ["BEAR", "ACCUMULATION", "RECOVERY", "BULL", "LATE_BULL", "DISTRIBUTION"]

REQUIRED_COLUMNS = ["close", "sma_50", "sma_200", "drawdown_from_ath", "rsi_14"]
