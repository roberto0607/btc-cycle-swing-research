"""
Milestone 12 ML baseline model (RESEARCH_SPEC.md section 33: "Do NOT
begin with a neural network. Start with Logistic Regression.").

A single sklearn Pipeline (StandardScaler -> LogisticRegression). The
scaler is fit ONLY on training data and applied unchanged to test data
(section 38: "fit preprocessing on training data... never fit scalers on
the entire dataset") -- sklearn's Pipeline.fit/.predict_proba enforces
this automatically as long as the caller never calls .fit() on test data,
which walk_forward_ml.py is responsible for getting right.
"""

from __future__ import annotations

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 42


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)),
        ]
    )


def fit(X_train: pd.DataFrame, y_train: pd.Series) -> Pipeline:
    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)
    return pipeline


def predict_proba(pipeline: Pipeline, X: pd.DataFrame) -> pd.Series:
    """Probability of the POSITIVE class (pullback=True), aligned to X's index."""
    proba = pipeline.predict_proba(X)[:, 1]
    return pd.Series(proba, index=X.index, name="predicted_pullback_probability")
