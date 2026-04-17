"""Swedish personnummer recognizer (regex + Luhn)."""

from __future__ import annotations

import re

from gdpr_classifier.core import Category, Finding

_PATTERN = re.compile(
    r"(?<!\d)("
    r"\d{8}[-+]\d{4}"
    r"|\d{12}"
    r"|\d{6}[-+]\d{4}"
    r"|\d{10}"
    r")(?!\d)"
)


def _luhn_valid(ten_digits: str) -> bool:
    total = 0
    for i, ch in enumerate(ten_digits):
        d = ord(ch) - ord("0")
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _is_valid_date(mm: int, dd: int) -> bool:
    if not 1 <= mm <= 12:
        return False
    if 1 <= dd <= 31:
        return True
    if 61 <= dd <= 91:
        return True
    return False


class PersonnummerRecognizer:
    """Recognizer for Swedish personnummer validated with Luhn."""

    @property
    def category(self) -> Category:
        return Category.PERSONNUMMER

    @property
    def source_name(self) -> str:
        return "luhn_personnummer"

    def recognize(self, text: str) -> list[Finding]:
        findings: list[Finding] = []
        for match in _PATTERN.finditer(text):
            span = match.group(1)
            digits = span.replace("-", "").replace("+", "")
            ten = digits[-10:]
            mm = int(ten[2:4])
            dd = int(ten[4:6])
            if not _is_valid_date(mm, dd):
                continue
            if not _luhn_valid(ten):
                continue
            findings.append(
                Finding(
                    category=Category.PERSONNUMMER,
                    start=match.start(1),
                    end=match.end(1),
                    text_span=span,
                    confidence=1.0,
                    source="pattern.luhn_personnummer",
                    metadata=None,
                )
            )
        return findings
