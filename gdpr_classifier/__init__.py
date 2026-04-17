"""gdpr-classifier package.

Top-level package for the layered GDPR text classification pipeline.
Combines pattern matching, named entity recognition, and contextual
analysis to identify personal data (Art. 4) and sensitive data (Art. 9).
"""

from __future__ import annotations

from gdpr_classifier.aggregator import Aggregator
from gdpr_classifier.pipeline import Pipeline

__all__ = ["Aggregator", "Pipeline"]
