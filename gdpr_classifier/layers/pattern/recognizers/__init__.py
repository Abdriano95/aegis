"""Concrete pattern recognizers.

Collection of concrete Recognizer implementations used by the
PatternLayer: Swedish personnummer, email addresses, Swedish phone
numbers, and IBAN.
"""

from __future__ import annotations

from .email import EmailRecognizer
from .personnummer import PersonnummerRecognizer
from .telefon import TelefonRecognizer

__all__ = ["EmailRecognizer", "PersonnummerRecognizer", "TelefonRecognizer"]
