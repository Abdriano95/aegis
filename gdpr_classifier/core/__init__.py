"""Core domain primitives for the GDPR classifier."""

from __future__ import annotations

from .category import Category
from .classification import Classification, SensitivityLevel
from .finding import Finding
from .layer import Layer

__all__ = [
    "Category",
    "Classification",
    "Finding",
    "Layer",
    "SensitivityLevel",
]
