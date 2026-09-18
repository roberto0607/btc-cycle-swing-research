# BTC Cycle + Swing Research System — Research Specification

Status: DRAFT — Phase 0 (Research Design)
This document is the locked reference for datasets, features, labels, and
methodology. Changes here must be deliberate and documented (Section 58,
Rules 11 & 16 of the master spec) — never silently altered mid-research.

---

## 0. Relationship to other projects

This is a fully standalone project. It is NOT part of, and does not import
from or depend on, the `AI Trading Agent` project (Fastify/TypeScript/
Postgres). The only intended future relationship is one-directional: a
validated strategy/feature/model from this project could eventually inform
the AI Trading Agent's execution layer. No such integration happens in
Phases 0–7.

---

## 1. Research Question

Can historical BTC market behavior be used to identify broad market-cycle
regimes and meaningful pullbacks, allowing a systematic long-only strategy
to accumulate BTC during favorable long-term conditions, participate in
major bull trends, tactically reduce exposure during statistically
significant extensions, and re-enter after pullbacks — while improving
risk-adjusted performance and drawdown characteristics versus simpler BTC
benchmarks?

This is decomposed into three hypotheses (Cycle Allocation, Swing Behavior,
Combined Strategy) — see master spec Sections 4–7.

---

## 2. Datasets

### 2.1 Primary dataset
- **Sources:** Coinbase Exchange public candles endpoint (no auth, product
  `BTC-USD`, daily granularity) and Kraken public REST
  (`GET /0/public/OHLC`, no auth, pair `XBTUSD`, interval `1440` = daily).
- **Coverage:** 2014-01-01 → present via Coinbase. Kraken only covers the
  trailing ~720 daily candles (~2 years) — see correction note below.
- **Rationale:** both free, no-auth, US-accessible (satisfies the project's
  data-source rule — no geoblocking risk).
- **Role of each source — CORRECTED 2026-09-18:** originally specified
  Kraken as primary with Coinbase for cross-validation. That was wrong.
  Kraken's public `OHLC` endpoint has a hard, documented platform limit:
  *"Returns up to 720 of the most recent entries (older data cannot be
  retrieved, regardless of the value of `since`)"* — there is no
  pagination path to deep history on this endpoint, confirmed against
  Kraken's own API docs after a live ingestion run only returned 721 rows.
  Corrected roles:
  - **Coinbase is now primary/reference** for all strategy and backtest
    logic — its `/candles` endpoint genuinely paginates back to 2014.
  - **Kraken is a recent-period cross-check only**, valid for roughly the
    trailing 2 years. Any Section 50 cross-validation claim is limited to
    that overlapping recent window, not the full history.
  - Kraken also publishes a full historical OHLCVT bulk-download archive
    (multi-GB ZIP, manual download from Kraken's site/Google Drive, not
    auth-gated) as a possible future second full-history source if the
    ~2-year Kraken cross-check proves insufficient — not implemented in
    Phase 1, flagged as a Section 13 open item instead.

### 2.2 Deferred/appendix dataset
- Pre-2014 BTC price history (Mt. Gox era and early exchanges) — lower
  data quality, different market structure. Not part of the primary
  research set. May be added later as an explicitly-labeled low-confidence
  appendix if cycle-level sample size becomes a binding constraint.

### 2.3 Future layers (not in Phase 1)
Derivatives (funding, OI, basis), on-chain (MVRV, realized price, NUPL),
macro (Fed policy, CPI, DXY) — see master spec Section 14. Added only after
Layer 1–2 (price + derived features) research is complete, and only if a
specific hypothesis needs them.

---

## 3. Timeframe

- Primary research timeframe: **daily**.
- 4H/1H considered later for swing-research granularity only if daily
  resolution proves insufficient to resolve a specific question — not a
  default.

---

## 4. Feature families (Phase 1–2 scope)

- **Price/trend:** returns, log returns, SMA20/50/100/200 distance ratios,
  drawdown from rolling ATH, run-up from rolling low (30/60/90/180/365D).
- **Momentum:** RSI(7/14/21), N-day returns (1/3/7/14/30/60/90D), rate of
  change.
- **Volatility:** ATR, ATR%, realized volatility (rolling), volatility
  percentile, Bollinger Band width.
- **Volume:** volume, volume MA, volume ratio, volume percentile.
- **Market structure:** higher-high/higher-low/lower-high/lower-low state,
  distance from recent swing high/low, breakout state.

All features computed causally — a feature at time T uses only data with
timestamp ≤ T. No exceptions (master spec Section 3, "NO LOOK-AHEAD BIAS").

---

## 5. Regime definitions (candidate, research-driven)

Candidate labels: `BEAR, ACCUMULATION, RECOVERY, BULL, LATE_BULL,
DISTRIBUTION`. These are hypotheses to test, not assumed ground truth.
Phase 3 explicitly asks: does knowing the regime add predictive information
over not knowing it? If a simpler regime scheme (e.g. 3 states) performs
equivalently, prefer the simpler scheme.

---

## 6. Pullback label definition

`PULLBACK(threshold, horizon)`:

> Starting from the decision timestamp with reference price P, did the
> future **intraperiod low** fall to ≤ P × (1 − threshold) at any point
> within the next `horizon` days?

- `threshold ∈ {5%, 7.5%, 10%, 12.5%, 15%, 20%, 25%}`
- `horizon ∈ {3D, 7D, 14D, 30D, 60D, 90D}`

Both intraperiod-low-based and close-to-close-based versions are computed
(master spec Section 24) and kept as distinct, separately-named columns —
never conflated.

---

## 7. Benchmarks

1. 100% BTC buy-and-hold
2. 100% cash
3. Simple moving-average trend strategy
4. Cycle allocation only
5. Cycle + swing
6. Cycle + swing + risk management (later)

---

## 8. Backtesting assumptions

- Execution model: to be selected in Phase 6 from {next-candle-open,
  next-candle VWAP approx, bid/ask + spread model} — explicitly documented
  per experiment, never assumed as "fill at signal close" by default.
- Cost scenarios: optimistic / baseline / pessimistic / stress — every
  reported backtest result carries its cost scenario label.

---

## 9. Performance metrics

Return (Total, CAGR), Risk (Max DD, annualized vol, downside deviation),
Risk-adjusted (Sharpe, Sortino, Calmar), Trading behavior (trade count,
turnover, win rate, profit factor, avg holding period), BTC-specific
(exposure, time invested, bull capture, bear-loss avoidance, ending BTC
holdings), Opportunity cost (upside missed, downside avoided). No single
composite "best strategy" score — full tradeoff surface reported (master
spec Section 22).

---

## 10. Robustness methodology

Parameter perturbation (test ranges, not single values — look for stable
plateaus), timeframe variation, cost variation, execution degradation,
per-cycle regime variation. Mandatory before any strategy is called
"working" (master spec Phase 7).

---

## 11. Walk-forward methodology

Train → Validate → Locked Test, then roll forward. Exact window lengths
chosen in Phase 8 once total available history (2014–present ≈ 11+ years
daily) is confirmed against the number of BTC cycles available. No feature,
scaler, or parameter may be fit using data outside its train window.

---

## 12. ML experiment design (Phase 9+, not before)

Primary target: `P(≥10% pullback within 30 days)` as a starting point, with
the full label grid (Section 6) available for secondary targets. Model
progression: Logistic Regression → Random Forest/Gradient Boosting/XGBoost
/LightGBM → neural nets only if justified. ML is retained only if it beats
the deterministic baseline out-of-sample on risk-adjusted metrics — not
retained by default (master spec Section 37).

---

## 13. Open items to revisit

- Exact walk-forward window lengths (Phase 8, once EDA confirms usable
  history length).
- Whether 4H granularity is needed for swing research (Phase 4, only if
  daily proves insufficient).
- Whether pre-2014 appendix data gets added (only if cycle-level sample
  size is a binding constraint by Phase 3).
- Whether a second full-history source is worth adding (e.g. Kraken's
  bulk OHLCVT archive, manually downloaded, or another exchange's public
  API) to restore genuine multi-year cross-validation — currently
  Coinbase is the only full-history source; Kraken cross-checks only the
  trailing ~2 years.
