"""Report data model and printing features."""

from __future__ import annotations

from dataclasses import dataclass, field

from evaluation.dataset.labeled_finding import LabeledFinding
from gdpr_classifier.core.category import Category
from gdpr_classifier.core.finding import Finding


@dataclass(frozen=True)
class RunMetrics:
    tp: int
    fp: int
    fn: int
    recall: float
    precision: float
    f1: float


@dataclass(frozen=True)
class SampleResult:
    text: str
    false_positives: list[Finding]
    false_negatives: list[LabeledFinding]


@dataclass(frozen=True)
class MechanismStats:
    high_via_article9: int
    medium_via_bypass: int
    medium_via_mechanism3: int
    low_count: int
    none_count: int


@dataclass(frozen=True)
class Report:
    total: RunMetrics
    per_category: dict[Category, RunMetrics]
    per_layer: dict[str, RunMetrics]
    samples: list[SampleResult] = field(default_factory=list)
    per_mechanism: MechanismStats = field(
        default_factory=lambda: MechanismStats(0, 0, 0, 0, 0)
    )


def _context_snippet(text: str, start: int, end: int, window: int = 20) -> str:
    ctx_start = max(0, start - window)
    ctx_end = min(len(text), end + window)
    prefix = "..." if ctx_start > 0 else ""
    suffix = "..." if ctx_end < len(text) else ""
    return f"{prefix}{text[ctx_start:ctx_end]}{suffix}"


def print_report(report: Report, verbose: bool = False) -> None:
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

    print("\n--- Per Mechanism ---")
    pm = report.per_mechanism
    print(f"  HIGH  via Article 9:   {pm.high_via_article9}")
    print(f"  MEDIUM via bypass:     {pm.medium_via_bypass}")
    print(f"  MEDIUM via mechanism3: {pm.medium_via_mechanism3}")
    print(f"  LOW:                   {pm.low_count}")
    print(f"  NONE:                  {pm.none_count}")

    if verbose:
        fp_pairs: list[tuple[str, Finding]] = [
            (sample.text, fp) for sample in report.samples for fp in sample.false_positives
        ]
        fn_pairs: list[tuple[str, LabeledFinding]] = [
            (sample.text, fn) for sample in report.samples for fn in sample.false_negatives
        ]

        print(f"\n--- False Positives ({len(fp_pairs)}) ---")
        for text, fp in fp_pairs:
            snippet = _context_snippet(text, fp.start, fp.end)
            print(f'  [{fp.source}] "{fp.text_span}" (start={fp.start}, end={fp.end})')
            print(f'    i text: "{snippet}"')

        print(f"\n--- False Negatives ({len(fn_pairs)}) ---")
        for text, fn in fn_pairs:
            snippet = _context_snippet(text, fn.start, fn.end)
            print(f'  [{fn.category.value}] "{fn.text_span}" (start={fn.start}, end={fn.end})')
            print(f'    i text: "{snippet}"')

    print("=" * 60)
