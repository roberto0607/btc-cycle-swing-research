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

(To be populated as `src/features/*` modules are implemented — each
feature function's output column, formula, and lookback window documented
here before use.)

## Labels

(To be populated once `PULLBACK(threshold, horizon)` labels are
implemented — see RESEARCH_SPEC.md §6 for the formal definition.)
