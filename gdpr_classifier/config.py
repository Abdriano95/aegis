"""Pipeline configuration.

Holds configuration for the classifier: which layers are active,
confidence thresholds per layer or category, and other tunable
parameters used by the pipeline and the aggregator.
"""

import os


def get_llm_provider(model_name: str):
    """Instantiate the configured LLM provider.

    Reads the LLM_PROVIDER environment variable to select the backend.
    Accepted values: "ollama" (default), "gemini", "anthropic".

    Args:
        model_name: Model identifier forwarded to the provider constructor.
            The caller must choose a model explicitly — no default is applied.

    Returns:
        An LLMProvider instance for the selected backend.
    """
    from gdpr_classifier.layers.llm import (  # noqa: PLC0415
        AnthropicProvider,
        GeminiProvider,
        OllamaProvider,
    )

    provider = os.environ.get("LLM_PROVIDER", "ollama").lower()
    if provider == "gemini":
        return GeminiProvider(model_name=model_name)
    if provider == "anthropic":
        return AnthropicProvider(model_name=model_name)
    if provider == "ollama":
        return OllamaProvider(model_name=model_name)
    raise ValueError(
        f"Unknown LLM_PROVIDER value {provider!r}. "
        "Allowed values: 'ollama', 'gemini', 'anthropic'."
    )
