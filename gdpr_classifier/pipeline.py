"""Detection pipeline.

Defines the Pipeline, which orchestrates the configured active layers:
it feeds the input text through each layer, collects their findings,
and hands the combined result to the aggregator for merging and
final classification.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from gdpr_classifier.core import Classification, Finding, Layer

if TYPE_CHECKING:
    from gdpr_classifier.aggregator import Aggregator


class Pipeline:
    def __init__(self, layers: list[Layer], aggregator: Aggregator) -> None:
        self.layers = list(layers)
        self.aggregator = aggregator

    def classify(self, text: str) -> Classification:
        all_findings: list[Finding] = []
        for layer in self.layers:
            all_findings.extend(layer.detect(text))
        return self.aggregator.aggregate(
            findings=all_findings,
            active_layers=[layer.name for layer in self.layers],
        )
