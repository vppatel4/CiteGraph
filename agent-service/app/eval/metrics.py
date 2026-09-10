"""Plain-Python precision / recall / F1 / accuracy for binary labels.

Written out by hand (no sklearn import needed) so the numbers are obviously
correct and the module can be unit-tested on its own. Positive class = 1 =
"supports".
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Scores:
    accuracy: float
    precision: float
    recall: float
    f1: float
    tp: int
    fp: int
    tn: int
    fn: int

    def as_row(self) -> str:
        return (
            f"{self.accuracy:.3f} | {self.precision:.3f} | "
            f"{self.recall:.3f} | {self.f1:.3f}"
        )


def score(y_true: list[int], y_pred: list[int]) -> Scores:
    if len(y_true) != len(y_pred):
        raise ValueError("length mismatch")
    tp = fp = tn = fn = 0
    for t, p in zip(y_true, y_pred):
        if p == 1 and t == 1:
            tp += 1
        elif p == 1 and t == 0:
            fp += 1
        elif p == 0 and t == 0:
            tn += 1
        else:
            fn += 1
    n = len(y_true) or 1
    accuracy = (tp + tn) / n
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return Scores(accuracy, precision, recall, f1, tp, fp, tn, fn)
