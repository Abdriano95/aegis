"""PatternLayer: iterates registered recognizers and aggregates their findings."""

from __future__ import annotations

from gdpr_classifier.core import Finding

from .recognizer import Recognizer
from .recognizers import (
    EmailRecognizer,
    IbanRecognizer,
    PersonnummerRecognizer,
    TelefonRecognizer,
)


class PatternLayer:
    def __init__(self, recognizers: list[Recognizer] | None = None):
        if recognizers is None:
            recognizers = [
                PersonnummerRecognizer(),
                EmailRecognizer(),
                TelefonRecognizer(),
                IbanRecognizer(),
            ]
        self._recognizers: list[Recognizer] = list(recognizers)

    @property
    def name(self) -> str:
        return "pattern"

    def detect(self, text: str) -> list[Finding]:
        findings: list[Finding] = []
        for recognizer in self._recognizers:
            findings.extend(recognizer.recognize(text))
        return findings
