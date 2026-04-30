"""Unit tests for OllamaProvider — all network calls mocked."""

import json
from unittest.mock import MagicMock, patch

import pytest

from gdpr_classifier.layers.llm.ollama_provider import OllamaProvider
from gdpr_classifier.layers.llm.provider import LLMProviderError


def _mock_response(json_body: dict, status_code: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_body
    mock.text = json.dumps(json_body)
    mock.raise_for_status = MagicMock()
    if status_code >= 400:
        import requests

        mock.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock
        )
    return mock


class TestOllamaProviderGenerateJson:
    def test_success_returns_dict(self):
        payload = {"response": json.dumps({"label": "halsodata", "confidence": 0.9})}
        with patch("requests.post", return_value=_mock_response(payload)) as mock_post:
            provider = OllamaProvider(model_name="llama3")
            result = provider.generate_json("Classify this text.")

        assert result == {"label": "halsodata", "confidence": 0.9}
        mock_post.assert_called_once()

    def test_network_error_raises_llm_provider_error(self):
        import requests as req

        with patch(
            "requests.post", side_effect=req.exceptions.ConnectionError("refused")
        ):
            provider = OllamaProvider(model_name="llama3")
            with pytest.raises(LLMProviderError, match="Ollama request failed"):
                provider.generate_json("prompt")

    def test_http_error_raises_llm_provider_error(self):
        import requests as req

        mock = _mock_response({}, status_code=500)
        mock.raise_for_status.side_effect = req.exceptions.HTTPError(response=mock)
        with patch("requests.post", return_value=mock):
            provider = OllamaProvider(model_name="llama3")
            with pytest.raises(LLMProviderError, match="Ollama request failed"):
                provider.generate_json("prompt")

    def test_invalid_json_in_response_field_raises(self):
        payload = {"response": "not-valid-json{{{"}
        with patch("requests.post", return_value=_mock_response(payload)):
            provider = OllamaProvider(model_name="llama3")
            with pytest.raises(LLMProviderError, match="not valid JSON"):
                provider.generate_json("prompt")

    def test_empty_response_field_raises(self):
        payload = {"response": ""}
        with patch("requests.post", return_value=_mock_response(payload)):
            provider = OllamaProvider(model_name="llama3")
            with pytest.raises(LLMProviderError, match="empty"):
                provider.generate_json("prompt")

    def test_missing_response_field_raises(self):
        payload = {"done": True}
        with patch("requests.post", return_value=_mock_response(payload)):
            provider = OllamaProvider(model_name="llama3")
            with pytest.raises(LLMProviderError, match="empty"):
                provider.generate_json("prompt")

    def test_temperature_sent_in_options(self):
        payload = {"response": json.dumps({"ok": True})}
        with patch("requests.post", return_value=_mock_response(payload)) as mock_post:
            provider = OllamaProvider(model_name="llama3", temperature=0.0)
            provider.generate_json("prompt")

        call_kwargs = mock_post.call_args
        sent_json = call_kwargs.kwargs.get("json") or call_kwargs.args[1]
        assert sent_json["options"]["temperature"] == 0.0

    def test_custom_temperature_forwarded(self):
        payload = {"response": json.dumps({"ok": True})}
        with patch("requests.post", return_value=_mock_response(payload)) as mock_post:
            provider = OllamaProvider(model_name="llama3", temperature=0.7)
            provider.generate_json("prompt")

        sent_json = mock_post.call_args.kwargs.get("json") or mock_post.call_args.args[1]
        assert sent_json["options"]["temperature"] == 0.7

    def test_system_prompt_included_when_provided(self):
        payload = {"response": json.dumps({"ok": True})}
        with patch("requests.post", return_value=_mock_response(payload)) as mock_post:
            provider = OllamaProvider(model_name="llama3")
            provider.generate_json("prompt", system_prompt="You are an expert.")

        sent_json = mock_post.call_args.kwargs.get("json") or mock_post.call_args.args[1]
        assert sent_json.get("system") == "You are an expert."

    def test_system_prompt_absent_when_not_provided(self):
        payload = {"response": json.dumps({"ok": True})}
        with patch("requests.post", return_value=_mock_response(payload)) as mock_post:
            provider = OllamaProvider(model_name="llama3")
            provider.generate_json("prompt")

        sent_json = mock_post.call_args.kwargs.get("json") or mock_post.call_args.args[1]
        assert "system" not in sent_json

    def test_format_json_always_sent(self):
        payload = {"response": json.dumps({"ok": True})}
        with patch("requests.post", return_value=_mock_response(payload)) as mock_post:
            provider = OllamaProvider(model_name="llama3")
            provider.generate_json("prompt")

        sent_json = mock_post.call_args.kwargs.get("json") or mock_post.call_args.args[1]
        assert sent_json.get("format") == "json"
        assert sent_json.get("stream") is False

    def test_custom_endpoint_used(self):
        payload = {"response": json.dumps({"ok": True})}
        with patch("requests.post", return_value=_mock_response(payload)) as mock_post:
            provider = OllamaProvider(
                model_name="llama3", endpoint="http://myhost:11434"
            )
            provider.generate_json("prompt")

        url = mock_post.call_args.args[0]
        assert url == "http://myhost:11434/api/generate"

    def test_http_body_json_parse_failure_raises(self):
        # response.json() itself raises ValueError (Ollama returns a non-JSON HTTP body)
        mock = MagicMock()
        mock.status_code = 200
        mock.text = "not json at all"
        mock.raise_for_status = MagicMock()
        mock.json.side_effect = ValueError("no JSON")
        with patch("requests.post", return_value=mock):
            provider = OllamaProvider(model_name="llama3")
            with pytest.raises(LLMProviderError, match="non-JSON HTTP body"):
                provider.generate_json("prompt")

    def test_non_dict_json_response_raises(self):
        # Ollama returns valid JSON but not a dict (e.g. a list)
        payload = {"response": json.dumps([1, 2, 3])}
        with patch("requests.post", return_value=_mock_response(payload)):
            provider = OllamaProvider(model_name="llama3")
            with pytest.raises(LLMProviderError, match="expected a dict"):
                provider.generate_json("prompt")
