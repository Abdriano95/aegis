"""Unit tests for matcher."""

from __future__ import annotations

from gdpr_classifier.core.category import Category
from gdpr_classifier.core.finding import Finding
from evaluation.dataset.labeled_finding import LabeledFinding
from evaluation.matcher import match


def test_match_exact():
    """Test standard exact match on category and position."""
    e1 = LabeledFinding(category=Category.PERSONNUMMER, start=10, end=20, text_span="850101-1234")
    p1 = Finding(category=Category.PERSONNUMMER, start=10, end=20, text_span="850101-1234", confidence=1.0, source="test")
    
    result = match([p1], [e1])
    
    assert len(result.true_positives) == 1
    assert result.true_positives[0] == (p1, e1)
    assert len(result.false_positives) == 0
    assert len(result.false_negatives) == 0


def test_match_partial_overlap():
    """Test that overlapping spans match even if start/end are not identical."""
    e1 = LabeledFinding(category=Category.EMAIL, start=10, end=30, text_span="anna.svensson@mail.se")
    p1 = Finding(category=Category.EMAIL, start=12, end=28, text_span="na.svensson@mail", confidence=0.9, source="test")
    
    result = match([p1], [e1])
    
    assert len(result.true_positives) == 1
    assert len(result.false_positives) == 0
    assert len(result.false_negatives) == 0


def test_no_overlap():
    """Test no overlap resulting in 1 FP, 1 FN."""
    e1 = LabeledFinding(category=Category.TELEFONNUMMER, start=5, end=15, text_span="070-1234567")
    p1 = Finding(category=Category.TELEFONNUMMER, start=20, end=30, text_span="070-7654321", confidence=0.9, source="test")
    
    result = match([p1], [e1])
    
    assert len(result.true_positives) == 0
    assert len(result.false_positives) == 1
    assert result.false_positives[0] == p1
    assert len(result.false_negatives) == 1
    assert result.false_negatives[0] == e1


def test_category_mismatch():
    """Test identical spans with different categories fail to match."""
    e1 = LabeledFinding(category=Category.EMAIL, start=10, end=20, text_span="anna@t.se")
    p1 = Finding(category=Category.NAMN, start=10, end=20, text_span="anna@t.se", confidence=0.9, source="test")
    
    result = match([p1], [e1])
    
    assert len(result.true_positives) == 0
    assert len(result.false_positives) == 1
    assert len(result.false_negatives) == 1


def test_duplicate_coverage_highest_confidence_wins():
    """Test that two predictions overlapping the same target resolves to highest confidence."""
    e1 = LabeledFinding(category=Category.IBAN, start=10, end=30, text_span="SE1234567890")
    
    # Both predictions have same category and overlap
    p_low = Finding(category=Category.IBAN, start=8, end=25, text_span="12345", confidence=0.5, source="low")
    p_high = Finding(category=Category.IBAN, start=12, end=32, text_span="67890", confidence=0.9, source="high")
    
    result = match([p_low, p_high], [e1])
    
    # Highest confidence wins the claim
    assert len(result.true_positives) == 1
    assert result.true_positives[0][0] == p_high
    assert result.true_positives[0][1] == e1
    
    # Lower confidence falls through
    assert len(result.false_positives) == 1
    assert result.false_positives[0] == p_low
    assert len(result.false_negatives) == 0


def test_multiple_expecteds_handled_correctly():
    """Test multiple predictions and expected findings resolving correctly."""
    e1 = LabeledFinding(category=Category.PERSONNUMMER, start=0, end=5, text_span="e1")
    e2 = LabeledFinding(category=Category.PERSONNUMMER, start=10, end=15, text_span="e2")
    
    p1 = Finding(category=Category.PERSONNUMMER, start=0, end=5, text_span="p1", confidence=1.0, source="")
    p2 = Finding(category=Category.PERSONNUMMER, start=10, end=15, text_span="p2", confidence=0.8, source="")
    
    result = match([p1, p2], [e1, e2])
    
    assert len(result.true_positives) == 2
    assert len(result.false_positives) == 0
    assert len(result.false_negatives) == 0
