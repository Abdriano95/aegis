"""Unit tests for AnthropicProvider — anthropic SDK fully mocked via sys.modules.

These tests run green without a real ANTHROPIC_API_KEY and without the
anthropic package installed.
"""

import json
import logging
import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from gdpr_classifier.layers.llm.provider import LLMProviderError

_SLEEP_PATH = "gdpr_classifier.layers.llm.anthropic_provider.time.sleep"


class _FakeResponse:
    """Minimal stand-in for the SDK's httpx response (carries headers)."""

    def __init__(self, headers: dict):
        self.headers = headers


class _FakeRateLimitError(Exception):
    """A real BaseException (caught by `except Exception`) shaped like the
    anthropic SDK's APIStatusError: it exposes .status_code and
    .response.headers, so duck-typed 429 detection works."""

    status_code = 429

    def __init__(self, retry_after=None):
        super().__init__("rate limited")
        headers = {} if retry_after is None else {"retry-after": retry_after}
        self.response = _FakeResponse(headers)


def _build_sys_modules_patch(
    response_text: str | None = None,
    raise_exc: Exception | None = None,
    side_effects: list | None = None,
):
    """Return (patch_dict, mock_client, mock_anthropic_module).

    Patches sys.modules so that `import anthropic` inside AnthropicProvider
    succeeds and returns a mocked client.
    """
    mock_block = MagicMock()
    mock_block.text = response_text
    mock_response = MagicMock()
    mock_response.content = [mock_block]

    mock_client = MagicMock()
    if side_effects is not None:
        mock_client.messages.create.side_effect = side_effects
    elif raise_exc is not None:
        mock_client.messages.create.side_effect = raise_exc
    else:
        mock_client.messages.create.return_value = mock_response

    mock_anthropic_module = ModuleType("anthropic")
    mock_anthropic_module.Anthropic = MagicMock(return_value=mock_client)  # type: ignore[attr-defined]

    patch_dict = {"anthropic": mock_anthropic_module}
    return patch_dict, mock_client, mock_anthropic_module


class TestAnthropicProviderInstantiation:
    def test_missing_api_key_raises_at_init(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        # No anthropic SDK needed — error fires before the import attempt.
        from gdpr_classifier.layers.llm.anthropic_provider import AnthropicProvider

        with pytest.raises(LLMProviderError, match="ANTHROPIC_API_KEY"):
            AnthropicProvider()

    def test_missing_sdk_raises_at_init(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        # Simulate anthropic not installed by setting the module to None.
        with patch.dict(sys.modules, {"anthropic": None}):
            from gdpr_classifier.layers.llm.anthropic_provider import (
                AnthropicProvider,
            )

            with pytest.raises(LLMProviderError, match="anthropic is not installed"):
                AnthropicProvider()

    def test_production_warning_logged(self, monkeypatch, caplog):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        patch_dict, _, _ = _build_sys_modules_patch(response_text="{}")
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.anthropic_provider import (
                AnthropicProvider,
            )

            with caplog.at_level(logging.WARNING):
                AnthropicProvider()

        assert any(
            "not sanctioned for production" in r.message for r in caplog.records
        )

    def test_client_constructed_with_retries_disabled(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        patch_dict, _, mock_module = _build_sys_modules_patch(response_text="{}")
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.anthropic_provider import (
                AnthropicProvider,
            )

            AnthropicProvider()

        mock_module.Anthropic.assert_called_once_with(
            api_key="test-key", max_retries=0
        )


class TestAnthropicProviderGenerateJson:
    @pytest.fixture(autouse=True)
    def set_api_key(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    def test_success_returns_dict(self):
        expected = {"label": "halsodata", "confidence": 0.95}
        patch_dict, _, _ = _build_sys_modules_patch(
            response_text=json.dumps(expected)
        )
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.anthropic_provider import (
                AnthropicProvider,
            )

            provider = AnthropicProvider()
            result = provider.generate_json("Classify this.")
        assert result == expected

    def test_invalid_json_raises(self):
        patch_dict, _, _ = _build_sys_modules_patch(response_text="not-json{{")
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.anthropic_provider import (
                AnthropicProvider,
            )

            provider = AnthropicProvider()
            with pytest.raises(LLMProviderError, match="not valid JSON"):
                provider.generate_json("prompt")

    def test_empty_response_raises(self):
        patch_dict, _, _ = _build_sys_modules_patch(response_text="")
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.anthropic_provider import (
                AnthropicProvider,
            )

            provider = AnthropicProvider()
            with pytest.raises(LLMProviderError, match="empty response"):
                provider.generate_json("prompt")

    def test_non_429_sdk_exception_raises_llm_provider_error(self):
        patch_dict, _, _ = _build_sys_modules_patch(
            raise_exc=RuntimeError("boom")
        )
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.anthropic_provider import (
                AnthropicProvider,
            )

            provider = AnthropicProvider()
            with pytest.raises(LLMProviderError, match="Anthropic API call failed"):
                provider.generate_json("prompt")

    def test_non_object_json_raises(self):
        patch_dict, _, _ = _build_sys_modules_patch(
            response_text=json.dumps([1, 2, 3])
        )
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.anthropic_provider import (
                AnthropicProvider,
            )

            provider = AnthropicProvider()
            with pytest.raises(LLMProviderError, match="expected a dict"):
                provider.generate_json("prompt")

    def test_request_params_forwarded(self):
        patch_dict, mock_client, _ = _build_sys_modules_patch(
            response_text=json.dumps({"ok": True})
        )
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.anthropic_provider import (
                AnthropicProvider,
            )

            provider = AnthropicProvider()
            provider.generate_json("the-prompt")

        kwargs = mock_client.messages.create.call_args.kwargs
        assert kwargs["model"] == "claude-opus-4-7"
        # temperature is omitted by default (Opus 4.7 rejects an explicit one).
        assert "temperature" not in kwargs
        assert kwargs["max_tokens"] == 4096
        assert kwargs["messages"] == [{"role": "user", "content": "the-prompt"}]

    def test_explicit_temperature_forwarded_when_set(self):
        patch_dict, mock_client, _ = _build_sys_modules_patch(
            response_text=json.dumps({"ok": True})
        )
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.anthropic_provider import (
                AnthropicProvider,
            )

            provider = AnthropicProvider(temperature=0.3)
            provider.generate_json("prompt")

        kwargs = mock_client.messages.create.call_args.kwargs
        assert kwargs["temperature"] == 0.3

    def test_system_prompt_forwarded(self):
        patch_dict, mock_client, _ = _build_sys_modules_patch(
            response_text=json.dumps({"ok": True})
        )
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.anthropic_provider import (
                AnthropicProvider,
            )

            provider = AnthropicProvider()
            provider.generate_json("prompt", system_prompt="Be precise.")

        kwargs = mock_client.messages.create.call_args.kwargs
        assert kwargs.get("system") == "Be precise."

    def test_system_prompt_absent_when_not_provided(self):
        patch_dict, mock_client, _ = _build_sys_modules_patch(
            response_text=json.dumps({"ok": True})
        )
        with patch.dict(sys.modules, patch_dict):
            from gdpr_classifier.layers.llm.anthropic_provider import (
                AnthropicProvider,
            )

            provider = AnthropicProvider()
            provider.generate_json("prompt")

        kwargs = mock_client.messages.create.call_args.kwargs
        assert "system" not in kwargs

    def test_429_then_success_retries(self):
        good = MagicMock()
        good.content = [MagicMock(text=json.dumps({"ok": True}))]
        patch_dict, mock_client, _ = _build_sys_modules_patch(
            side_effects=[_FakeRateLimitError(retry_after="0"), good]
        )
        with patch.dict(sys.modules, patch_dict), patch(_SLEEP_PATH) as mock_sleep:
            from gdpr_classifier.layers.llm.anthropic_provider import (
                AnthropicProvider,
            )

            provider = AnthropicProvider()
            result = provider.generate_json("prompt")

        assert result == {"ok": True}
        assert mock_client.messages.create.call_count == 2
        mock_sleep.assert_called_once_with(0.0)

    def test_429_exhausts_retries_raises(self):
        patch_dict, mock_client, _ = _build_sys_modules_patch(
            side_effects=[
                _FakeRateLimitError(),
                _FakeRateLimitError(),
                _FakeRateLimitError(),
            ]
        )
        with patch.dict(sys.modules, patch_dict), patch(_SLEEP_PATH):
            from gdpr_classifier.layers.llm.anthropic_provider import (
                AnthropicProvider,
            )

            provider = AnthropicProvider()
            with pytest.raises(
                LLMProviderError, match="after 3 attempts .*rate limited"
            ):
                provider.generate_json("prompt")

        assert mock_client.messages.create.call_count == 3

    def test_429_exponential_backoff_when_no_retry_after(self):
        good = MagicMock()
        good.content = [MagicMock(text=json.dumps({"ok": True}))]
        patch_dict, _, _ = _build_sys_modules_patch(
            side_effects=[
                _FakeRateLimitError(),  # no retry-after header
                _FakeRateLimitError(),  # no retry-after header
                good,
            ]
        )
        with patch.dict(sys.modules, patch_dict), patch(_SLEEP_PATH) as mock_sleep:
            from gdpr_classifier.layers.llm.anthropic_provider import (
                AnthropicProvider,
            )

            provider = AnthropicProvider()
            result = provider.generate_json("prompt")

        assert result == {"ok": True}
        # 2 ** 0 = 1.0 on first retry, 2 ** 1 = 2.0 on second.
        assert [c.args[0] for c in mock_sleep.call_args_list] == [1.0, 2.0]
