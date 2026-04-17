"""Report data model and printing features."""

from __future__ import annotations

from dataclasses import dataclass

from gdpr_classifier.core.category import Category


@dataclass(frozen=True)
class RunMetrics:
    tp: int
    fp: int
    fn: int
    recall: float
    precision: float
    f1: float


@dataclass(frozen=True)
class Report:
    total: RunMetrics
    per_category: dict[Category, RunMetrics]
    per_layer: dict[str, RunMetrics]


def print_report(report: Report) -> None:
    print("=" * 60)
    print("EVALUATION REPORT")
    print("=" * 60)
    print("\n--- Total Metrics ---")
    print(f"TP: {report.total.tp:<5} FP: {report.total.fp:<5} FN: {report.total.fn:<5}")
    print(f"Precision: {report.total.precision:.2%}")
    print(f"Recall:    {report.total.recall:.2%}")
    print(f"F1 Score:  {report.total.f1:.2%}")

    print("\n--- Metrics per Category ---")
    for category, metrics in sorted(report.per_category.items(), key=lambda x: x[0].value):
        print(f"Category: {category.value}")
        print(f"  TP: {metrics.tp:<5} FP: {metrics.fp:<5} FN: {metrics.fn:<5}")
        print(f"  Precision: {metrics.precision:.2%} | Recall: {metrics.recall:.2%} | F1: {metrics.f1:.2%}")

    print("\n--- Metrics per Layer ---")
    if not report.per_layer:
        print("  No layer-level findings.")
    for layer, metrics in sorted(report.per_layer.items()):
        print(f"Layer: {layer}")
        print(f"  TP: {metrics.tp:<5} FP: {metrics.fp:<5} FN: {metrics.fn:<5}")
        print(f"  Precision: {metrics.precision:.2%} | Recall: N/A | F1: N/A")
    print("=" * 60)
