# Project Map

Every file created in this project is documented here. Update this file
whenever files are added or changed (master spec Section 43, Coding
Instruction 13).

| File | Purpose | Depends on | Inputs | Outputs | Status |
|---|---|---|---|---|---|
| `docs/RESEARCH_SPEC.md` | Locked research spec: datasets, features, labels, methodology | — | Master handoff doc + Roberto's decisions | Reference doc for all later phases | Done (Phase 0) |
| `docs/PROJECT_MAP.md` | This file | — | — | — | Living |
| `docs/METHODOLOGY.md` | Development rules (no-look-ahead, costs, etc.) | RESEARCH_SPEC.md | — | Reference doc | Done (Phase 0) |
| `docs/DATA_DICTIONARY.md` | Column-level definitions for every dataset | — | — | Reference doc | Skeleton — filled in Phase 1 |
| `docs/EXPERIMENT_LOG.md` | Record of every research experiment | — | — | Running log | Skeleton — filled starting Phase 2 |
| `README.md` | Project overview, setup instructions | — | — | — | Done (Phase 0) |
| `pyproject.toml` | Python project + dependency config | — | — | — | Done (Phase 0) |
| `configs/` | Data/research/backtest/ml configuration files | — | — | — | Skeleton — populated per phase |
| `src/data/ingestion/` | Kraken + Coinbase OHLCV fetchers | RESEARCH_SPEC.md §2 | Exchange public APIs | `data/raw/*` | Not started (Phase 1) |
| `src/data/validation/` | Gap/duplicate/bad-OHLC checks | ingestion | `data/raw/*` | validation reports | Not started (Phase 1) |
| `src/data/processing/` | Normalization, timezone handling | validation | `data/raw/*` | `data/processed/*` | Not started (Phase 1) |
| `src/features/` | Price/momentum/volatility/volume/structure/regime feature functions | processing | `data/processed/*` | `data/features/*` | Not started (Phase 2+) |
| `src/research/` | Cycle, pullback, swing, statistical research notebooks-as-code | features | `data/features/*` | `reports/*` | Not started (Phase 2–4) |
| `src/regimes/` | Regime definitions, classifier, analysis | research | features | regime labels | Not started (Phase 3) |
| `src/strategies/` | Cycle, swing, combined deterministic strategies | regimes | features + regime labels | strategy signals | Not started (Phase 5) |
| `src/backtesting/` | Engine, portfolio, execution, costs, metrics | strategies | signals + processed data | backtest results | Not started (Phase 6) |
| `src/ml/` | Datasets, features, labels, models, training, evaluation | backtesting baseline | features + labels | ML predictions + comparison | Not started (Phase 9+) |
| `src/visualization/` | Chart generation | backtesting/research | results | `reports/*` charts | Not started (as needed) |
| `tests/` | Unit tests, esp. leakage checks | all `src/` modules | — | pass/fail | Not started (Phase 1+, grows with each module) |

## Milestone status

- [x] Milestone 1 — Project initialization
- [ ] Milestone 2 — Data acquisition
- [ ] Milestone 3 — Data validation
- [ ] Milestone 4 — Feature engineering
- [ ] Milestone 5 — Exploratory analysis
- [ ] Milestone 6 — Cycle research
- [ ] Milestone 7 — Pullback research
- [ ] Milestone 8 — Deterministic strategy
- [ ] Milestone 9 — Backtester
- [ ] Milestone 10 — Robustness
- [ ] Milestone 11 — Walk-forward
- [ ] Milestone 12 — ML dataset
- [ ] Milestone 13 — ML baseline
- [ ] Milestone 14 — ML comparison
- [ ] Milestone 15 — Paper validation
