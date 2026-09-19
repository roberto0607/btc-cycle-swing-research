# Phase 8 Walk-Forward Evaluation -- Cycle Only vs Buy & Hold

**Honesty note (read this before the numbers):** Cycle Only's allocation table was never numerically fit to this dataset -- it's a fixed hypothesis from Milestone 6's qualitative regime ranking, not an optimized parameter set, so there's no parameter-fitting leakage for walk-forward to catch in the usual ML sense. However, the DECISION to keep Cycle Only over Cycle + Swing (Milestone 9) was made using full-history results, including the most recent window below. This is therefore a test of whether the already-chosen, frozen strategy's edge holds up window by window -- not an uncontaminated test of whether it was the right strategy to choose in the first place. See RESEARCH_SPEC.md section 12.5 and src/backtesting/walk_forward.py for the full caveat.

- Windows where strategy beat Buy & Hold on CAGR: 50%
- Windows where strategy beat Buy & Hold on max drawdown: 100%
- **Most recent window** (2025-07-19 → 2026-09-18): strategy CAGR -10.97% vs Buy & Hold -30.50% (beat benchmark)

## Window-by-window comparison
| window_start | window_end | n_days_strategy | cagr_strategy | cagr_benchmark | beat_on_cagr | max_drawdown_strategy | max_drawdown_benchmark | beat_on_drawdown |
|---|---|---|---|---|---|---|---|---|
| 2015-07-20 00:00:00+00:00 | 2017-07-19 12:00:00+00:00 | 731 | 0.8969 | 1.8341 | False | -0.2432 | -0.3625 | True |
| 2017-07-19 12:00:00+00:00 | 2019-07-20 00:00:00+00:00 | 731 | 0.9410 | 0.9318 | True | -0.5678 | -0.8380 | True |
| 2019-07-20 00:00:00+00:00 | 2021-07-19 12:00:00+00:00 | 731 | 0.6810 | 0.6903 | False | -0.3146 | -0.5946 | True |
| 2021-07-19 12:00:00+00:00 | 2023-07-20 00:00:00+00:00 | 731 | 0.0450 | -0.0006 | True | -0.4371 | -0.7667 | True |
| 2023-07-20 00:00:00+00:00 | 2025-07-19 12:00:00+00:00 | 731 | 0.5512 | 0.9853 | False | -0.1913 | -0.2817 | True |
| 2025-07-19 12:00:00+00:00 | 2026-09-18 00:00:00+00:00 | 426 | -0.1097 | -0.3050 | True | -0.2591 | -0.5308 | True |

## Chart
![Walk-forward windows](figures/walk_forward_windows.png)
