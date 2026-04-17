"""Finding dataclass."""

from __future__ import annotations

from dataclasses import dataclass

from .category import Category


@dataclass(frozen=True)
class Finding:
    category: Category
    start: int                   # startposition i originaltexten
    end: int                     # slutposition i originaltexten
    text_span: str               # den exakta strängen som matchades
    confidence: float            # 0.0 - 1.0 (sannolikhet att det är en personuppgift)
    source: str                  # vilken layer eller recognizer som producerade det (layer_name.recognizer_name)
                                 # exempel: pattern.email_recognizer, pattern.phone_recognizer, etc.
    metadata: dict | None = None # ytterligare metadata om findinget
