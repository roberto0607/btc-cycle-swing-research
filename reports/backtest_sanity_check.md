# Backtest Engine Sanity Check

100% buy-and-hold is the trivial case: one BUY, held forever. The engine's simulated end value is compared against an independently hand-computed expected value using the same cost assumptions but different code.

- Engine end value: $2,740,486.17
- Independently expected end value: $2,740,486.17
- Difference: $0.0000 (0.00000000%)
- **PASS** (threshold: 0.0001% relative difference)

## Buy-and-hold metrics (baseline cost scenario)
- start_value: 10000.0
- end_value: 2740486.174251535
- n_days: 4079
- n_years: 11.18
- total_return: 273.0486174251535
- cagr: 0.6525074915960649
- annualized_volatility: 0.6666689264381883
- max_drawdown: -0.838015349610509
- sharpe: 1.0894195446707873
- n_trades: 1

- Number of trades executed: 1 (expect exactly 1 -- a single entry, never rebalanced since allocation never changes)
