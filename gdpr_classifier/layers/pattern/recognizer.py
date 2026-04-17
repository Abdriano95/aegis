"""Recognizer protocol.

Defines the Recognizer protocol used by the pattern layer. A
recognizer exposes the GDPR category it detects, a ``source_name``
identifying it in findings, and a ``recognize(text: str)`` method
returning the list of Findings produced from the input text.
"""
