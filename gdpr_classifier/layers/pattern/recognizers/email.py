"""Email address recognizer (regex)."""

from __future__ import annotations

import re

from gdpr_classifier.core import Category, Finding

_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+\-åäöÅÄÖ]+@[a-zA-Z0-9.\-åäöÅÄÖ]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)


class EmailRecognizer:
    """Recognizer for email addresses via regex."""

    @property
    def category(self) -> Category:
        return Category.EMAIL

    @property
    def source_name(self) -> str:
        return "regex_email"

    def recognize(self, text: str) -> list[Finding]:
        findings: list[Finding] = []
        for match in _PATTERN.finditer(text):
            findings.append(
                Finding(
                    category=Category.EMAIL,
                    start=match.start(),
                    end=match.end(),
                    text_span=match.group(),
                    confidence=1.0,
                    source="pattern.regex_email",
                    metadata=None,
                )
            )
        return findings
