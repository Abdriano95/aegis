"""Evaluation package.

Tools for evaluating the GDPR classifier against labeled test data:
dataset loading, span-level matching of predictions against ground
truth, confusion matrix construction, metrics (precision, recall,
F1), and a runner that ties it all together.
"""

from .confusion_matrix import ConfusionMatrix
from .matcher import MatchResult, match
from .metrics import f1, precision, recall
from .report import MechanismStats, Report, RunMetrics, print_report
from .runner import run_evaluation

__all__ = [
    "ConfusionMatrix",
    "MatchResult",
    "MechanismStats",
    "Report",
    "RunMetrics",
    "f1",
    "match",
    "precision",
    "print_report",
    "recall",
    "run_evaluation",
]
