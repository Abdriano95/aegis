"""Payment card recognizer (regex + Luhn)."""

from __future__ import annotations

import re

from gdpr_classifier.core import Category, Finding

_PATTERN = re.compile(
    r"(?<!\d)(?:\d[\s\-]*){12,15}\d(?!\d)"
)


def _luhn_valid(card_number: str) -> bool:
    digits = [int(c) for c in card_number if c.isdigit()]
    if not digits:
        return False
    
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    
    return total % 10 == 0


class BetalkortRecognizer:
    """Recognizer for payment cards validated with Luhn."""

    @property
    def category(self) -> Category:
        return Category.BETALKORT

    @property
    def source_name(self) -> str:
        return "luhn_betalkort"

    def recognize(self, text: str) -> list[Finding]:
        findings: list[Finding] = []
        for match in _PATTERN.finditer(text):
            span = match.group(0)
            if not _luhn_valid(span):
                continue
                
            findings.append(
                Finding(
                    category=Category.BETALKORT,
                    start=match.start(),
                    end=match.end(),
                    text_span=span,
                    confidence=1.0,
                    source="pattern.luhn_betalkort",
                    metadata=None,
                )
            )
        return findings
