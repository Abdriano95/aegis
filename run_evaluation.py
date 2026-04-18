"""Run the full evaluation pipeline against the iteration 1 test dataset."""

from __future__ import annotations

from gdpr_classifier import Aggregator, Pipeline
from gdpr_classifier.layers.pattern import PatternLayer
from gdpr_classifier.layers.entity import EntityLayer
from gdpr_classifier.layers.context import ContextLayer
from evaluation.dataset.loader import load_dataset
from evaluation.runner import run_evaluation
from evaluation.report import print_report


def main() -> None:
    pipeline = Pipeline(
        layers=[PatternLayer(), EntityLayer(), ContextLayer()],
        aggregator=Aggregator(),
    )
    dataset = load_dataset("tests/data/iteration_1/test_dataset.json")
    report = run_evaluation(pipeline, dataset)
    print_report(report)


if __name__ == "__main__":
    main()
