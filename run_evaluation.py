"""Run the full evaluation pipeline against the combined iteration 1 + 2 dataset."""

from __future__ import annotations

from gdpr_classifier import Aggregator, Pipeline
from gdpr_classifier.config import get_llm_provider
from gdpr_classifier.layers.pattern import PatternLayer
from gdpr_classifier.layers.entity import EntityLayer
from gdpr_classifier.layers.article9 import Article9Layer
from gdpr_classifier.layers.combination import CombinationLayer
from evaluation.dataset.loader import load_dataset
from evaluation.runner import run_evaluation
from evaluation.report import print_report

_MODEL = "qwen2.5:7b-instruct"


def main() -> None:
    provider = get_llm_provider(_MODEL)
    pipeline = Pipeline(
        layers=[
            PatternLayer(),
            EntityLayer(),
            Article9Layer(provider),
            CombinationLayer(provider),
        ],
        aggregator=Aggregator(),
    )
    dataset = (
        load_dataset("tests/data/iteration_1/test_dataset.json")
        + load_dataset("tests/data/iteration_2/article9_dataset.json")
        + load_dataset("tests/data/iteration_2/combination_dataset.json")
    )
    report = run_evaluation(pipeline, dataset)
    print_report(report, verbose=True)


if __name__ == "__main__":
    main()
