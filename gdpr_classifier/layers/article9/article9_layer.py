"""Article 9 detection layer using LLM."""

from __future__ import annotations

import logging

from ...core.category import Category
from ...core.finding import Finding
from ...prompts.loader import load_prompt
from ..llm.provider import LLMProvider

logger = logging.getLogger(__name__)


class Article9LayerError(Exception):
    """Raised when Article9Layer fails to parse the LLM output."""


class Article9Layer:
    """Detection layer for explicit Article 9 data using an LLM.

    This layer detects explicitly mentioned Article 9 data (e.g. health data,
    religious beliefs) but does not evaluate identifiability. Identifiability
    is handled by CombinationLayer.
    """

    def __init__(self, provider: LLMProvider, prompt_version: str = "latest"):
        """Initialize the layer with an LLM provider and prompt version.

        Args:
            provider: An instance of an LLMProvider.
            prompt_version: The prompt version to use, defaults to "latest".
        """
        self._provider = provider
        self._prompt_version = prompt_version

    @property
    def name(self) -> str:
        """Name of the layer."""
        return "article9"

    def detect(self, text: str) -> list[Finding]:
        """Detect Article 9 data in the provided text.

        Args:
            text: The text to analyze.

        Returns:
            A list of Finding objects containing the detected Article 9 data.

        Raises:
            LLMProviderError: If the LLM provider fails.
            Article9LayerError: If the LLM output cannot be parsed or does not
                match the expected schema.
        """
        prompt = load_prompt("article9", version=self._prompt_version)
        
        user_prompt = f"{prompt.assembled_prompt}\n\nText att analysera:\n<<<\n{text}\n>>>\n"
        
        response = self._provider.generate_json(
            prompt=user_prompt,
            system_prompt=prompt.system_prompt,
        )
        
        if not isinstance(response, dict):
            raise Article9LayerError("Expected JSON response to be a dict.")
            
        if "findings" not in response:
            raise Article9LayerError("Missing 'findings' field in JSON response.")
            
        findings_data = response["findings"]
        if not isinstance(findings_data, list):
            raise Article9LayerError("'findings' field must be a list.")
            
        findings = []
        for f_data in findings_data:
            if not isinstance(f_data, dict):
                raise Article9LayerError("Each finding must be a dict.")
                
            cat_str = f_data.get("category")
            text_span = f_data.get("text_span")
            confidence = f_data.get("confidence")
            
            if not cat_str or not text_span or confidence is None:
                raise Article9LayerError("Finding missing required fields (category, text_span, confidence).")
                
            try:
                category = Category(f"article9.{cat_str}")
            except ValueError as e:
                raise Article9LayerError(f"Unknown category: {cat_str}") from e
                
            # Fallback text search: case-sensitive first, then case-insensitive
            start = text.find(text_span)
            actual_text_span = text_span
            
            if start == -1:
                # Case-insensitive search
                lower_text = text.lower()
                lower_span = text_span.lower()
                start = lower_text.find(lower_span)
                if start != -1:
                    # Extract the exact substring from the original text
                    actual_text_span = text[start:start+len(text_span)]
                else:
                    logger.debug("Hallucination detected: text_span '%s' not found in text.", text_span)
                    continue
                    
            end = start + len(actual_text_span)
            
            findings.append(Finding(
                category=category,
                start=start,
                end=end,
                text_span=actual_text_span,
                confidence=float(confidence),
                source=f"article9.{cat_str}"
            ))
            
        return findings
