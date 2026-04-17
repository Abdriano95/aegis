"""Concrete pattern recognizers.

Collection of concrete Recognizer implementations used by the
PatternLayer: Swedish personnummer, email addresses, Swedish phone
numbers, and IBAN.
"""

from __future__ import annotations

from .email import EmailRecognizer
from .personnummer import PersonnummerRecognizer

__all__ = ["EmailRecognizer", "PersonnummerRecognizer"]
