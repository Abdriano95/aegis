"""Unit tests for per-mechanism statistics (Issue #75, I-8).

Verifies that:
  a) Aggregator sets mechanism_used="article9" for article9.* findings
  b) Aggregator sets mechanism_used="bypass" for high-confidence kombination
  c) Aggregator sets mechanism_used="mechanism3" for mekanism-3-qualified kombination
  d) Aggregator sets mechanism_used="low" for article4.* without MEDIUM/HIGH trigger
  e) Aggregator sets mechanism_used="none" for empty findings
  f) article9 takes priority over bypass when both are present
  g) run_evaluation accumulates MechanismStats correctly across a mixed dataset
  h) MechanismStats defaults to all-zeros on a bare Report construction
  i) print_report includes Per Mechanism section in stdout
"""

from __future__ import annotations

import io
from unittest.mock import patch

from evaluation.dataset.labeled_text import LabeledText
from evaluation.report import MechanismStats, Report, RunMetrics, print_report
from evaluation.runner import run_evaluation
from gdpr_classifier.aggregator import Aggregator
from gdpr_classifier.core import Category, Finding, SensitivityLevel
from gdpr_classifier.core.classification import Classification


def _make_finding(
    category: Category,
    start: int,
    end: int,
    *,
    confidence: float = 1.0,
    source: str = "test",
) -> Finding:
    return Finding(
        category=category,
        start=start,
        end=end,
        text_span="x" * (end - start),
        confidence=confidence,
        source=source,
    )


def _zero_metrics() -> RunMetrics:
    return RunMetrics(tp=0, fp=0, fn=0, recall=0.0, precision=0.0, f1=0.0)


class TestMechanismUsedOnClassification:
    """Aggregator.aggregate sets mechanism_used correctly for each decision path."""

    def test_article9_sets_mechanism(self) -> None:
        halsodata = _make_finding(
            Category.HALSODATA, start=0, end=10, source="article9.halsodata"
        )
        result = Aggregator().aggregate(findings=[halsodata], active_layers=["article9"])
        assert result.mechanism_used == "article9"

    def test_bypass_sets_mechanism(self) -> None:
        kombination = _make_finding(
            Category.KOMBINATION,
            start=0,
            end=50,
            confidence=0.9,  # >= high_confidence_bypass default 0.85
            source="context.kombination",
        )
        result = Aggregator().aggregate(findings=[kombination], active_layers=["combination"])
        assert result.mechanism_used == "bypass"

    def test_mechanism3_sets_mechanism(self) -> None:
        kombination = _make_finding(
            Category.KOMBINATION,
            start=0,
            end=60,
            confidence=0.75,  # >= medium_threshold 0.7, < bypass 0.85
            source="context.kombination",
        )
        namn = _make_finding(Category.NAMN, start=0, end=15, source="entity.spacy_PRS")
        email = _make_finding(Category.EMAIL, start=20, end=45, source="pattern.regex_email")

        result = Aggregator().aggregate(
            findings=[kombination, namn, email],
            active_layers=["pattern", "entity", "combination"],
        )
        assert result.mechanism_used == "mechanism3"

    def test_low_sets_mechanism(self) -> None:
        email = _make_finding(Category.EMAIL, start=0, end=20, source="pattern.regex_email")
        result = Aggregator().aggregate(findings=[email], active_layers=["pattern"])
        assert result.mechanism_used == "low"

    def test_none_sets_mechanism(self) -> None:
        result = Aggregator().aggregate(findings=[], active_layers=["pattern"])
        assert result.mechanism_used == "none"

    def test_article9_priority_over_bypass(self) -> None:
        halsodata = _make_finding(
            Category.HALSODATA, start=0, end=10, source="article9.halsodata"
        )
        kombination = _make_finding(
            Category.KOMBINATION,
            start=0,
            end=50,
            confidence=0.9,
            source="context.kombination",
        )
        result = Aggregator().aggregate(
            findings=[halsodata, kombination],
            active_layers=["article9", "combination"],
        )
        assert result.mechanism_used == "article9"
        assert result.sensitivity == SensitivityLevel.HIGH


class _DummyPipeline:
    """Returns pre-built Classification objects in sequence."""

    def __init__(self, results: list[Classification]) -> None:
        self._results = list(results)

    def classify(self, text: str) -> Classification:
        return self._results.pop(0)


def _make_classification(mechanism: str) -> Classification:
    sensitivity_map = {
        "article9": SensitivityLevel.HIGH,
        "bypass": SensitivityLevel.MEDIUM,
        "mechanism3": SensitivityLevel.MEDIUM,
        "low": SensitivityLevel.LOW,
        "none": SensitivityLevel.NONE,
    }
    return Classification(
        findings=[],
        sensitivity=sensitivity_map[mechanism],
        active_layers=[],
        overlapping_findings=[],
        mechanism_used=mechanism,
    )


def test_run_evaluation_counts_mechanisms() -> None:
    """run_evaluation accumulates per-mechanism counters correctly."""
    mechanisms = ["article9", "article9", "bypass", "mechanism3", "low", "none", "none"]
    results = [_make_classification(m) for m in mechanisms]
    pipeline = _DummyPipeline(results)
    dataset = [LabeledText(text=str(i), expected_findings=[], description="") for i in range(len(mechanisms))]

    report = run_evaluation(pipeline, dataset)

    assert report.per_mechanism == MechanismStats(
        high_via_article9=2,
        medium_via_bypass=1,
        medium_via_mechanism3=1,
        low_count=1,
        none_count=2,
    )


def test_run_evaluation_none_mechanism_used_counts_as_none() -> None:
    """mechanism_used=None (backward-compat path) is counted as none."""
    classification = Classification(
        findings=[],
        sensitivity=SensitivityLevel.NONE,
        active_layers=[],
        overlapping_findings=[],
        # mechanism_used omitted → defaults to None
    )
    pipeline = _DummyPipeline([classification])
    dataset = [LabeledText(text="x", expected_findings=[], description="")]

    report = run_evaluation(pipeline, dataset)

    assert report.per_mechanism.none_count == 1


def test_mechanism_stats_default_in_bare_report() -> None:
    """Report constructed without per_mechanism gets all-zero MechanismStats."""
    report = Report(total=_zero_metrics(), per_category={}, per_layer={})
    assert report.per_mechanism == MechanismStats(0, 0, 0, 0, 0)


def test_print_report_includes_per_mechanism_section(capsys) -> None:
    """print_report always outputs the Per Mechanism section."""
    stats = MechanismStats(
        high_via_article9=3,
        medium_via_bypass=1,
        medium_via_mechanism3=2,
        low_count=5,
        none_count=4,
    )
    report = Report(
        total=_zero_metrics(),
        per_category={},
        per_layer={},
        per_mechanism=stats,
    )
    print_report(report)
    captured = capsys.readouterr().out

    assert "Per Mechanism" in captured
    assert "3" in captured  # high_via_article9
    assert "1" in captured  # medium_via_bypass
    assert "2" in captured  # medium_via_mechanism3
    assert "5" in captured  # low_count
    assert "4" in captured  # none_count
