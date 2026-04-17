"""Recognizer protocol for the pattern layer.

Konvention: en recognizer ansvarar själv för att sätta hela
``Finding.source``-strängen på formen ``"pattern.<source_name>"``
(t.ex. ``"pattern.luhn_personnummer"``). ``source_name`` exponeras
separat som den lager-lokala identifieraren för spärbarhet och
registerlogik. ``PatternLayer`` gör ingen efterbearbetning av
``source``-fältet.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from gdpr_classifier.core import Category, Finding


@runtime_checkable
class Recognizer(Protocol):
    @property
    def category(self) -> Category:
        """Den GDPR-kategori denna recognizer detekterar."""
        ...

    @property
    def source_name(self) -> str:
        """Lager-lokal identifierare, t.ex. ``'luhn_personnummer'``."""
        ...

    def recognize(self, text: str) -> list[Finding]:
        """Analysera ``text`` och returnera fynd f\u00f6r recognizerns kategori."""
        ...
