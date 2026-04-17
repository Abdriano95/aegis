"""Unit tests for evaluation metrics."""

from __future__ import annotations

import pytest

from evaluation.metrics import f1, precision, recall


def test_recall_normal():
    """Test standard recall calculation."""
    # TP=8, FN=2 => 8/(8+2) = 0.8
    assert recall(tp=8, fn=2) == 0.8


def test_recall_zero_division():
    """Test recall handling of division by zero."""
    assert recall(tp=0, fn=0) == 0.0


def test_precision_normal():
    """Test standard precision calculation."""
    # TP=8, FP=2 => 8/(8+2) = 0.8
    assert precision(tp=8, fp=2) == 0.8


def test_precision_zero_division():
    """Test precision handling of division by zero."""
    assert precision(tp=0, fp=0) == 0.0


def test_f1_normal():
    """Test standard F1 calculation."""
    # TP=4, FP=1, FN=1 => P=0.8, R=0.8 => F1=0.8
    assert f1(tp=4, fp=1, fn=1) == pytest.approx(0.8)
    
    # TP=5, FP=5, FN=0 => P=0.5, R=1.0 => F1 = 2*0.5*1.0 / 1.5 = 2/3
    assert f1(tp=5, fp=5, fn=0) == pytest.approx(0.6666666666666666)


def test_f1_zero_division():
    """Test F1 handling of division by zero."""
    # TP=0, FP=0, FN=0 => P=0, R=0 => Denominator=0
    assert f1(tp=0, fp=0, fn=0) == 0.0

    # TP=0, FP=10, FN=5 => P=0, R=0 => Denominator=0
    assert f1(tp=0, fp=10, fn=5) == 0.0
