from __future__ import annotations

"""Evaluation metrics.

Implements the standard information-retrieval metrics used to assess
the classifier: ``recall()``, ``precision()``, and ``f1()``, computed
from the counts stored in a ConfusionMatrix.
"""

def recall(tp: int, fn: int) -> float:
    denominator = tp + fn
    if denominator == 0:
        return 0.0
    return tp / denominator

def precision(tp: int, fp: int) -> float:
    denominator = tp + fp
    if denominator == 0:
        return 0.0
    return tp / denominator

def f1(tp: int, fp: int, fn: int) -> float:
    p = precision(tp, fp)
    r = recall(tp, fn)
    denominator = p + r
    if denominator == 0.0:
        return 0.0
    return 2 * (p * r) / denominator
