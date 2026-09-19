# Phase 9 ML Baseline vs Deterministic Baseline

Target: `pullback_10pct_30d` (10% pullback within 30 days). Model: logistic regression, expanding-window walk-forward (fit only on data strictly before each window, per RESEARCH_SPEC.md section 39). Compared against Cycle Only (RESEARCH_SPEC.md section 12.5) on the SAME window boundaries as Milestone 11.

## Verdict

**REJECT -- ML beat Cycle Only on Sharpe in only 40% of evaluated windows (CAGR: 40%), mean out-of-sample ROC-AUC 0.581. Per RESEARCH_SPEC.md section 37, this is a valid, complete result -- the deterministic Cycle Only baseline stands.**

## Window-by-window comparison
| window_start | window_end | n_train | skipped | base_rate | accuracy | roc_auc | cagr_ml | cagr_baseline | sharpe_ml | sharpe_baseline | max_drawdown_ml | max_drawdown_baseline |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2015-07-20 00:00:00+00:00 | 2017-07-19 12:00:00+00:00 | 0 | True | nan | nan | nan | nan | 0.8969 | nan | 1.9438 | nan | -0.2432 |
| 2017-07-19 12:00:00+00:00 | 2019-07-20 00:00:00+00:00 | 367 | False | 0.5157 | 0.4802 | 0.5634 | 1.0776 | 0.9410 | 1.5106 | 1.5106 | -0.6464 | -0.5678 |
| 2019-07-20 00:00:00+00:00 | 2021-07-19 12:00:00+00:00 | 1097 | False | 0.5021 | 0.5951 | 0.5943 | 0.6548 | 0.6810 | 1.3317 | 1.4151 | -0.3517 | -0.3146 |
| 2021-07-19 12:00:00+00:00 | 2023-07-20 00:00:00+00:00 | 1828 | False | 0.5048 | 0.5048 | 0.5890 | 0.0398 | 0.0450 | 0.2828 | 0.2981 | -0.4859 | -0.4371 |
| 2023-07-20 00:00:00+00:00 | 2025-07-19 12:00:00+00:00 | 2558 | False | 0.3694 | 0.5964 | 0.6095 | 0.6599 | 0.5512 | 1.6020 | 1.5860 | -0.2397 | -0.1913 |
| 2025-07-19 12:00:00+00:00 | 2026-09-18 00:00:00+00:00 | 3289 | False | 0.3510 | 0.6465 | 0.5504 | -0.1240 | -0.1097 | -0.5331 | -0.5460 | -0.2940 | -0.2591 |
