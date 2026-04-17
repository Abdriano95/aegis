"""IBAN recognizer.

Detects International Bank Account Numbers (IBAN) in text using a
regular expression to locate candidates and the mod-97 checksum
(ISO 13616) to validate them before emitting a Finding.
"""
