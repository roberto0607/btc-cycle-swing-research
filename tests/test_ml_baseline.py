"""
Tests for Milestone 12: ML baseline feature matrix, model fitting, and
expanding-window walk-forward evaluation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.ml.features import NUMERIC_FEATURE_COLS, REGIME_CATEGORIES, build_feature_matrix
from src.ml.model import fit, predict_proba
from src.ml.walk_forward_ml import run_ml_walk_forward


def _synthetic_labeled_df(n: int = 1500, seed: int = 0, easy_signal: bool = False) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2016-01-01", periods=n, freq="D", tz="UTC")
    close = 100 * np.cumprod(1 + rng.normal(0, 0.02, n))
    regimes = rng.choice(
        ["BEAR", "ACCUMULATION", "EARLY_RECOVERY", "LATE_RECOVERY", "BULL", "LATE_BULL", "DISTRIBUTION"], size=n
    )

    df = pd.DataFrame({"timestamp": dates, "open": close, "close": close, "regime": regimes})
    for col in NUMERIC_FEATURE_COLS:
        df[col] = rng.normal(0, 1, n)

    if easy_signal:
        # Target is trivially derivable from rsi_14 alone, no noise --
        # a sanity check that the pipeline can actually learn something.
        df["pullback_10pct_30d"] = (df["rsi_14"] > 0.5).astype(bool)
    else:
        df["pullback_10pct_30d"] = rng.uniform(0, 1, n) < 0.3

    return df


# ---------------------------------------------------------------------
# Feature matrix
# ---------------------------------------------------------------------

def test_build_feature_matrix_shape_and_columns():
    df = _synthetic_labeled_df(n=100)
    X, names = build_feature_matrix(df)
    assert len(X) == 100
    assert len(names) == len(NUMERIC_FEATURE_COLS) + len(REGIME_CATEGORIES)
    for regime in REGIME_CATEGORIES:
        assert f"regime_is_{regime}" in X.columns


def test_build_feature_matrix_onehot_is_correct():
    df = pd.DataFrame({"regime": ["BULL", "BEAR"], **{c: [0.0, 0.0] for c in NUMERIC_FEATURE_COLS}})
    X, _ = build_feature_matrix(df)
    assert X["regime_is_BULL"].tolist() == [1.0, 0.0]
    assert X["regime_is_BEAR"].tolist() == [0.0, 1.0]
    assert X["regime_is_BULL"].sum() + X["regime_is_BEAR"].sum() == 2  # each row exactly one category


# ---------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------

def test_model_fit_is_deterministic():
    rng = np.random.default_rng(1)
    X = pd.DataFrame(rng.normal(0, 1, (200, 3)), columns=["a", "b", "c"])
    y = (X["a"] > 0).astype(int)

    pipeline_a = fit(X, y)
    pipeline_b = fit(X, y)

    proba_a = predict_proba(pipeline_a, X)
    proba_b = predict_proba(pipeline_b, X)
    pd.testing.assert_series_equal(proba_a, proba_b)


def test_model_learns_an_easy_signal():
    """Sanity check the pipeline actually learns: a target perfectly
    separable by one feature should be predicted with high ROC-AUC on
    held-out data from the SAME distribution."""
    from sklearn.metrics import roc_auc_score

    rng = np.random.default_rng(2)
    X_train = pd.DataFrame(rng.normal(0, 1, (500, 3)), columns=["a", "b", "c"])
    y_train = (X_train["a"] > 0).astype(int)
    X_test = pd.DataFrame(rng.normal(0, 1, (200, 3)), columns=["a", "b", "c"])
    y_test = (X_test["a"] > 0).astype(int)

    pipeline = fit(X_train, y_train)
    proba = predict_proba(pipeline, X_test)
    auc = roc_auc_score(y_test, proba)
    assert auc > 0.9


# ---------------------------------------------------------------------
# Expanding-window walk-forward: the core causality property
# ---------------------------------------------------------------------

def test_first_window_is_always_skipped_no_prior_data():
    df = _synthetic_labeled_df(n=1500)
    results = run_ml_walk_forward(df, target_col="pullback_10pct_30d", window_years=2.0)
    first_row = results.iloc[0]
    assert first_row["n_train"] == 0
    assert first_row["skipped"] == True  # noqa: E712


def test_n_train_grows_monotonically_across_windows():
    """The defining expanding-window property: each successive window's
    training set must be at least as large as the previous one's (it
    only ever grows, since training data is everything strictly before
    the window start)."""
    df = _synthetic_labeled_df(n=3000)
    results = run_ml_walk_forward(df, target_col="pullback_10pct_30d", window_years=1.5)
    n_train_values = results["n_train"].tolist()
    assert n_train_values == sorted(n_train_values)


def test_ml_walk_forward_learns_easy_signal_out_of_sample():
    """
    End-to-end sanity check with the pipeline's own walk-forward harness
    (not just the raw model): when the target is trivially derivable
    from one feature with a STABLE relationship over time, later windows
    (which have real training data) should show strong out-of-sample
    ROC-AUC -- confirming train/predict wiring is correct, not just the
    bare model in isolation.
    """
    df = _synthetic_labeled_df(n=3000, easy_signal=True)
    results = run_ml_walk_forward(df, target_col="pullback_10pct_30d", window_years=1.5)
    evaluated = results[~results["skipped"]]
    assert len(evaluated) >= 1
    assert (evaluated["roc_auc"].dropna() > 0.85).all()


def test_ml_walk_forward_returns_one_row_per_window_including_skipped():
    df = _synthetic_labeled_df(n=1500)
    from src.backtesting.walk_forward import define_windows

    windows = define_windows(df, window_years=2.0)
    results = run_ml_walk_forward(df, target_col="pullback_10pct_30d", window_years=2.0)
    assert len(results) == len(windows)
