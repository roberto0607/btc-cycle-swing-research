# Methodology & Development Rules

These rules are non-negotiable throughout the project (master spec
Sections 3, 38, 48, 58, 60).

## No look-ahead bias
A feature, regime label, or decision at time T may use only data with
timestamp ≤ T. This applies to rolling windows, normalization, scaling,
feature selection, and parameter optimization. Fit any preprocessing
(scalers, feature selectors) on the training window only, then apply
unchanged to validation/test — never fit on the full dataset.

Future information (e.g. "this was the eventual cycle bottom") may be used
for *research analysis* explaining what happened historically, but must
never leak into a feature, training input, or live decision unless it is
explicitly the target/label being predicted.

## No unrealistic fills
Never assume perfect fill at the signal's own close price unless that is
explicitly the documented execution assumption for a given experiment.

## Costs are mandatory
Every backtest runs under multiple cost scenarios (optimistic / baseline /
pessimistic / stress). A strategy that only "works" under unrealistically
low costs is not a working strategy.

## Don't optimize for return alone
Primary evaluation = risk-adjusted performance + drawdown reduction +
long-term BTC participation. Report the full tradeoff surface, not a
single composite score.

## Prefer stable parameter regions
When searching parameters, look for stable plateaus, not isolated peaks.
Document the search space and the reason for its bounds.

## Out-of-sample discipline
Final evaluation uses data untouched by any prior experiment. If many
hypotheses are tested along the way, document that fact explicitly — it's
relevant to interpreting how much to trust the final result.

## ML must earn its place
ML is introduced only after the deterministic strategy has been
robustness- and walk-forward-tested. It's retained only if it produces a
persistent, meaningful improvement on unseen data. "ML didn't help" is a
valid, useful research conclusion — not a failure to hide.

## Documentation discipline
- Never silently change a research assumption, label definition, or
  transaction-cost assumption.
- Explicitly flag any potential leakage the moment it's noticed.
- Update `PROJECT_MAP.md` and `README.md` whenever files are added/changed.
- Log every meaningful experiment in `EXPERIMENT_LOG.md`.

## Engineering hygiene
- Type hints throughout Python.
- Tests for every important calculation, especially leakage checks.
- Raw data is immutable — never overwritten.
- Datasets and configs are versioned.
- No unnecessary abstractions; no premature ML; no live trading; no
  Kraken execution; no integration with the AI Trading Agent — until
  each is explicitly justified by completed research.
