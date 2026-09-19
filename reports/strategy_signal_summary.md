# Phase 5 Deterministic Strategy Signal

Core allocation by regime (src/strategies/cycle.py) and tactical swing overlay (src/strategies/swing.py) -- both first-pass hypotheses per their module docstrings, not optimized parameters. No backtest yet; this is target allocation only (Phase 5, before Phase 6's backtester).

## Allocation by regime
| regime | n_days | avg_core | avg_tactical | avg_total |
|---|---|---|---|---|
| ACCUMULATION | 179 | 0.4000 | 0.0000 | 0.4000 |
| BEAR | 899 | 0.0000 | 0.0000 | 0.0000 |
| BULL | 1481 | 0.7000 | 0.0828 | 0.7828 |
| DISTRIBUTION | 591 | 0.5000 | 0.0910 | 0.5910 |
| EARLY_RECOVERY | 230 | 0.3000 | 0.0000 | 0.3000 |
| LATE_BULL | 308 | 0.7000 | 0.0747 | 0.7747 |
| LATE_RECOVERY | 192 | 0.6000 | 0.0000 | 0.6000 |

## Tactical reduction activity

- Number of distinct REDUCED episodes: 9
- Fraction of classified days spent REDUCED: 27.63%

## Chart
![Price and allocation](figures/strategy_price_and_allocation.png)
