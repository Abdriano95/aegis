"""Finding dataclass."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

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
    evidence_basis: Literal[     # vilken evidensgrund fyndet tilläts påverka dimensionsbestämningen på
        "structural_support",        # >= min_evidence_count giltiga stödfynd överlappar
        "high_confidence_no_support", # passerade bypass utan strukturellt stöd
        "no_support_required",       # policy kräver inget stöd (R1/R2/R5); även default i legacy
    ] = "no_support_required"    # default = bakåtkompatibel/tyst i legacy (arkitektur.md §9.6.3)
