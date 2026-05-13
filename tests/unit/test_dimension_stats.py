"""Unit tests for per-dimension statistics.

Verifies that:
  a) DimensionStats defaults to all-zeros on a bare Report construction
  b) run_evaluation accumulates per-dimension counters correctly across
     a mixed dataset under the kategorisk modell (Beslut 49 reviderad):
     Identifiability NONE/INDIRECT/DIRECT and DataClass NONE/SPECIAL/CRIMINAL.
  c) Classification with default NONE/NONE counts as NONE/NONE
  d) print_report outputs the Per Dimension section with both sub-headers

MechanismStats and per_mechanism togs bort i Beslut 49 reviderad fixup —
klassifikationen kommuniceras helt av (identifiability, data_class)-paret.
"""

from __future__ import annotations

from evaluation.dataset.labeled_text import LabeledText
from evaluation.report import (
    DimensionStats,
    Report,
    RunMetrics,
    print_report,
)
from evaluation.runner import run_evaluation
from gdpr_classifier.core import SensitivityLevel
from gdpr_classifier.core.classification import Classification, DataClass, Identifiability


def _zero_metrics() -> RunMetrics:
    return RunMetrics(tp=0, fp=0, fn=0, recall=0.0, precision=0.0, f1=0.0)


class _DummyPipeline:
    """Returns pre-built Classification objects in sequence."""

    def __init__(self, results: list[Classification]) -> None:
        self._results = list(results)

    def classify(self, text: str) -> Classification:
        return self._results.pop(0)


def _make_classification(
    sensitivity: SensitivityLevel,
    identifiability: Identifiability = Identifiability.NONE,
    data_class: DataClass = DataClass.NONE,
) -> Classification:
    return Classification(
        findings=[],
        sensitivity=sensitivity,
        active_layers=[],
        overlapping_findings=[],
        identifiability=identifiability,
        data_class=data_class,
    )


class TestDimensionStats:
    """Per-dimension counter accumulation across the dataset."""

    def test_dimension_stats_default_in_bare_report(self) -> None:
        """Report constructed without per_dimension gets all-zero DimensionStats."""
        report = Report(total=_zero_metrics(), per_category={}, per_layer={})
        assert report.per_dimension == DimensionStats()
        assert report.per_dimension.identifiability_none == 0
        assert report.per_dimension.identifiability_indirect == 0
        assert report.per_dimension.identifiability_direct == 0
        assert report.per_dimension.data_class_none == 0
        assert report.per_dimension.data_class_special == 0
        assert report.per_dimension.data_class_criminal == 0

    def test_run_evaluation_counts_dimensions(self) -> None:
        """run_evaluation accumulates per-dimension counters correctly."""
        results = [
            _make_classification(SensitivityLevel.HIGH, Identifiability.DIRECT, DataClass.SPECIAL),
            _make_classification(SensitivityLevel.HIGH, Identifiability.DIRECT, DataClass.SPECIAL),
            _make_classification(SensitivityLevel.MEDIUM, Identifiability.INDIRECT, DataClass.SPECIAL),
            _make_classification(SensitivityLevel.MEDIUM, Identifiability.INDIRECT, DataClass.CRIMINAL),
            _make_classification(SensitivityLevel.LOW, Identifiability.DIRECT, DataClass.NONE),
            _make_classification(SensitivityLevel.NONE, Identifiability.NONE, DataClass.NONE),
            _make_classification(SensitivityLevel.LOW, Identifiability.NONE, DataClass.SPECIAL),
        ]
        pipeline = _DummyPipeline(results)
        dataset = [
            LabeledText(text=str(i), expected_findings=[], description="")
            for i in range(len(results))
        ]

        report = run_evaluation(pipeline, dataset)

        assert report.per_dimension == DimensionStats(
            identifiability_none=2,
            identifiability_indirect=2,
            identifiability_direct=3,
            data_class_none=2,
            data_class_special=4,
            data_class_criminal=1,
        )

    def test_run_evaluation_dimension_defaults_count_as_none(self) -> None:
        """Classification with default NONE/NONE counts as identifiability_none + data_class_none."""
        classification = Classification(
            findings=[],
            sensitivity=SensitivityLevel.NONE,
            active_layers=[],
            overlapping_findings=[],
            # identifiability and data_class omitted → default to NONE
        )
        pipeline = _DummyPipeline([classification])
        dataset = [LabeledText(text="x", expected_findings=[], description="")]

        report = run_evaluation(pipeline, dataset)

        assert report.per_dimension.identifiability_none == 1
        assert report.per_dimension.data_class_none == 1
        assert report.per_dimension.identifiability_indirect == 0
        assert report.per_dimension.identifiability_direct == 0
        assert report.per_dimension.data_class_special == 0
        assert report.per_dimension.data_class_criminal == 0

    def test_print_report_includes_per_dimension_section(self, capsys) -> None:
        """print_report outputs the Per Dimension section with both sub-headers."""
        stats = DimensionStats(
            identifiability_none=1,
            identifiability_indirect=2,
            identifiability_direct=3,
            data_class_none=4,
            data_class_special=5,
            data_class_criminal=6,
        )
        report = Report(
            total=_zero_metrics(),
            per_category={},
            per_layer={},
            per_dimension=stats,
        )
        print_report(report)
        captured = capsys.readouterr().out

        assert "Per Dimension" in captured
        assert "Identifiability" in captured
        assert "Data class" in captured
        assert "INDIRECT" in captured
        assert "DIRECT" in captured
        assert "SPECIAL" in captured
        assert "CRIMINAL" in captured
        for n in range(1, 7):
            assert str(n) in captured
