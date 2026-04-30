"""GeminiProvider: LLMProvider implementation for the Google Gemini API.

WARNING — NOT FOR PRODUCTION USE (Beslut 17, Loggbok iteration 2):
Sending personal data to a third-party cloud service constitutes a transfer
under GDPR Chapter V. This provider is sanctioned only for development and
testing purposes where no real personal data is processed.

SDK: google-genai v1.x (the current unified Google AI Python SDK).
Do NOT use the legacy google-generativeai package.
"""

import json
import logging
import os

from gdpr_classifier.layers.llm.provider import LLMProviderError

logger = logging.getLogger(__name__)

_PRODUCTION_WARNING = (
    "GeminiProvider is not sanctioned for production use (Beslut 17). "
    "Sending personal data to Google's API constitutes a GDPR Chapter V "
    "third-country transfer. Use OllamaProvider in production."
)


class GeminiProvider:
    """Sends prompts to the Google Gemini API and returns parsed JSON.

    Uses response_mime_type='application/json' to request structured output
    and temperature=0.0 by default for deterministic responses
    (Karras et al., 2025).

    NOT FOR PRODUCTION — see module docstring.

    Args:
        model_name: Gemini model identifier (e.g. "gemini-1.5-flash").
            No default — the caller must choose explicitly.
        temperature: Sampling temperature. 0.0 is fully deterministic.

    Raises:
        LLMProviderError: Immediately at instantiation if GEMINI_API_KEY is
            not set in the environment.
    """

    def __init__(
        self,
        model_name: str,
        temperature: float = 0.0,
    ) -> None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise LLMProviderError(
                "GEMINI_API_KEY environment variable is not set. "
                "GeminiProvider cannot be instantiated without an API key."
            )

        logger.warning(_PRODUCTION_WARNING)

        try:
            import google.genai as genai  # noqa: PLC0415

            self._client = genai.Client(api_key=api_key)
        except ImportError as exc:
            raise LLMProviderError(
                "google-genai is not installed. Run: pip install 'gdpr-classifier[llm]'"
            ) from exc

        self._model_name = model_name
        self._temperature = temperature

    def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> dict:
        """Send prompt to Gemini and return the parsed JSON response.

        Raises:
            LLMProviderError: On SDK exception, non-JSON response, or empty
                response text.
        """
        try:
            import google.genai.types as genai_types  # noqa: PLC0415

            config_kwargs: dict = {
                "response_mime_type": "application/json",
                "temperature": self._temperature,
            }
            if system_prompt is not None:
                config_kwargs["system_instruction"] = system_prompt

            response = self._client.models.generate_content(
                model=self._model_name,
                contents=prompt,
                config=genai_types.GenerateContentConfig(**config_kwargs),
            )
        except Exception as exc:
            raise LLMProviderError(f"Gemini API call failed: {exc}") from exc

        raw = getattr(response, "text", None) or ""
        if not raw:
            raise LLMProviderError("Gemini returned an empty response.")

        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMProviderError(
                f"Gemini response is not valid JSON: {raw!r}"
            ) from exc
