"""End-to-end integration test: pipeline + evaluation against the iteration 1 dataset."""

from __future__ import annotations

from gdpr_classifier import Aggregator, Pipeline
from gdpr_classifier.layers.pattern import PatternLayer
from gdpr_classifier.layers.entity import EntityLayer
from gdpr_classifier.layers.context import ContextLayer
from evaluation.dataset.loader import load_dataset
from evaluation.runner import run_evaluation
from evaluation.report import print_report


def test_end_to_end_pipeline_evaluation() -> None:
    pipeline = Pipeline(
        layers=[PatternLayer(), EntityLayer(), ContextLayer()],
        aggregator=Aggregator(),
    )
    dataset = load_dataset("tests/data/iteration_1/test_dataset.json")

    report = run_evaluation(pipeline, dataset)

    assert report is not None
    assert report.total.recall > 0, (
        "Testdatan innehåller matchbara mönster (personnummer/email/telefon/"
        "IBAN/betalkort); total recall måste vara > 0."
    )

    print_report(report)
