# Phase 3 Cycle / Regime Research

Regime definitions are a first-pass research hypothesis (RESEARCH_SPEC.md section 5 / src/regimes/definitions.py) -- this report is exactly the test of whether they carry information.

## Regime persistence
If a regime's avg_duration_days is only a few days, the label is flickering, not describing a real market state.
| regime | n_segments | avg_duration_days | median_duration_days | total_days | pct_of_classified_days |
|---|---|---|---|---|---|
| BEAR | 48 | 18.7292 | 8.0000 | 899 | 0.2317 |
| ACCUMULATION | 26 | 6.8846 | 2.0000 | 179 | 0.0461 |
| EARLY_RECOVERY | 23 | 10.0000 | 4.0000 | 230 | 0.0593 |
| LATE_RECOVERY | 27 | 7.1111 | 3.0000 | 192 | 0.0495 |
| BULL | 116 | 12.7672 | 5.0000 | 1481 | 0.3817 |
| LATE_BULL | 54 | 5.7037 | 3.0000 | 308 | 0.0794 |
| DISTRIBUTION | 74 | 7.9865 | 3.0000 | 591 | 0.1523 |

## Day-to-day transition matrix
Rows = today's regime, columns = tomorrow's regime. Diagonal = stickiness.
| from \ to | BEAR | ACCUMULATION | EARLY_RECOVERY | LATE_RECOVERY | BULL | LATE_BULL | DISTRIBUTION |
|---|---|---|---|---|---|---|---|
| BEAR | 0.9470 | 0.0030 | 0.0240 | 0.0170 | 0.0010 | 0.0000 | 0.0080 |
| ACCUMULATION | 0.0280 | 0.8550 | 0.0000 | 0.0390 | 0.0220 | 0.0000 | 0.0560 |
| EARLY_RECOVERY | 0.0780 | 0.0000 | 0.9000 | 0.0000 | 0.0220 | 0.0000 | 0.0000 |
| LATE_RECOVERY | 0.0680 | 0.0310 | 0.0000 | 0.8590 | 0.0310 | 0.0100 | 0.0000 |
| BULL | 0.0010 | 0.0020 | 0.0010 | 0.0020 | 0.9220 | 0.0350 | 0.0370 |
| LATE_BULL | 0.0000 | 0.0000 | 0.0000 | 0.0060 | 0.1660 | 0.8250 | 0.0030 |
| DISTRIBUTION | 0.0190 | 0.0240 | 0.0000 | 0.0000 | 0.0830 | 0.0000 | 0.8750 |

## Chart
![Price with regimes](figures/price_with_regimes.png)

## Regime-conditional forward returns and pullback probability

Compare each regime's row against the 'ALL' (unconditional) row. If they don't look meaningfully different, this regime scheme isn't adding information over just looking at the whole series -- that's a valid, useful research conclusion, not a failure.

### 14-day forward horizon
| regime | n | mean_forward_return | median_forward_return | std_forward_return | pct_with_pullback_ge_10pct | pct_with_pullback_ge_20pct |
|---|---|---|---|---|---|---|
| ALL | 3866 | 0.0288 | 0.0142 | 0.1421 | 0.2212 | 0.0618 |
| ACCUMULATION | 179 | 0.0174 | 0.0164 | 0.1144 | 0.1899 | 0.0615 |
| BEAR | 899 | 0.0075 | 0.0063 | 0.1250 | 0.2303 | 0.0712 |
| BULL | 1467 | 0.0452 | 0.0186 | 0.1440 | 0.1854 | 0.0423 |
| DISTRIBUTION | 591 | 0.0061 | 0.0015 | 0.1305 | 0.2792 | 0.0846 |
| EARLY_RECOVERY | 230 | 0.0089 | 0.0097 | 0.1551 | 0.3391 | 0.1087 |
| LATE_BULL | 308 | 0.0868 | 0.0470 | 0.1939 | 0.2078 | 0.0779 |
| LATE_RECOVERY | 192 | 0.0143 | 0.0048 | 0.1010 | 0.1823 | 0.0156 |

### 30-day forward horizon
| regime | n | mean_forward_return | median_forward_return | std_forward_return | pct_with_pullback_ge_10pct | pct_with_pullback_ge_20pct |
|---|---|---|---|---|---|---|
| ALL | 3850 | 0.0650 | 0.0284 | 0.2334 | 0.3553 | 0.1499 |
| ACCUMULATION | 179 | 0.0245 | 0.0129 | 0.1573 | 0.2849 | 0.1341 |
| BEAR | 899 | 0.0227 | 0.0181 | 0.1797 | 0.3571 | 0.1524 |
| BULL | 1451 | 0.1012 | 0.0358 | 0.2719 | 0.3349 | 0.1103 |
| DISTRIBUTION | 591 | 0.0377 | 0.0291 | 0.2203 | 0.4129 | 0.1946 |
| EARLY_RECOVERY | 230 | 0.0374 | -0.0377 | 0.2110 | 0.4609 | 0.2565 |
| LATE_BULL | 308 | 0.1467 | 0.1106 | 0.2377 | 0.2857 | 0.1461 |
| LATE_RECOVERY | 192 | 0.0129 | 0.0167 | 0.1751 | 0.3750 | 0.1927 |

### 90-day forward horizon
| regime | n | mean_forward_return | median_forward_return | std_forward_return | pct_with_pullback_ge_10pct | pct_with_pullback_ge_20pct |
|---|---|---|---|---|---|---|
| ALL | 3790 | 0.2246 | 0.0938 | 0.5514 | 0.5554 | 0.3430 |
| ACCUMULATION | 179 | 0.0890 | 0.0409 | 0.3303 | 0.5419 | 0.4972 |
| BEAR | 870 | 0.0625 | -0.0012 | 0.3382 | 0.6195 | 0.3575 |
| BULL | 1450 | 0.3284 | 0.2276 | 0.5723 | 0.5000 | 0.2469 |
| DISTRIBUTION | 591 | 0.2199 | 0.0391 | 0.6886 | 0.6007 | 0.3909 |
| EARLY_RECOVERY | 230 | 0.2497 | -0.0801 | 0.6082 | 0.6261 | 0.5261 |
| LATE_BULL | 308 | 0.3967 | 0.2003 | 0.5946 | 0.4221 | 0.2987 |
| LATE_RECOVERY | 162 | -0.0299 | -0.1604 | 0.3869 | 0.7099 | 0.6049 |
