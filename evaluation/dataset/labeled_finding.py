"""LabeledFinding dataclass.

Represents a single ground-truth finding in the evaluation dataset:
the expected GDPR category and character span (start, end) of a
piece of personal data in a labeled text.
"""
from __future__ import annotations

from dataclasses import dataclass

from gdpr_classifier.core.category import Category


@dataclass(frozen=True)
class LabeledFinding:
    category: Category
    start: int
    end: int
    text_span: str
