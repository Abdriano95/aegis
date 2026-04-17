"""Tests for ConfusionMatrix and run_evaluation."""

from __future__ import annotations

from evaluation.confusion_matrix import ConfusionMatrix
from evaluation.dataset.labeled_finding import LabeledFinding
from evaluation.dataset.labeled_text import LabeledText
from evaluation.matcher import MatchResult
from evaluation.report import Report
from evaluation.runner import run_evaluation
from gdpr_classifier.core.category import Category
from gdpr_classifier.core.classification import Classification, SensitivityLevel
from gdpr_classifier.core.finding import Finding


def test_confusion_matrix_accumulation():
    cm = ConfusionMatrix()

    # Create dummy findings
    p1 = Finding(category=Category.PERSONNUMMER, start=0, end=10, text_span="123", confidence=1.0, source="pattern.luhn")
    p2 = Finding(category=Category.EMAIL, start=15, end=20, text_span="a@b.c", confidence=0.9, source="pattern.regex")

    e1 = LabeledFinding(category=Category.PERSONNUMMER, start=0, end=10, text_span="123")
    e2 = LabeledFinding(category=Category.EMAIL, start=50, end=60, text_span="e@f.g")

    # MatchResult 1
    # TP: p1 matches e1
    # FP: p2
    # FN: e2
    mr1 = MatchResult(
        true_positives=[(p1, e1)],
        false_positives=[p2],
        false_negatives=[e2],
    )

    cm.add_match_result(mr1)

    assert cm.get_total_stats() == (1, 1, 1)

    # Category stats
    assert cm.get_category_stats(Category.PERSONNUMMER) == (1, 0, 0)
    assert cm.get_category_stats(Category.EMAIL) == (0, 1, 1)

    # Layer stats
    assert cm.get_layer_stats("pattern") == (1, 1, 0)


class DummyPipeline:
    def classify(self, text: str) -> Classification:
        finding = Finding(
            category=Category.PERSONNUMMER,
            start=0,
            end=10,
            text_span=text[:10],
            confidence=1.0,
            source="pattern.test"
        )
        return Classification(
            findings=[finding],
            sensitivity=SensitivityLevel.LOW,
            active_layers=["pattern"],
            overlapping_findings=[],
        )


def test_run_evaluation():
    pipeline = DummyPipeline()
    # Dummy dataset
    # 1. Expected matches dummy finding
    expected1 = LabeledFinding(category=Category.PERSONNUMMER, start=0, end=10, text_span="1234567890")
    t1 = LabeledText(text="1234567890", expected_findings=[expected1], description="A")

    # 2. Expected is email, dummy produces personnummer (mismatch)
    expected2 = LabeledFinding(category=Category.EMAIL, start=0, end=10, text_span="a@b.com   ")
    t2 = LabeledText(text="a@b.com   ", expected_findings=[expected2], description="B")

    dataset = [t1, t2]

    report = run_evaluation(pipeline, dataset)

    assert isinstance(report, Report)

    # total_tp = 1 (t1)
    # total_fp = 1 (t2 dummy finding)
    # total_fn = 1 (t2 expected email)
    assert report.total.tp == 1
    assert report.total.fp == 1
    assert report.total.fn == 1

    assert report.total.precision == 0.5  # 1 / 2
    assert report.total.recall == 0.5     # 1 / 2
    assert report.total.f1 == 0.5         # 2 * 0.25 / 1.0

    assert "pattern" in report.per_layer
    assert report.per_layer["pattern"].tp == 1
    assert report.per_layer["pattern"].fp == 1
    assert report.per_layer["pattern"].fn == 0

    assert Category.PERSONNUMMER in report.per_category
    assert report.per_category[Category.PERSONNUMMER].tp == 1
    assert report.per_category[Category.PERSONNUMMER].fp == 1
    assert report.per_category[Category.PERSONNUMMER].fn == 0

    assert Category.EMAIL in report.per_category
    assert report.per_category[Category.EMAIL].tp == 0
    assert report.per_category[Category.EMAIL].fp == 0
    assert report.per_category[Category.EMAIL].fn == 1
