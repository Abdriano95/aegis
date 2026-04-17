"""Pattern-based detection layer.

Contains the PatternLayer, the Recognizer protocol, and the concrete
recognizers that identify personal data via regular expressions and
checksum validation (e.g. Swedish personnummer, email, phone, IBAN).
"""

from __future__ import annotations

from .pattern_layer import PatternLayer
from .recognizer import Recognizer

__all__ = ["PatternLayer", "Recognizer"]
