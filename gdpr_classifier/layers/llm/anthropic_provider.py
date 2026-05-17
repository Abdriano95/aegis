"""AnthropicProvider: LLMProvider implementation for the Anthropic Claude API.

WARNING — NOT FOR PRODUCTION USE (Beslut 17, Loggbok iteration 2):
Sending personal data to a third-party cloud service constitutes a transfer
under GDPR Chapter V. This provider is sanctioned only for development and
testing purposes (e.g. the Issue #107 cloud-model probe) where no real
personal data is processed.

SDK: anthropic (the official Anthropic Python SDK). Unlike Gemini there is no
response_mime_type; structured JSON is requested by the consuming layer's
user prompt (its output_format section already mandates raw JSON).
"""

import json
import logging
import os
import time

from gdpr_classifier.layers.llm.provider import LLMProviderError

logger = logging.getLogger(__name__)

_PRODUCTION_WARNING = (
    "AnthropicProvider is not sanctioned for production use (Beslut 17). "
    "Sending personal data to Anthropic's API constitutes a GDPR Chapter V "
    "third-country transfer. Use OllamaProvider in production."
)


class AnthropicProvider:
    """Sends prompts to the Anthropic Claude API and returns parsed JSON.

    Temperature is omitted from the request by default: the newest Claude
    models (e.g. Opus 4.7) reject an explicit ``temperature`` with HTTP 400,
    and determinism is the model's server-side default. Pass an explicit
    temperature only for older models that still accept it. Anthropic has no
    response_mime_type equivalent; the consuming layer's user prompt already
    instructs raw JSON output via its output_format section, so the caller's
    system_prompt is forwarded unchanged.

    NOT FOR PRODUCTION — see module docstring.

    Args:
        model_name: Claude model identifier. Defaults to "claude-opus-4-7".
            (Named model_name — not model — to match the get_llm_provider
            dispatch contract and the other providers.)
        temperature: Optional sampling temperature. Defaults to None, which
            omits the parameter entirely (required for Opus 4.7 and other
            newest models). Set explicitly only for models that accept it.
        max_tokens: Upper bound on generated tokens for the JSON response.
        max_retries: Number of attempts on HTTP 429 (rate limit) before
            giving up. The SDK's own retry is disabled so this loop fully
            owns retry/backoff behaviour.

    Raises:
        LLMProviderError: Immediately at instantiation if ANTHROPIC_API_KEY is
            not set in the environment, or if the anthropic SDK is missing.
    """

    def __init__(
        self,
        model_name: str = "claude-opus-4-7",
        temperature: float | None = None,
        max_tokens: int = 4096,
        max_retries: int = 3,
    ) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMProviderError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "AnthropicProvider cannot be instantiated without an API key."
            )

        logger.warning(_PRODUCTION_WARNING)

        try:
            import anthropic  # noqa: PLC0415

            # max_retries=0: the hand-rolled retry loop in generate_json is the
            # single source of truth for retry/backoff (deterministic tests).
            self._client = anthropic.Anthropic(api_key=api_key, max_retries=0)
        except ImportError as exc:
            raise LLMProviderError(
                "anthropic is not installed. Run: pip install 'gdpr-classifier[llm]'"
            ) from exc

        self._model_name = model_name
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._max_retries = max_retries

    def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> dict:
        """Send prompt to Claude and return the parsed JSON response.

        On HTTP 429 the request is retried up to max_retries times, honouring
        the retry-after header when present, otherwise using exponential
        backoff (1s, 2s, 4s).

        Raises:
            LLMProviderError: On SDK exception, rate-limit exhaustion, non-JSON
                response, or empty response text.
        """
        request_kwargs: dict = {
            "model": self._model_name,
            "max_tokens": self._max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        # Newest models (Opus 4.7) reject an explicit temperature with HTTP
        # 400; only send it when the caller set one explicitly.
        if self._temperature is not None:
            request_kwargs["temperature"] = self._temperature
        if system_prompt is not None:
            request_kwargs["system"] = system_prompt

        response = None
        for attempt in range(self._max_retries):
            try:
                response = self._client.messages.create(**request_kwargs)
                break
            except Exception as exc:
                # Duck-typed 429 detection (the anthropic SDK's APIStatusError
                # exposes .status_code and .response.headers). Catching the
                # concrete SDK class is impossible when the SDK is mocked.
                if getattr(exc, "status_code", None) == 429:
                    if attempt == self._max_retries - 1:
                        raise LLMProviderError(
                            f"Anthropic API call failed after {self._max_retries} "
                            f"attempts (rate limited): {exc}"
                        ) from exc
                    wait = self._retry_after_seconds(exc)
                    if wait is None:
                        wait = float(2**attempt)
                    time.sleep(wait)
                    continue
                raise LLMProviderError(
                    f"Anthropic API call failed: {exc}"
                ) from exc

        content = getattr(response, "content", None)
        text = None
        if content:
            text = getattr(content[0], "text", None)
        raw = text or ""
        if not raw:
            raise LLMProviderError("Anthropic returned an empty response.")

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMProviderError(
                f"Anthropic response is not valid JSON (length={len(raw)} chars)."
            ) from exc

        if not isinstance(result, dict):
            raise LLMProviderError(
                f"generate_json expected a dict but Anthropic returned "
                f"{type(result).__name__}."
            )
        return result

    @staticmethod
    def _retry_after_seconds(exc: Exception) -> float | None:
        """Parse the retry-after header (seconds) from a 429 exception, if any."""
        headers = getattr(getattr(exc, "response", None), "headers", None)
        if headers is None:
            return None
        try:
            value = headers.get("retry-after")
        except AttributeError:
            return None
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
