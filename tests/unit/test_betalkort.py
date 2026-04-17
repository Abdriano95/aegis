"""Unit tests for the BetalkortRecognizer."""

from __future__ import annotations

from gdpr_classifier.core.category import Category
from gdpr_classifier.layers.pattern.recognizers.betalkort import BetalkortRecognizer


def test_betalkort_recognizer_visa():
    # Arrange
    recognizer = BetalkortRecognizer()
    text = "Mitt visakort är 4111 1111 1111 1111, dra pengarna från det."
    
    # Act
    findings = recognizer.recognize(text)
    
    # Assert
    assert len(findings) == 1
    finding = findings[0]
    assert finding.category == Category.BETALKORT
    assert finding.text_span == "4111 1111 1111 1111"
    assert finding.source == "pattern.luhn_betalkort"
    assert finding.confidence == 1.0
    assert text[finding.start : finding.end] == "4111 1111 1111 1111"

def test_betalkort_recognizer_mastercard_continuous():
    recognizer = BetalkortRecognizer()
    text = "Kortnummer: 5105105105105100"
    findings = recognizer.recognize(text)
    assert len(findings) == 1
    assert findings[0].text_span == "5105105105105100"

def test_betalkort_recognizer_amex_with_dashes():
    recognizer = BetalkortRecognizer()
    # 15 digits
    text = "Amex-kort 3782-822463-10005 är spärrat."
    findings = recognizer.recognize(text)
    assert len(findings) == 1
    assert findings[0].text_span == "3782-822463-10005"

def test_betalkort_invalid_luhn_gets_ignored():
    recognizer = BetalkortRecognizer()
    text = "Här är ett låtsaskort 4111 1111 1111 1112 som inte validerar."
    findings = recognizer.recognize(text)
    assert len(findings) == 0

def test_betalkort_multiple_in_text():
    recognizer = BetalkortRecognizer()
    text = "Två kort: 4111 1111 1111 1111 och 5105-1051-0510-5100."
    findings = recognizer.recognize(text)
    assert len(findings) == 2
    assert findings[0].text_span == "4111 1111 1111 1111"
    assert findings[1].text_span == "5105-1051-0510-5100"

def test_betalkort_too_long_or_too_short():
    recognizer = BetalkortRecognizer()
    text = "12 siffror: 123456789012, 17 siffror: 12345678901234567"
    # Even if Luhn would match by coincidence, the digit count is outside 13-16.
    findings = recognizer.recognize(text)
    assert len(findings) == 0
