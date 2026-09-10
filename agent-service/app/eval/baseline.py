"""The baseline verifier: a single similarity threshold.

This is the "obvious" approach — if the claim and the cited chunk are similar
enough, call it supported. It's the thing the logistic-regression classifier has
to beat in the evaluation.
"""
from __future__ import annotations

LABEL_TO_INT = {"supports": 1, "does_not_support": 0}


def label_to_int(label: str) -> int:
    key = label.strip().lower().replace(" ", "_").replace("-", "_")
    if key in ("does_not_support", "not_support", "no", "unsupported", "0"):
        return 0
    if key in ("supports", "support", "yes", "supported", "1"):
        return 1
    raise ValueError(f"unknown label: {label!r}")


def predict(similarity: float, threshold: float) -> int:
    return 1 if similarity >= threshold else 0
