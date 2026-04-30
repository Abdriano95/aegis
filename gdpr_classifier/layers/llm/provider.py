"""LLMProvider protocol and shared exception for all LLM provider implementations."""

from typing import Protocol, runtime_checkable


class LLMProviderError(Exception):
    """Raised by any LLMProvider on network error, parse failure, or empty response."""


@runtime_checkable
class LLMProvider(Protocol):
    """Minimal contract for pluggable LLM providers.

    Providers accept a prompt and an optional system prompt, send a request to
    the underlying model, and return the parsed JSON response as a dict.
    Schema validation of the returned dict is the responsibility of the
    consuming layer, not the provider.
    """

    def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> dict:
        """Send prompt to the model and return its response as a parsed dict.

        Args:
            prompt: The user-facing instruction or query.
            system_prompt: Optional system-level instruction prepended to the
                conversation context.

        Returns:
            The model's JSON response parsed into a Python dict.

        Raises:
            LLMProviderError: On network failure, non-JSON response, or empty
                response from the model.
        """
        ...
