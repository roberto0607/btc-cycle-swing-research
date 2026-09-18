# Data Dictionary

Filled in during Phase 1 (Data Pipeline). Every raw and processed column
gets an entry here before it's used in any feature or research notebook.

## Raw data schema (target, before Phase 1 implementation)

| Column | Type | Description | Source |
|---|---|---|---|
| `timestamp` | datetime (UTC) | Candle open time | Kraken / Coinbase |
| `source` | string | `kraken` or `coinbase` | ingestion |
| `symbol` | string | `BTC-USD` | ingestion |
| `timeframe` | string | `1d` | ingestion |
| `open` | float | Candle open price | exchange |
| `high` | float | Candle high price | exchange |
| `low` | float | Candle low price | exchange |
| `close` | float | Candle close price | exchange |
| `volume` | float | Base-asset volume | exchange |
| `ingested_at` | datetime (UTC) | When this row was pulled | ingestion |

## Processed / derived features

Built by `src/features/pipeline.py` (Milestone 4) from the primary
(Coinbase) raw series only. All features are causal by construction — see
the docstring in `src/features/common.py` and the leakage-regression
tests in `tests/test_features.py`. `w` = rolling window length in days
unless noted; a feature is `NaN` for the first `w-1` rows of the series
(insufficient warmup data), which is expected, not a data-quality defect.

### Price / trend (`src/features/price.py`)
| Column | Definition |
|---|---|
| `return_1d` | 1-day simple return: `close[t]/close[t-1] - 1` |
| `log_return_1d` | 1-day log return: `ln(close[t]/close[t-1])` |
| `sma_{20,50,100,200}` | Simple moving average of `close` over the window |
| `dist_from_sma_{20,50,100,200}` | `(close - sma) / sma` |
| `drawdown_from_ath` | `(close - running_max(close)) / running_max(close)`, running max taken over all data up to and including row t (expanding window, causal) |
| `runup_from_low_{30,60,90,180,365}d` | `(close - rolling_min(close, w)) / rolling_min(close, w)` |

### Momentum (`src/features/momentum.py`)
| Column | Definition |
|---|---|
| `rsi_{7,14,21}` | Wilder-style RSI using simple (not exponential) rolling average gain/loss. Edge cases: all-gain/no-loss window → 100; completely flat window (no gain, no loss) → neutral 50, not 100 (see `test_rsi_is_neutral_for_flat_price` regression test) |
| `return_{1,3,7,14,30,60,90}d` | N-day simple return |

### Volatility (`src/features/volatility.py`)
| Column | Definition |
|---|---|
| `atr_14` | 14-day rolling mean of Wilder's True Range (`max(high-low, \|high-prev_close\|, \|low-prev_close\|)`) |
| `atr_pct_14` | `atr_14 / close` |
| `realized_vol_{14,30}d` | Rolling std of 1-day log returns over the window, annualized (`* sqrt(365)`) |
| `vol_percentile_365d` | Percentile rank (0-1) of `realized_vol_14d` within its own trailing 365-day distribution |
| `bollinger_width_20` | `(upper_band - lower_band) / sma_20`, bands = `sma_20 ± 2 * rolling_std_20(close)` |

### Volume (`src/features/volume.py`)
| Column | Definition |
|---|---|
| `volume_ma_20` | 20-day rolling mean of `volume` |
| `volume_ratio_20` | `volume / volume_ma_20` (note: the MA includes today, so a spike day inflates its own average — a genuine 3x-average day reads as ~2.7x, not exactly 3x) |
| `volume_percentile_365d` | Percentile rank (0-1) of `volume` within its own trailing 365-day distribution |

### Market structure (`src/features/structure.py`) — first-pass definition, see module docstring
| Column | Definition |
|---|---|
| `dist_from_swing_high_20d` / `dist_from_swing_low_20d` | `(close - rolling_max/min(high/low, 20)) / rolling_max/min(...)`, window includes today |
| `breakout_up_20d` / `breakout_down_20d` | `close` clears the prior 20 days' high/low, EXCLUDING today from its own reference range (`shift(1)` before the rolling window) |

## Labels

(To be populated once `PULLBACK(threshold, horizon)` labels are
implemented — see RESEARCH_SPEC.md §6 for the formal definition.)
