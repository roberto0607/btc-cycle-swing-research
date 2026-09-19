"""
Milestone 12 walk-forward evaluation (RESEARCH_SPEC.md section 39: "The
model should be retrained only using information that would have been
available at that point in history.").

Uses the SAME window boundaries as Milestone 11 (src/backtesting.
walk_forward.define_windows) for direct comparability, but unlike
Milestone 11 (which just resets capital per window for an already-frozen,
never-fitted strategy), this is genuine expanding-window ML walk-forward:
for window i, the model is fit ONLY on rows strictly before that window's
start, then used to predict (never refit) on every row inside the window.
Window 1 has no prior data to train on and is skipped, not filled with a
guess.

The ML-enhanced allocation mirrors Milestone 8's swing.py architecture --
core allocation from cycle.py, a tactical layer that reduces exposure
when triggered, gated to the same regimes swing.py used -- but the
trigger is now "predicted pullback probability from a properly fit
model" instead of a hand-picked percentile threshold. This makes the
comparison to Milestone 9's rejected swing layer as apples-to-apples as
possible: same architecture, different (and, this time, actually fitted)
trigger.
"""

from __future__ import annotations

import pandas as pd
from sklearn.metrics import accuracy_score, roc_auc_score

from src.backtesting.costs import get_cost_model
from src.backtesting.engine import run_backtest
from src.backtesting.metrics import compute_metrics
from src.backtesting.walk_forward import define_windows
from src.ml.features import build_feature_matrix
from src.ml.model import fit, predict_proba
from src.strategies.cycle import add_core_allocation

TACTICAL_MAX = 0.20
TACTICAL_ELIGIBLE_REGIMES = {"BULL", "LATE_BULL", "DISTRIBUTION"}  # matches swing.py's choice
TRIGGER_THRESHOLD = 0.5  # predicted P(pullback) >= this -> reduce tactical exposure


def run_ml_walk_forward(
    df: pd.DataFrame,
    target_col: str,
    window_years: float = 2.0,
    cost_scenario: str = "baseline",
    initial_capital: float = 10_000.0,
    timestamp_col: str = "timestamp",
) -> pd.DataFrame:
    windows = define_windows(df, window_years=window_years, timestamp_col=timestamp_col)
    costs = get_cost_model(cost_scenario)

    X_full, feature_names = build_feature_matrix(df)
    valid_mask = X_full.notna().all(axis=1) & df[target_col].notna() & df["regime"].notna()

    rows = []
    for i, (start, end) in enumerate(windows):
        train_mask = valid_mask & (df[timestamp_col] < start)
        test_segment_mask = (df[timestamp_col] >= start) & (df[timestamp_col] <= end)

        n_train = train_mask.sum()
        if n_train < 200:  # not enough history to fit anything meaningful yet
            rows.append({"window_start": start, "window_end": end, "n_train": int(n_train), "skipped": True})
            continue

        y_train = df.loc[train_mask, target_col].astype(int)
        if y_train.nunique() < 2:  # can't fit/evaluate a classifier with only one class present
            rows.append({"window_start": start, "window_end": end, "n_train": int(n_train), "skipped": True})
            continue

        pipeline = fit(X_full.loc[train_mask], y_train)

        test_mask = valid_mask & test_segment_mask
        segment = df.loc[test_segment_mask].reset_index(drop=True)
        if len(segment) < 30:
            rows.append({"window_start": start, "window_end": end, "n_train": int(n_train), "skipped": True})
            continue

        # Predict for every row in the window that has valid inputs;
        # rows without valid inputs (shouldn't happen post-warmup, but
        # handled defensively) get probability 0 (no reduction) rather
        # than crashing.
        proba_valid = predict_proba(pipeline, X_full.loc[test_mask])
        predicted_prob = pd.Series(0.0, index=df.loc[test_segment_mask].index)
        predicted_prob.loc[proba_valid.index] = proba_valid
        predicted_prob = predicted_prob.reset_index(drop=True)

        segment = add_core_allocation(segment)
        trigger = (predicted_prob >= TRIGGER_THRESHOLD) & segment["regime"].isin(TACTICAL_ELIGIBLE_REGIMES)
        tactical = trigger.map({True: 0.0, False: TACTICAL_MAX})
        tactical = tactical.where(segment["regime"].isin(TACTICAL_ELIGIBLE_REGIMES), 0.0)
        segment["ml_alloc"] = (segment["core_allocation"] + tactical).clip(upper=1.0)

        result = run_backtest(segment, allocation_col="ml_alloc", costs=costs, initial_capital=initial_capital)
        metrics = compute_metrics(result.to_series(), n_trades=len(result.portfolio.trades))

        y_test = df.loc[test_mask, target_col].astype(int)
        if len(y_test) >= 10 and y_test.nunique() == 2:
            test_pred = (proba_valid >= TRIGGER_THRESHOLD).astype(int)
            accuracy = accuracy_score(y_test.loc[proba_valid.index], test_pred)
            roc_auc = roc_auc_score(y_test.loc[proba_valid.index], proba_valid)
        else:
            accuracy, roc_auc = float("nan"), float("nan")

        rows.append(
            {
                "window_start": start,
                "window_end": end,
                "n_train": int(n_train),
                "skipped": False,
                "base_rate": y_test.mean() if len(y_test) else float("nan"),
                "accuracy": accuracy,
                "roc_auc": roc_auc,
                "cagr": metrics.get("cagr"),
                "max_drawdown": metrics.get("max_drawdown"),
                "sharpe": metrics.get("sharpe"),
            }
        )

    return pd.DataFrame(rows)
