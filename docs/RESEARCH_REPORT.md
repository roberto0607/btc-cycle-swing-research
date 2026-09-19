# BTC Cycle + Swing Research System — Research Report

**Status:** Deterministic + ML research phases complete. No paper trading yet.
**Repo:** github.com/roberto0607/btc-cycle-swing-research
**Data:** Coinbase BTC-USD daily, 2015-07-20 → 2026-09-18 (4,079 days, ~11.2 years)

---

## 1. Executive Summary

This project investigated whether Bitcoin's historical market behavior
contains enough structure to build a systematic, risk-reducing allocation
strategy — one that stays invested through favorable conditions and
reduces exposure ahead of unfavorable ones, without relying on
prediction of exact tops or bottoms.

The answer is **yes, but narrowly and specifically**: a deterministic
strategy that sizes BTC exposure by market regime (`Cycle Only`) delivers
a real, reproducible improvement in risk-adjusted return over passive
buy-and-hold — beating it on Sharpe (1.28 vs 1.09) and Sortino (1.54 vs
1.47), and cutting maximum drawdown nearly in half (-56.8% vs -83.8%).
That edge held up under parameter perturbation, execution-assumption
degradation, and out-of-sample walk-forward testing across six
sequential 2-year windows — where it beat buy-and-hold on drawdown
reduction in **100% of windows**, though only on raw return in 50%.

Two attempts to improve on this baseline both failed and were rejected:
a hand-tuned tactical "swing" overlay (Milestone 8-9) and a properly
fit logistic regression ML layer (Milestone 12), both tested against
the same baseline under the same walk-forward discipline. Neither beat
`Cycle Only`. Both rejections are treated as complete, valid research
results, not failures — per this project's own methodology (section 37).

**The honest one-sentence version:** BTC's market cycles carry enough
signal to meaningfully reduce drawdown risk through regime-based
allocation, but not enough exploitable short-term structure — at least
not from the features tested here — to beat that simple allocation rule
with tactical timing or machine learning.

---

## 2. Research Question

> Can historical BTC market behavior be used to identify broad
> market-cycle regimes and meaningful pullbacks, allowing a systematic
> long-only strategy to accumulate BTC during favorable long-term
> conditions, participate in major bull trends, tactically reduce
> exposure during statistically significant extensions, and re-enter
> after pullbacks — while improving risk-adjusted performance and
> drawdown characteristics versus simpler BTC benchmarks?

(RESEARCH_SPEC.md section 1, set before any data was pulled.)

---

## 3. Data

- **Primary source:** Coinbase Exchange public candles API (free,
  no-auth). Daily BTC-USD OHLCV, 2015-07-20 → present. This start date
  is Coinbase's actual earliest available daily candle for this pair —
  confirmed empirically (Milestone 3 validation found zero gaps within
  the range), not the 2014-01-01 originally assumed in the spec before
  live data corrected it.
- **Cross-validation source:** Kraken public OHLC API. Discovered to
  have a hard platform limit — it only returns the most recent ~720
  daily candles regardless of the `since` parameter, confirmed against
  Kraken's own documentation. Demoted from primary to a recent-period-
  only (~2 year) cross-check after this was found.
- **Validation:** Every raw file passed automated checks for duplicate
  timestamps, null values, non-positive prices, impossible OHLC
  geometry (high < low, etc.), and calendar gaps. Zero critical issues
  found on either source's real data.

---

## 4. Methodology Overview

Research proceeded in the sequence the spec mandated: exploratory
analysis → regime research → pullback research → deterministic strategy
→ backtest → robustness → walk-forward → ML comparison. No step was
skipped or reordered, and no later step's findings were allowed to
silently rewrite an earlier step's conclusions — corrections are
documented inline (see section 12).

---

## 5. Feature Definitions

38 causal features built from raw OHLCV (Milestone 4), covering five
families: price/trend (returns, SMA distances, drawdown-from-ATH,
run-up-from-low), momentum (RSI at 3 windows, N-day returns), volatility
(ATR, realized vol, Bollinger width, vol percentile), volume (MA, ratio,
percentile), and market structure (swing high/low distance, breakout
flags). Every feature is provably causal — verified by dedicated
leakage-regression tests that confirm no feature's value at row *t*
changes when data after *t* is altered or removed.

---

## 6. Regime Definitions

Seven regimes, classified by a fixed rule table (not fit to data) using
`close` vs. `sma_50`/`sma_200`, `drawdown_from_ath`, and `rsi_14`:
`BEAR`, `ACCUMULATION`, `EARLY_RECOVERY`, `LATE_RECOVERY`, `BULL`,
`LATE_BULL`, `DISTRIBUTION`.

**Correction made during research:** the original single `RECOVERY`
label conflated two opposite situations — its median 90-day forward
return was *negative* (-11.7%) despite a *positive* mean (+13.4%), the
signature of a dead-cat-bounce pattern being averaged together with
genuine bottoms. Split into `EARLY_RECOVERY` (still >50% below the
running ATH) and `LATE_RECOVERY` (shallower drawdown) on Milestone 6,
which cleanly separated the two behaviors at the 14-30 day horizon (the
split was less clean at 90 days — see limitations).

Persistence is real, not noise: day-to-day regime stickiness ranged
82-95% across all seven regimes.

---

## 7. Pullback Definitions

Formal `PULLBACK(threshold, horizon)` labels (Milestone 7): did the
future intraperiod low fall to ≤ (1 - threshold) × today's close within
the next `horizon` days. Full grid: 7 thresholds (5%-25%) × 6 horizons
(3-90 days) = 42 label columns, built with a nullable-boolean
implementation after catching a real bug where naive NaN comparisons
would have silently mislabeled "insufficient future data" as "confirmed
no pullback."

**Key finding:** `runup_from_low_365d` was the most reliable extension
signal — its relationship to forward pullback odds was monotonic across
nearly every regime and horizon tested. RSI and SMA-distance were
noisier and sometimes inverted (e.g., in plain `BULL`, high RSI showed
*lower* 14-day pullback odds than low RSI — the opposite of the naive
technical-analysis assumption). All three features agreed cleanly,
consistently, at every horizon specifically in `LATE_BULL` — the
strongest single finding in the pullback research phase.

---

## 8. Strategy Rules

**Cycle allocation** (`src/strategies/cycle.py`) — a fixed core BTC
allocation by regime, ranked qualitatively from Milestone 6's
regime-conditional forward-return/pullback-odds findings, never
numerically fit to returns:

| Regime | Core allocation |
|---|---|
| BEAR | 0% |
| ACCUMULATION | 40% |
| EARLY_RECOVERY | 30% |
| LATE_RECOVERY | 60% |
| BULL | 70% |
| LATE_BULL | 70% |
| DISTRIBUTION | 50% |

**Swing overlay** (`src/strategies/swing.py`, later rejected) — a
tactical layer reducing exposure when a causal, point-in-time rolling
percentile of `runup_from_low_365d` crossed the 80th percentile
(re-entering only once it fell back to the 50th), active only in
`BULL`/`LATE_BULL`/`DISTRIBUTION`. Built directly on the Milestone 7
finding, using a proper causal percentile rather than the
whole-dataset quantile cutoffs that finding was originally computed
with.

---

## 9. Backtesting Assumptions

- **Execution:** next-day open fill by default (a decision knowable by
  day *t*'s close cannot fill before day *t+1*'s open) — never the
  signal's own close, per the spec's explicit warning against that
  shortcut.
- **Portfolio accounting:** full cash/BTC tracking, fee deducted from
  notional traded, spread+slippage modeled as unfavorable price
  adjustment on both buys and sells.
- **Trade-only-on-change:** the engine only trades when the *target*
  allocation itself changes — a real bug (daily re-trading to correct
  ordinary price drift, 2,100 trades instead of the correct ~265) was
  caught and fixed only once the engine was run against real, moving
  prices; flat-price unit tests had masked it completely.
- **Verification:** engine output cross-checked against an
  independently hand-computed buy-and-hold formula — exact match,
  0.00000000% difference, on real data.

---

## 10. Transaction Costs

Four scenarios (fee + spread + slippage, in basis points), all tested,
not just one assumed-favorable case:

| Scenario | Fee | Spread | Slippage |
|---|---|---|---|
| Optimistic | 5 | 1 | 0 |
| Baseline | 10 | 2 | 5 |
| Pessimistic | 20 | 5 | 15 |
| Stress | 30 | 10 | 30 |

---

## 11. Results — Backtest Comparison (baseline costs, real data)

| Strategy | CAGR | Max Drawdown | Sharpe | Sortino | Trades |
|---|---|---|---|---|---|
| Buy & Hold | 65.25% | -83.80% | 1.089 | 1.470 | 1 |
| Simple MA Trend | 56.68% | -70.91% | 1.132 | 1.212 | 71 |
| **Cycle Only** | **50.97%** | **-56.78%** | **1.278** | **1.543** | **265** |
| Cycle + Swing (rejected) | 35.13% | -57.28% | 1.009 | 1.163 | 255 |

`Cycle Only` beats buy-and-hold on every risk-adjusted metric while
giving up some raw CAGR. `Cycle + Swing` lost to `Cycle Only` on
**every metric, across all four cost scenarios** — not a single-scenario
artifact — and was dropped (see section 12).

---

## 12. Decision Log — What Changed and Why

Documented explicitly per this project's rule against silently changing
research assumptions:

- **Kraken demoted from primary to recent-only cross-check** (Milestone
  2/9 correction) after discovering its API's hard 720-candle limit.
- **Coinbase start date corrected** from an assumed 2014-01-01 to the
  actual 2015-07-20 once live data confirmed it (Milestone 6/7
  correction).
- **`RECOVERY` split into `EARLY_RECOVERY`/`LATE_RECOVERY`** after the
  original label's mean/median divergence exposed a dead-cat-bounce
  confound (Milestone 6).
- **Swing overlay dropped, `Cycle Only` promoted to "the strategy"**
  after losing to the simpler baseline on every metric, every cost
  scenario (Milestone 9). The swing code remains in the repository as a
  documented negative result rather than being deleted.
- **Engine trade-on-drift bug fixed** after real price data (not flat
  test fixtures) exposed 2,100 spurious daily trades (Milestone 9 pass
  2).

---

## 13. Robustness (Milestone 10)

- **Parameter perturbation:** core allocations scaled 0.5×-1.5×. Sharpe
  held stable (1.21-1.29) across the entire range — a genuine plateau,
  not an isolated peak fitted to one specific set of numbers.
- **Execution degradation:** realistic next-open fills vs. the
  unrealistic same-close assumption produced nearly identical results
  (50.97% CAGR both ways) — the strategy's low trade frequency (265
  trades over 11 years) makes it insensitive to this assumption.
- **Per-cycle breakdown:** performance measured independently within
  each major historical bull/bear cycle rather than trusting the
  aggregate. Two clean, strong cycles (2015-18, 2019-21) followed by a
  materially choppier, weaker stretch from 2021 onward — flagged
  honestly rather than smoothed over (see section 16).

---

## 14. Walk-Forward Results (Milestone 11)

Six sequential, non-overlapping 2-year windows, each backtested with
fresh capital (verified not to carry gains from the prior window):

| Window | Cycle Only CAGR | Buy & Hold CAGR | Beat on CAGR | Beat on Max DD |
|---|---|---|---|---|
| 2015-17 | 89.7% | 183.4% | No | Yes |
| 2017-19 | 94.1% | 93.2% | Yes | Yes |
| 2019-21 | 68.1% | 69.0% | No | Yes |
| 2021-23 | 4.5% | -0.1% | Yes | Yes |
| 2023-25 | 55.1% | 98.5% | No | Yes |
| 2025-26 (most recent) | -11.0% | -30.5% | Yes | Yes |

**Win rate on CAGR: 50%. Win rate on max drawdown: 100%, with no
exceptions.** This is the cleanest statement of what the strategy
actually is: a consistent risk-reducer that trades away some bull-market
upside for downside protection — in every single window tested, not just
in aggregate. The most recent window is a direct, real-world example:
the strategy lost less than a third of what buy-and-hold lost during the
same decline.

**Caveat, stated plainly rather than left implicit:** the decision to
keep `Cycle Only` over `Cycle + Swing` (Milestone 9) was made using
full-history results, including this most recent window. This
walk-forward evaluation is therefore a test of whether the
already-chosen, frozen strategy's edge holds up window by window — not
an uncontaminated test of whether it was the correct strategy to select
in the first place.

---

## 15. ML Results (Milestone 12)

A logistic regression baseline, trained expanding-window (strictly on
data before each test window, refit at each window, never on future
data), tested against `Cycle Only` on the same six windows, predicting
`pullback_10pct_30d` from the causal feature set plus regime.

Out-of-sample ROC-AUC by window: **0.563, 0.594, 0.589, 0.610, 0.550** —
barely above the 0.50 random-guess baseline in every window. In one
window, classification accuracy (48.0%) was *worse* than the naive
base-rate guess (51.6%). In another, the model's predicted allocation
never actually crossed its own trigger threshold, so its Sharpe was
identical to `Cycle Only`'s down to the fourth decimal — the model added
nothing that window.

**Verdict: REJECT.** ML beat `Cycle Only` on Sharpe in only 40% of
evaluated windows. This is a stronger, more specific conclusion than the
swing layer's rejection alone could provide: a properly fit model, given
the same and more information, still couldn't extract a usable edge —
evidence the issue is a genuine lack of exploitable signal in these
features, not just a poorly chosen manual threshold.

---

## 16. Failure Cases and Honest Weak Points

- **Recent performance is the weakest in the dataset by some measures.**
  Milestone 10's per-cycle (drawdown-episode-boundary) breakdown showed
  the ongoing final segment with the worst Sharpe in 11 years. Milestone
  11's calendar-window view of the *same period* told a more favorable
  story (strategy lost a third of what buy-and-hold lost). Both are
  real; they're measuring different things (an unresolved mid-decline
  snapshot vs. a completed 2-year window), and reporting only one would
  have been misleading.
- **`LATE_RECOVERY`'s 90-day findings are partly sample-concentrated** —
  ~47% of one window's observations came from a single recent year,
  flagged automatically by a dedicated concentration check rather than
  caught by eye.
- **Small regimes have thin samples.** `LATE_BULL`, `ACCUMULATION`,
  `EARLY_RECOVERY`, and `LATE_RECOVERY` each cover a few hundred rows at
  most out of 4,079 — real, but not enough for high-confidence
  regime-specific claims on their own.
- **RSI and SMA-distance sometimes point the wrong way** within specific
  regimes (section 7) — a caveat that matters if either is ever reused
  outside this project's specific regime-conditional framing.

---

## 17. Limitations

- BTC has only ~3-4 genuinely independent full market cycles in the
  available history — any cycle-level claim (as opposed to swing/pullback-
  level, which has far more observations) carries real, irreducible
  small-sample risk.
- Regime thresholds and the core allocation table are hand-specified
  hypotheses, informed by the data but never numerically optimized
  against it — intentional (to avoid overfitting a 7-regime, few-cycle
  history), but it means the specific numbers chosen were never proven
  optimal, only reasonable.
- The swing layer's 80th/50th percentile thresholds were never
  revisited via a proper parameter sweep once rejected — deferred until
  a walk-forward structure existed to validate any retuning against,
  which it now does; this remains a legitimate, not-yet-done follow-up.
- ML testing covered one target (`pullback_10pct_30d` of the 42-label
  grid), one feature set, and one model family (logistic regression per
  the spec's "don't start with a neural network" rule). Rejection here
  is evidence against *this* approach, not proof no ML approach could
  ever add value.
- Transaction cost modeling is a simplified fee+spread+slippage price
  adjustment, not a full order-book/market-impact model.
- Everything in this report is simulated. No paper trading has occurred.

---

## 18. Conclusion

**What the data demonstrates:** BTC's market history contains real,
detectable regime structure. A simple, interpretable, non-optimized
allocation rule based on that structure delivers a consistent,
walk-forward-validated improvement in risk-adjusted return over passive
holding — specifically through drawdown reduction (100% win rate across
six independent out-of-sample windows), not through timing skill or
return enhancement (50% win rate on raw CAGR). Two more sophisticated
attempts to improve on this — a hand-tuned tactical overlay and a
properly fit ML model — both failed under the same rigorous testing and
were rejected rather than kept.

**What remains uncertain:** whether the specific regime thresholds and
allocation percentages are anywhere near optimal (they were never
tuned), whether a different ML target or feature set would fare better,
and how the strategy performs with real money and real execution
frictions rather than simulated ones.

**The strategy going forward is `Cycle Only`** — deterministic, tested,
and its narrow, honest claim (risk reduction, not return enhancement) is
exactly the kind of specific, defensible research conclusion this
project set out to reach.
