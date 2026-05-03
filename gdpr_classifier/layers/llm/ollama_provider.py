"""OllamaProvider: LLMProvider implementation for local Ollama instances."""

import json
import logging

import requests

from gdpr_classifier.layers.llm.provider import LLMProviderError

logger = logging.getLogger(__name__)


class OllamaProvider:
    """Sends prompts to a local Ollama instance and returns parsed JSON.

    Uses the /api/generate endpoint with format="json" to request structured
    output and temperature=0.0 by default for deterministic responses
    (Karras et al., 2025).

    Args:
        model_name: Name of the Ollama model to use (e.g. "llama3", "mistral").
            No default is provided — the caller must choose explicitly.
        endpoint: Base URL of the Ollama HTTP API.
        temperature: Sampling temperature. 0.0 is fully deterministic.
        timeout: HTTP request timeout in seconds. Increase for large models.
    """

    def __init__(
        self,
        model_name: str,
        endpoint: str = "http://localhost:11434",
        temperature: float = 0.0,
        timeout: int = 300,
    ) -> None:
        self._model_name = model_name
        self._endpoint = endpoint.rstrip("/")
        self._temperature = temperature
        self._timeout = timeout

    def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> dict:
        """Send prompt to Ollama and return the parsed JSON response.

        Raises:
            LLMProviderError: On network failure, HTTP error, non-JSON response,
                or empty response field.
        """
        payload: dict = {
            "model": self._model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "think": False,
            "options": {"temperature": self._temperature},
        }
        if system_prompt is not None:
            payload["system"] = system_prompt

        try:
            response = requests.post(
                f"{self._endpoint}/api/generate",
                json=payload,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise LLMProviderError(f"Ollama request failed: {exc}") from exc

        try:
            body = response.json()
        except ValueError as exc:
            raise LLMProviderError(
                f"Ollama returned non-JSON HTTP body "
                f"(status={response.status_code}, body length={len(response.text)} chars)."
            ) from exc

        raw = body.get("response", "")
        if not raw:
            raise LLMProviderError("Ollama returned an empty 'response' field.")

        logger.debug("Ollama raw response: %r", raw)

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMProviderError(
                f"Ollama 'response' field is not valid JSON "
                f"(length={len(raw)} chars)."
            ) from exc

        if not isinstance(result, dict):
            raise LLMProviderError(
                f"generate_json expected a dict but Ollama returned {type(result).__name__}."
            )
        return result
