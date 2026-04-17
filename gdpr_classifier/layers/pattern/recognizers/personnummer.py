"""Swedish personnummer recognizer.

Detects Swedish personal identity numbers (personnummer) in text
using a regular expression to locate candidates and the Luhn
algorithm to validate the check digit, reducing false positives.
"""
