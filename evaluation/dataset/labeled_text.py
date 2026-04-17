"""LabeledText dataclass.

Represents a single evaluation sample: the raw text and the list of
expected LabeledFinding ground-truth annotations the classifier is
supposed to produce for that text.
"""
from __future__ import annotations

from dataclasses import dataclass

from .labeled_finding import LabeledFinding


@dataclass(frozen=True)
class LabeledText:
    text: str
    expected_findings: list[LabeledFinding]
    description: str = ""
