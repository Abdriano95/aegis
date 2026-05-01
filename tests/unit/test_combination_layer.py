"""Unit tests for CombinationLayer."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

import pytest

from gdpr_classifier.core.category import Category
from gdpr_classifier.core.finding import Finding
from gdpr_classifier.core.layer import Layer
from gdpr_classifier.layers.combination.combination_layer import (
    CombinationLayer,
    CombinationLayerError,
)
from gdpr_classifier.layers.llm.provider import LLMProvider, LLMProviderError


class TestCombinationLayer(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_provider = MagicMock(spec=LLMProvider)
        self.layer = CombinationLayer(provider=self.mock_provider, prompt_version="v2")

    def test_layer_protocol(self) -> None:
        """Test that CombinationLayer implements the Layer protocol."""
        # Using isinstance with Layer Protocol
        self.assertIsInstance(self.layer, Layer)
        self.assertEqual(self.layer.name, "combination")

    def test_detect_empty_response(self) -> None:
        """Test detect with an empty response indicating no identifiable combination."""
        self.mock_provider.generate_json.return_value = {
            "individual_signals": [],
            "combination": {
                "is_identifiable": False,
                "text_span": "",
                "confidence": 0.0,
                "reasoning": "",
            },
        }
        findings = self.layer.detect("Många lärare jobbar här.")
        self.assertEqual(findings, [])

    def test_detect_valid_exact_match(self) -> None:
        """Test detect with valid exact matches for all signals and combination."""
        text = "Min chef på lagret i Eskilstuna trakasserar mig."
        self.mock_provider.generate_json.return_value = {
            "individual_signals": [
                {"signal": "yrke", "text_span": "chef", "confidence": 0.9},
                {"signal": "plats", "text_span": "Eskilstuna", "confidence": 0.95},
                {"signal": "organisation", "text_span": "lagret", "confidence": 0.8},
            ],
            "combination": {
                "is_identifiable": True,
                "text_span": "chef på lagret i Eskilstuna",
                "confidence": 0.85,
                "reasoning": "CoT",
            },
        }
        findings = self.layer.detect(text)

        self.assertEqual(len(findings), 4)
        
        # Check individual signals
        yrke_finding = next(f for f in findings if f.category == Category.YRKE)
        self.assertEqual(yrke_finding.text_span, "chef")
        self.assertEqual(yrke_finding.source, "context.yrke")
        
        plats_finding = next(f for f in findings if f.category == Category.PLATS)
        self.assertEqual(plats_finding.text_span, "Eskilstuna")
        
        org_finding = next(f for f in findings if f.category == Category.ORGANISATION)
        self.assertEqual(org_finding.text_span, "lagret")

        # Check combination finding
        comb_finding = next(f for f in findings if f.category == Category.KOMBINATION)
        self.assertEqual(comb_finding.text_span, "chef på lagret i Eskilstuna")
        self.assertEqual(comb_finding.source, "context.kombination")
        self.assertEqual(comb_finding.metadata["validation_path"], "exact")

    def test_differentiated_validation_hallucinated_individual(self) -> None:
        """Test differentiated validation: hallucinated individual signal is dropped silently."""
        text = "Min chef i Eskilstuna."
        self.mock_provider.generate_json.return_value = {
            "individual_signals": [
                {"signal": "yrke", "text_span": "chef", "confidence": 0.9},
                {"signal": "plats", "text_span": "Stockholm", "confidence": 0.9},  # Hallucinated
            ],
            "combination": {
                "is_identifiable": False,
            },
        }
        findings = self.layer.detect(text)
        
        # Only "chef" should be kept
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].text_span, "chef")

    def test_differentiated_validation_reconstructed_combination(self) -> None:
        """Test differentiated validation: hallucinated combination span reconstructed from min/max."""
        text = "Min chef på lagret i Eskilstuna trakasserar mig."
        self.mock_provider.generate_json.return_value = {
            "individual_signals": [
                {"signal": "yrke", "text_span": "chef", "confidence": 0.9},
                {"signal": "plats", "text_span": "Eskilstuna", "confidence": 0.9},
            ],
            "combination": {
                "is_identifiable": True,
                "text_span": "något helt påhittat som inte finns i texten",
                "confidence": 0.8,
                "reasoning": "CoT",
            },
        }
        findings = self.layer.detect(text)
        
        self.assertEqual(len(findings), 3)  # 2 individual + 1 reconstructed comb
        
        comb_finding = next(f for f in findings if f.category == Category.KOMBINATION)
        self.assertEqual(comb_finding.metadata["validation_path"], "reconstructed")
        # Min span is "chef", max is "Eskilstuna". 
        # text.find("chef") = 4, text.find("Eskilstuna") = 21, len("Eskilstuna") = 10 -> 4 to 31
        self.assertEqual(comb_finding.text_span, "chef på lagret i Eskilstuna")

    def test_differentiated_validation_dropped_combination(self) -> None:
        """Test differentiated validation: hallucinated combination span with <2 valid signals is dropped."""
        text = "Min chef är arg."
        self.mock_provider.generate_json.return_value = {
            "individual_signals": [
                {"signal": "yrke", "text_span": "chef", "confidence": 0.9},
            ],
            "combination": {
                "is_identifiable": True,
                "text_span": "hallucinerad kombination",
                "confidence": 0.8,
                "reasoning": "CoT",
            },
        }
        findings = self.layer.detect(text)
        
        # Should only contain the 1 individual finding, combination is dropped
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, Category.YRKE)

    def test_differentiated_validation_normalized_whitespace(self) -> None:
        """Test differentiated validation: combination span with whitespace variance."""
        text = "Min   chef på   lagret"
        self.mock_provider.generate_json.return_value = {
            "individual_signals": [],
            "combination": {
                "is_identifiable": True,
                "text_span": "chef på lagret",  # Different whitespace
                "confidence": 0.8,
                "reasoning": "CoT",
            },
        }
        findings = self.layer.detect(text)
        
        self.assertEqual(len(findings), 1)
        comb_finding = findings[0]
        self.assertEqual(comb_finding.category, Category.KOMBINATION)
        self.assertEqual(comb_finding.metadata["validation_path"], "normalized")
        self.assertEqual(comb_finding.text_span, "chef på   lagret")

    def test_schema_error_missing_key(self) -> None:
        """Test schema error handling for missing keys."""
        self.mock_provider.generate_json.return_value = {
            "individual_signals": []
            # missing "combination"
        }
        with self.assertRaises(CombinationLayerError):
            self.layer.detect("text")

    def test_schema_error_invalid_signal(self) -> None:
        """Test schema error handling for invalid individual signal."""
        self.mock_provider.generate_json.return_value = {
            "individual_signals": [
                {"signal": "invalid_signal", "text_span": "text", "confidence": 0.5}
            ],
            "combination": {"is_identifiable": False},
        }
        with self.assertRaises(CombinationLayerError):
            self.layer.detect("text")

    def test_provider_error_propagates(self) -> None:
        """Test that LLMProviderError propagates unchanged."""
        self.mock_provider.generate_json.side_effect = LLMProviderError("LLM failed")
        with self.assertRaises(LLMProviderError):
            self.layer.detect("text")
