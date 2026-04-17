"""Evaluation dataset package.

Data structures and loader used to represent labeled evaluation data:
labeled findings (ground-truth spans), labeled texts (raw text plus
expected findings), and JSON loading utilities.
"""
from __future__ import annotations

from .labeled_finding import LabeledFinding
from .labeled_text import LabeledText
from .loader import load_dataset


__all__ = ["LabeledFinding", "LabeledText", "load_dataset"]
