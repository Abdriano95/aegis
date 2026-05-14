"""Run the full evaluation pipeline against the combined iteration 1 + 2 dataset."""

from __future__ import annotations

import argparse  # TEMP I-6 calibration, remove before commit

from gdpr_classifier import Aggregator, Pipeline
from gdpr_classifier.aggregator import (  # TEMP I-6 calibration, remove before commit
    get_mechanism3_count,
    reset_mechanism3_counter,
)
from gdpr_classifier.config import get_llm_provider
from gdpr_classifier.layers.pattern import PatternLayer
from gdpr_classifier.layers.entity import EntityLayer
from gdpr_classifier.layers.article9 import Article9Layer
from gdpr_classifier.layers.combination import CombinationLayer
from evaluation.dataset.loader import load_dataset
from evaluation.runner import run_evaluation
from evaluation.report import print_report

_MODEL = "qwen2.5:7b-instruct"


# TEMP I-6 calibration, remove before commit
def _parse_args() -> argparse.Namespace:
    """TEMP I-6 calibration, remove before commit"""
    parser = argparse.ArgumentParser(description="Run GDPR evaluation pipeline.")
    parser.add_argument("--medium-threshold", type=float, default=None)
    parser.add_argument("--high-confidence-bypass", type=float, default=None)
    parser.add_argument("--min-evidence-count", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()  # TEMP I-6 calibration, remove before commit
    # TEMP I-6 calibration, remove before commit
    aggregator_kwargs = {}
    if args.medium_threshold is not None:
        aggregator_kwargs["medium_threshold"] = args.medium_threshold
    if args.high_confidence_bypass is not None:
        aggregator_kwargs["high_confidence_bypass"] = args.high_confidence_bypass
    if args.min_evidence_count is not None:
        aggregator_kwargs["min_evidence_count"] = args.min_evidence_count

    provider = get_llm_provider(_MODEL)
    pipeline = Pipeline(
        layers=[
            PatternLayer(),
            EntityLayer(),
            Article9Layer(provider),
            CombinationLayer(provider),
        ],
        aggregator=Aggregator(**aggregator_kwargs),  # TEMP I-6 calibration, remove before commit
    )
    dataset = (
        load_dataset("tests/data/iteration_1/test_dataset.json")
        + load_dataset("tests/data/iteration_2/article9_dataset.json")
        + load_dataset("tests/data/iteration_2/combination_dataset.json")
    )
    reset_mechanism3_counter()  # TEMP I-6 calibration, remove before commit
    report = run_evaluation(pipeline, dataset)
    print_report(report, verbose=True)
    # TEMP I-6 calibration, remove before commit
    print(f"Mekanism 3 pass count: {get_mechanism3_count()}")


if __name__ == "__main__":
    main()
