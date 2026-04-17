"""IBAN recognizer (regex + mod97)."""

from __future__ import annotations

import re

from gdpr_classifier.core import Category, Finding

_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])"
    r"[A-Za-z]{2}\d{2}(?:[ ]?[A-Za-z0-9]){10,30}"
    r"(?![A-Za-z0-9])"
)


def _mod97_valid(iban: str) -> bool:
    rearranged = iban[4:] + iban[:4]
    converted_parts: list[str] = []
    for ch in rearranged:
        if ch.isdigit():
            converted_parts.append(ch)
        elif "A" <= ch <= "Z":
            converted_parts.append(str(ord(ch) - 55))
        else:
            return False
    return int("".join(converted_parts)) % 97 == 1


class IbanRecognizer:
    """Recognizer for IBAN numbers validated with ISO 7064 mod97."""

    @property
    def category(self) -> Category:
        return Category.IBAN

    @property
    def source_name(self) -> str:
        return "checksum_iban"

    def recognize(self, text: str) -> list[Finding]:
        findings: list[Finding] = []
        for match in _PATTERN.finditer(text):
            span = match.group()
            normalized = span.replace(" ", "").upper()
            if not 15 <= len(normalized) <= 34:
                continue
            if not _mod97_valid(normalized):
                continue
            findings.append(
                Finding(
                    category=Category.IBAN,
                    start=match.start(),
                    end=match.end(),
                    text_span=span,
                    confidence=1.0,
                    source="pattern.checksum_iban",
                    metadata=None,
                )
            )
        return findings
