"""Finding dataclass."""

from __future__ import annotations

from dataclasses import dataclass

from .category import Category


@dataclass(frozen=True)
class Finding:
    category: Category
    start: int
    end: int
    text_span: str
    confidence: float
    source: str
    metadata: dict | None = None
