"""Confusion matrix.

Defines the ConfusionMatrix class, which accumulates true positives,
false positives, and false negatives (optionally broken down per
GDPR category) produced by the matcher during evaluation.
"""

from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict

from evaluation.matcher import MatchResult
from gdpr_classifier.core.category import Category


class ConfusionMatrix:
    def __init__(self) -> None:
        self.total_tp: int = 0
        self.total_fp: int = 0
        self.total_fn: int = 0

        self.category_tp: DefaultDict[Category, int] = defaultdict(int)
        self.category_fp: DefaultDict[Category, int] = defaultdict(int)
        self.category_fn: DefaultDict[Category, int] = defaultdict(int)

        self.layer_tp: DefaultDict[str, int] = defaultdict(int)
        self.layer_fp: DefaultDict[str, int] = defaultdict(int)
        self.layer_fn: DefaultDict[str, int] = defaultdict(int)

    def add_match_result(self, result: MatchResult) -> None:
        # True positives
        for p, e in result.true_positives:
            self.total_tp += 1
            self.category_tp[e.category] += 1
            layer = p.source.split(".")[0]
            self.layer_tp[layer] += 1

        # False positives
        for p in result.false_positives:
            self.total_fp += 1
            self.category_fp[p.category] += 1
            layer = p.source.split(".")[0]
            self.layer_fp[layer] += 1

        # False negatives
        for e in result.false_negatives:
            self.total_fn += 1
            self.category_fn[e.category] += 1

    def get_total_stats(self) -> tuple[int, int, int]:
        return self.total_tp, self.total_fp, self.total_fn

    def get_category_stats(self, category: Category) -> tuple[int, int, int]:
        return self.category_tp[category], self.category_fp[category], self.category_fn[category]

    def get_layer_stats(self, layer: str) -> tuple[int, int, int]:
        return self.layer_tp[layer], self.layer_fp[layer], self.layer_fn[layer]
