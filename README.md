# BTC Cycle + Swing Research System

A standalone quantitative research project investigating whether historical
BTC market behavior can be converted into a systematic, statistically
validated, long-only trading strategy — cycle-aware core allocation plus
tactical swing trading around statistically significant extensions and
pullbacks.

**This is independent of the `AI Trading Agent` project.** No shared code,
no shared architecture. The only intended relationship is one-directional:
a validated strategy or model from here could eventually inform that
project's execution layer — not before then.

## Research question

> Can historical BTC market behavior be used to identify broad market-cycle
> regimes and meaningful pullbacks, allowing a systematic long-only
> strategy to accumulate BTC during favorable long-term conditions,
> participate in major bull trends, tactically reduce exposure during
> statistically significant extensions, and re-enter after pullbacks —
> while improving risk-adjusted performance and drawdown characteristics
> versus simpler BTC benchmarks?

See `docs/RESEARCH_SPEC.md` for the full specification and
`docs/METHODOLOGY.md` for the non-negotiable development rules (no
look-ahead bias, mandatory transaction costs, ML must earn its place,
etc.).

## Status

Phase 0 (Research Design) complete. Phase 1 (Data Pipeline) next.
See `docs/PROJECT_MAP.md` for the live milestone tracker.

## Approach

Deterministic, statistically-validated research first. Machine learning is
introduced only after a deterministic strategy has survived robustness and
walk-forward testing — and is kept only if it beats that baseline
out-of-sample.

```
Hypothesis → Data → Validation → Exploration → Statistical Evidence →
Deterministic Strategy → Backtest → Robustness → Walk-Forward → ML →
ML vs Deterministic → Paper Validation
```

## Data

- Kraken public REST (`/0/public/OHLC`) and Coinbase Exchange public
  candles — both free, no-auth, US-accessible. Kraken is the primary
  series; Coinbase is used for cross-validation.
- Daily BTC-USD OHLCV, 2015-07-20 → present (Coinbase's earliest available
  daily candle for this pair), as the primary dataset.

## Setup

```bash
poetry install   # or: pip install -e .
```

## Project structure

See `docs/PROJECT_MAP.md` for what every directory and file is for and its
current status.

## Principles

1. Research before optimization.
2. No look-ahead bias, ever.
3. Realistic fills and mandatory transaction costs.
4. Don't optimize for return alone — report the full risk/return tradeoff.
5. Prefer stable parameter regions over isolated peaks.
6. Out-of-sample data stays untouched until final evaluation.
7. ML must beat the deterministic baseline to justify its complexity.
8. Every experiment is logged — including failures.
