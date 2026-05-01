"""Unit tests for Article9Layer."""

import pytest
from unittest.mock import MagicMock

from gdpr_classifier.core.category import Category
from gdpr_classifier.core.finding import Finding
from gdpr_classifier.core.layer import Layer
from gdpr_classifier.layers.article9 import Article9Layer, Article9LayerError
from gdpr_classifier.layers.llm.provider import LLMProvider, LLMProviderError


def test_article9_layer_constructor_requires_provider():
    """Test that the constructor requires an LLMProvider."""
    with pytest.raises(TypeError):
        Article9Layer()  # type: ignore


def test_article9_layer_properties():
    """Test basic layer properties."""
    mock_provider = MagicMock(spec=LLMProvider)
    layer = Article9Layer(provider=mock_provider)
    
    assert layer.name == "article9"
    assert isinstance(layer, Layer)


def test_article9_layer_empty_findings():
    """Test detect returning an empty findings list."""
    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.generate_json.return_value = {"findings": []}
    
    layer = Article9Layer(provider=mock_provider, prompt_version="v2")
    
    # We patch load_prompt so we don't have to depend on the actual filesystem prompt parsing in this test
    # But since load_prompt reads from the disk, and we are running tests with actual filesystem,
    # it's fine if it reads the real yaml.
    
    results = layer.detect("Inga personuppgifter här.")
    
    assert results == []
    mock_provider.generate_json.assert_called_once()


def test_article9_layer_valid_finding():
    """Test detect with a valid exact-match finding."""
    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.generate_json.return_value = {
        "findings": [
            {
                "category": "halsodata",
                "text_span": "diabetes typ 2",
                "confidence": 0.95
            }
        ]
    }
    
    layer = Article9Layer(provider=mock_provider, prompt_version="v2")
    text = "Patienten har diabetes typ 2 sedan flera år."
    results = layer.detect(text)
    
    assert len(results) == 1
    finding = results[0]
    assert finding.category == Category.HALSODATA
    assert finding.source == "article9.halsodata"
    assert finding.text_span == "diabetes typ 2"
    assert finding.start == 14
    assert finding.end == 28
    assert finding.confidence == 0.95


def test_article9_layer_hallucinated_finding():
    """Test that a hallucinated text_span is dropped."""
    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.generate_json.return_value = {
        "findings": [
            {
                "category": "halsodata",
                "text_span": "cancer", # Not in text
                "confidence": 0.99
            }
        ]
    }
    
    layer = Article9Layer(provider=mock_provider, prompt_version="v2")
    text = "Patienten är frisk."
    results = layer.detect(text)
    
    assert results == []


def test_article9_layer_mixed_findings():
    """Test that only valid findings are kept."""
    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.generate_json.return_value = {
        "findings": [
            {
                "category": "halsodata",
                "text_span": "bruten arm",
                "confidence": 0.90
            },
            {
                "category": "etniskt_ursprung",
                "text_span": "hallucination",
                "confidence": 0.99
            }
        ]
    }
    
    layer = Article9Layer(provider=mock_provider, prompt_version="v2")
    text = "Patienten inkom med en bruten arm."
    results = layer.detect(text)
    
    assert len(results) == 1
    assert results[0].text_span == "bruten arm"
    assert results[0].category == Category.HALSODATA


def test_article9_layer_case_insensitive_fallback():
    """Test case-insensitive fallback."""
    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.generate_json.return_value = {
        "findings": [
            {
                "category": "halsodata",
                "text_span": "diabetes", # Lowercase in prompt
                "confidence": 0.90
            }
        ]
    }
    
    layer = Article9Layer(provider=mock_provider, prompt_version="v2")
    text = "Patienten har Diabetes."
    results = layer.detect(text)
    
    assert len(results) == 1
    assert results[0].text_span == "Diabetes" # Should match original casing
    assert results[0].start == 14
    assert results[0].end == 22


def test_article9_layer_schema_error_missing_findings():
    """Test error on missing findings field."""
    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.generate_json.return_value = {"bad_key": []}
    
    layer = Article9Layer(provider=mock_provider, prompt_version="v2")
    with pytest.raises(Article9LayerError, match="Missing 'findings' field"):
        layer.detect("text")


def test_article9_layer_schema_error_unknown_category():
    """Test error on unknown category."""
    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.generate_json.return_value = {
        "findings": [
            {
                "category": "not_a_valid_category",
                "text_span": "text",
                "confidence": 0.9
            }
        ]
    }
    
    layer = Article9Layer(provider=mock_provider, prompt_version="v2")
    with pytest.raises(Article9LayerError, match="Unknown category: not_a_valid_category"):
        layer.detect("some text")


def test_article9_layer_provider_error_propagates():
    """Test that LLMProviderError is propagated."""
    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.generate_json.side_effect = LLMProviderError("Network failure")
    
    layer = Article9Layer(provider=mock_provider, prompt_version="v2")
    with pytest.raises(LLMProviderError):
        layer.detect("text")
