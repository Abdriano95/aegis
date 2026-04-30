"""Unit tests for GeminiProvider — google.genai SDK fully mocked via sys.modules."""

import json
import logging
import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from gdpr_classifier.layers.llm.provider import LLMProviderError


def _build_sys_modules_patch(response_text: str | None = None, raise_exc: Exception | None = None):
    """Return (patch_dict, mock_client, mock_types) for mocking google.genai.

    Patches sys.modules so that 'import google.genai' and
    'import google.genai.types' succeed inside GeminiProvider methods.
    """
    mock_response = MagicMock()
    mock_response.text = response_text

    mock_client = MagicMock()
    if raise_exc is not None:
        mock_client.models.generate_content.side_effect = raise_exc
    else:
        mock_client.models.generate_content.return_value = mock_response

    mock_genai_module = ModuleType("google.genai")
    mock_genai_module.Client = MagicMock(return_value=mock_client)  # type: ignore[attr-defined]

    mock_types_module = ModuleType("google.genai.types")
    mock_types_module.GenerateContentConfig = MagicMock(return_value=MagicMock())  # type: ignore[attr-defined]

    # Python requires the parent 'google' package to be in sys.modules too
    mock_google = ModuleType("google")
    mock_google.genai = mock_genai_module  # type: ignore[attr-defined]

    patch_dict = {
        "google": mock_google,
        "google.genai": mock_genai_module,
        "google.genai.types": mock_types_module,
    }
    return patch_dict, mock_client, mock_types_module


class TestGeminiProviderInstantiation:
    def test_missing_api_key_raises_at_init(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        # No google-genai needed — error fires before the import attempt
        patch_dict, _, _ = _build_sys_modules_patch()
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.gemini_provider import GeminiProvider

            with pytest.raises(LLMProviderError, match="GEMINI_API_KEY"):
                GeminiProvider(model_name="gemini-1.5-flash")

    def test_missing_sdk_raises_at_init(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        # Simulate google-genai not installed by setting the module to None
        with patch.dict(sys.modules, {"google": None, "google.genai": None, "google.genai.types": None}):
            from gdpr_classifier.layers.llm.gemini_provider import GeminiProvider

            with pytest.raises(LLMProviderError, match="google-genai is not installed"):
                GeminiProvider(model_name="gemini-1.5-flash")

    def test_production_warning_logged(self, monkeypatch, caplog):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        patch_dict, _, _ = _build_sys_modules_patch(response_text="{}")
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.gemini_provider import GeminiProvider

            with caplog.at_level(logging.WARNING):
                GeminiProvider(model_name="gemini-1.5-flash")

        assert any("not sanctioned for production" in r.message for r in caplog.records)


class TestGeminiProviderGenerateJson:
    @pytest.fixture(autouse=True)
    def set_api_key(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    def test_success_returns_dict(self):
        expected = {"label": "halsodata", "confidence": 0.95}
        patch_dict, _, _ = _build_sys_modules_patch(response_text=json.dumps(expected))
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.gemini_provider import GeminiProvider

            provider = GeminiProvider(model_name="gemini-1.5-flash")
            result = provider.generate_json("Classify this.")
        assert result == expected

    def test_invalid_json_raises(self):
        patch_dict, _, _ = _build_sys_modules_patch(response_text="not-json{{")
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.gemini_provider import GeminiProvider

            provider = GeminiProvider(model_name="gemini-1.5-flash")
            with pytest.raises(LLMProviderError, match="not valid JSON"):
                provider.generate_json("prompt")

    def test_empty_response_raises(self):
        patch_dict, _, _ = _build_sys_modules_patch(response_text="")
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.gemini_provider import GeminiProvider

            provider = GeminiProvider(model_name="gemini-1.5-flash")
            with pytest.raises(LLMProviderError, match="empty response"):
                provider.generate_json("prompt")

    def test_none_response_text_raises(self):
        patch_dict, _, _ = _build_sys_modules_patch(response_text=None)
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.gemini_provider import GeminiProvider

            provider = GeminiProvider(model_name="gemini-1.5-flash")
            with pytest.raises(LLMProviderError, match="empty response"):
                provider.generate_json("prompt")

    def test_sdk_exception_raises_llm_provider_error(self):
        patch_dict, _, _ = _build_sys_modules_patch(raise_exc=RuntimeError("quota exceeded"))
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.gemini_provider import GeminiProvider

            provider = GeminiProvider(model_name="gemini-1.5-flash")
            with pytest.raises(LLMProviderError, match="Gemini API call failed"):
                provider.generate_json("prompt")

    def test_temperature_forwarded_to_config(self):
        patch_dict, _, mock_types = _build_sys_modules_patch(response_text=json.dumps({"ok": True}))
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.gemini_provider import GeminiProvider

            provider = GeminiProvider(model_name="gemini-1.5-flash", temperature=0.0)
            provider.generate_json("prompt")

        config_kwargs = mock_types.GenerateContentConfig.call_args.kwargs
        assert config_kwargs.get("temperature") == 0.0

    def test_system_prompt_forwarded(self):
        patch_dict, _, mock_types = _build_sys_modules_patch(response_text=json.dumps({"ok": True}))
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.gemini_provider import GeminiProvider

            provider = GeminiProvider(model_name="gemini-1.5-flash")
            provider.generate_json("prompt", system_prompt="Be precise.")

        config_kwargs = mock_types.GenerateContentConfig.call_args.kwargs
        assert config_kwargs.get("system_instruction") == "Be precise."

    def test_system_prompt_absent_when_not_provided(self):
        patch_dict, _, mock_types = _build_sys_modules_patch(response_text=json.dumps({"ok": True}))
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.gemini_provider import GeminiProvider

            provider = GeminiProvider(model_name="gemini-1.5-flash")
            provider.generate_json("prompt")

        config_kwargs = mock_types.GenerateContentConfig.call_args.kwargs
        assert "system_instruction" not in config_kwargs

    def test_response_mime_type_always_json(self):
        patch_dict, _, mock_types = _build_sys_modules_patch(response_text=json.dumps({"ok": True}))
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.gemini_provider import GeminiProvider

            provider = GeminiProvider(model_name="gemini-1.5-flash")
            provider.generate_json("prompt")

        config_kwargs = mock_types.GenerateContentConfig.call_args.kwargs
        assert config_kwargs.get("response_mime_type") == "application/json"

    def test_non_object_json_raises(self):
        # Gemini returns valid JSON but not a dict (e.g. a list)
        patch_dict, _, _ = _build_sys_modules_patch(response_text=json.dumps([1, 2, 3]))
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.gemini_provider import GeminiProvider

            provider = GeminiProvider(model_name="gemini-1.5-flash")
            with pytest.raises(LLMProviderError, match="expected a dict"):
                provider.generate_json("prompt")
