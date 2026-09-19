# Locked Holdout Test -- Final Gate Before Paper Deployment

Holdout window: **2026-03-19 → 2026-09-18** (6 months, the most recent data available). Baseline cost scenario, fresh capital.

**Honesty note:** this is not a statistically clean never-seen holdout -- these days were part of the full-history data used to select Cycle Only over Cycle + Swing (Milestone 9). Its value is as a discipline commitment: the strategy is FROZEN as of this run. No further tuning based on this result. See src/backtesting/locked_holdout.py for the full caveat.

## Results
| strategy | n_days | total_return | cagr | max_drawdown | sharpe | sortino | n_trades |
|---|---|---|---|---|---|---|---|
| Cycle Only (frozen strategy) | 183 | 0.0965 | 0.2016 | -0.0916 | 1.0665 | 1.6865 | 16 |
| Buy & Hold | 183 | 0.0883 | 0.1839 | -0.2880 | 0.6362 | 1.0592 | 1 |
| Cash | 183 | 0.0000 | 0.0000 | 0.0000 | nan | nan | 0 |
| Simple MA Trend | 183 | 0.1071 | 0.2250 | -0.0699 | 1.2342 | 1.1213 | 1 |

## Equity curves
![Locked holdout equity curves](figures/locked_holdout_equity_curves.png)
