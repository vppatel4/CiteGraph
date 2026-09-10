"""The logistic-regression citation classifier.

Five interpretable features (see features.py) -> probability that the chunk
supports the claim. Standardizing the features first keeps the learned
coefficients comparable to each other. Small, fast, and easy to reason about;
the evaluation shows whether it actually beats the plain threshold.
"""
from __future__ import annotations

import os

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def new_model() -> Pipeline:
    return Pipeline(
        steps=[
            ("scale", StandardScaler()),
            ("lr", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )


def train(features: np.ndarray, labels: np.ndarray) -> Pipeline:
    model = new_model()
    model.fit(features, labels)
    return model


def save(model: Pipeline, path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    joblib.dump(model, path)


def load(path: str) -> Pipeline | None:
    if not os.path.exists(path):
        return None
    return joblib.load(path)


def predict_proba(model: Pipeline, features: list[float]) -> float:
    arr = np.asarray([features], dtype=np.float32)
    return float(model.predict_proba(arr)[0, 1])
