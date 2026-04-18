"""Swedish phone number recognizer (regex)."""

from __future__ import annotations

import re

from gdpr_classifier.core import Category, Finding

_PATTERN = re.compile(
    r"(?<![\d+])"
    r"(?:\((?:\+46|0046)\)|\+46|0046|0)"
    r"[-\s]?[1-9]"
    r"(?:[-\s]?\d){6,8}"
    r"(?!\d)"
)


class TelefonRecognizer:
    """Recognizer for Swedish phone numbers via regex."""

    @property
    def category(self) -> Category:
        return Category.TELEFONNUMMER

    @property
    def source_name(self) -> str:
        return "regex_telefon"

    def recognize(self, text: str) -> list[Finding]:
        findings: list[Finding] = []
        for match in _PATTERN.finditer(text):
            findings.append(
                Finding(
                    category=Category.TELEFONNUMMER,
                    start=match.start(),
                    end=match.end(),
                    text_span=match.group(),
                    confidence=0.9,
                    source="pattern.regex_telefon",
                    metadata=None,
                )
            )
        return findings
