"""Unit tests for StubCombinationLayer."""

from __future__ import annotations

from gdpr_classifier.core.category import Category
from gdpr_classifier.core.layer import Layer
from tests.fixtures.stub_combination_layer import StubCombinationLayer


def test_layer_protocol_compliance():
    """StubCombinationLayer must satisfy the runtime-checkable Layer protocol."""
    assert isinstance(StubCombinationLayer(), Layer) is True


def test_detect_empty_string_returns_empty():
    assert StubCombinationLayer().detect("") == []


def test_detect_no_wordlist_words_returns_empty():
    text = "Automatiserad processen genomfördes enligt schema utan personuppgifter."
    assert StubCombinationLayer().detect(text) == []


def test_detect_two_signals_returns_three_findings():
    """Two wordlist matches produce 2 signal findings + 1 aggregate = 3 findings total."""
    text = "En lärare i Stockholm diskuterade frågan."
    findings = StubCombinationLayer().detect(text)

    assert len(findings) == 3

    signals = [f for f in findings if f.source != "context.kombination"]
    aggregates = [f for f in findings if f.source == "context.kombination"]

    assert len(signals) == 2
    assert len(aggregates) == 1

    agg = aggregates[0]
    assert agg.start == min(f.start for f in signals)
    assert agg.end == max(f.end for f in signals)
    assert agg.text_span == text[agg.start:agg.end]


def test_detect_one_signal_returns_empty():
    """A single wordlist match is insufficient - no aggregate can be built."""
    text = "Vi behöver fler lärare i skolan."
    assert StubCombinationLayer().detect(text) == []


def test_text_span_invariant():
    """For every returned finding: text[f.start:f.end] == f.text_span."""
    text = "Sjuksköterskan arbetar vid Sahlgrenska Universitetssjukhuset i Göteborg."
    findings = StubCombinationLayer().detect(text)
    assert len(findings) > 0, "Expected findings for text with 3 wordlist matches"
    for f in findings:
        assert text[f.start:f.end] == f.text_span, (
            f"Span mismatch for {f.source!r}: "
            f"text[{f.start}:{f.end}]={text[f.start:f.end]!r}, "
            f"text_span={f.text_span!r}"
        )


def test_aggregate_confidence_gte_085():
    """Aggregate findings must have confidence >= 0.85 to trigger the bypass."""
    text = "Sjuksköterskan arbetar i Stockholm."
    findings = StubCombinationLayer().detect(text)
    aggregates = [f for f in findings if f.source == "context.kombination"]
    assert len(aggregates) == 1
    assert aggregates[0].confidence >= 0.85


def test_aggregate_category_is_kombination():
    """Aggregate finding category matches actual CombinationLayer output."""
    text = "lärare i Göteborg diskuterade utmaningarna."
    findings = StubCombinationLayer().detect(text)
    aggregates = [f for f in findings if f.source == "context.kombination"]
    assert len(aggregates) == 1
    assert aggregates[0].category == Category.KOMBINATION
