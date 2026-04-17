"""Evaluation package.

Tools for evaluating the GDPR classifier against labeled test data:
dataset loading, span-level matching of predictions against ground
truth, confusion matrix construction, metrics (precision, recall,
F1), and a runner that ties it all together.
"""

from .matcher import MatchResult, match

__all__ = ["MatchResult", "match"]
