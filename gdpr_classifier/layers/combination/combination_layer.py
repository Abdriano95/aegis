"""Combination layer using LLM for evaluating the puzzle-piece effect."""

from __future__ import annotations

import logging
import re

from ...core.category import Category
from ...core.finding import Finding
from ...prompts.loader import load_prompt
from ..llm.provider import LLMProvider

logger = logging.getLogger(__name__)


class CombinationLayerError(Exception):
    """Raised when CombinationLayer fails to parse the LLM output or schema."""


class CombinationLayer:
    """Detection layer for evaluating the puzzle-piece effect (GDPR Recital 26).
    
    This layer uses an LLM to determine if a combination of contextual signals
    (e.g., profession, location, organization) makes an individual identifiable
    even without direct identifiers.
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
        return "combination"

    def detect(self, text: str) -> list[Finding]:
        """Detect context signals and evaluate combinations in the provided text.

        Args:
            text: The text to analyze.

        Returns:
            A list of Finding objects containing the individual signals and
            optionally the combined finding.

        Raises:
            LLMProviderError: If the LLM provider fails.
            CombinationLayerError: If the LLM output cannot be parsed or does not
                match the expected schema.
        """
        prompt = load_prompt("combination", version=self._prompt_version)

        user_prompt = (
            f"{prompt.assembled_prompt}\n\nText att analysera:\n<<<\n{text}\n>>>\n"
        )

        response = self._provider.generate_json(
            prompt=user_prompt,
            system_prompt=prompt.system_prompt,
        )

        if not isinstance(response, dict):
            raise CombinationLayerError("Expected JSON response to be a dict.")

        if "individual_signals" not in response or "combination" not in response:
            raise CombinationLayerError(
                "Missing 'individual_signals' or 'combination' field in JSON response."
            )

        individual_signals_data = response["individual_signals"]
        combination_data = response["combination"]

        if not isinstance(individual_signals_data, list):
            raise CombinationLayerError("'individual_signals' field must be a list.")
        if not isinstance(combination_data, dict):
            raise CombinationLayerError("'combination' field must be a dict.")

        findings: list[Finding] = []
        valid_individual_findings: list[Finding] = []

        allowed_signals = {"yrke", "plats", "organisation"}

        # Step 2: Individual signals
        for sig_data in individual_signals_data:
            if not isinstance(sig_data, dict):
                raise CombinationLayerError("Each individual signal must be a dict.")

            signal_str = sig_data.get("signal")
            text_span = sig_data.get("text_span")
            confidence = sig_data.get("confidence")

            if not signal_str or not text_span or confidence is None:
                raise CombinationLayerError(
                    "Individual signal missing required fields (signal, text_span, confidence)."
                )

            if signal_str not in allowed_signals:
                raise CombinationLayerError(f"Invalid signal type: {signal_str}")

            try:
                confidence_float = float(confidence)
            except (TypeError, ValueError) as e:
                raise CombinationLayerError(
                    f"Invalid confidence value: {confidence}"
                ) from e

            category = Category(f"context.{signal_str}")

            # Validation: exact match then case-insensitive
            start = text.find(text_span)
            actual_text_span = text_span

            if start == -1:
                lower_text = text.lower()
                lower_span = text_span.lower()
                start = lower_text.find(lower_span)
                if start != -1:
                    actual_text_span = text[start : start + len(text_span)]
                else:
                    logger.debug(
                        "Hallucination detected for individual signal: text_span '%s' not found.",
                        text_span,
                    )
                    continue

            end = start + len(actual_text_span)

            finding = Finding(
                category=category,
                start=start,
                end=end,
                text_span=actual_text_span,
                confidence=confidence_float,
                source=f"context.{signal_str}",
            )
            findings.append(finding)
            valid_individual_findings.append(finding)

        # Step 3: Combination aggregate finding
        is_identifiable = combination_data.get("is_identifiable")
        if is_identifiable is True:
            text_span = combination_data.get("text_span")
            confidence = combination_data.get("confidence")
            reasoning = combination_data.get("reasoning")

            if not text_span or confidence is None or not reasoning:
                raise CombinationLayerError(
                    "Combination data missing required fields (text_span, confidence, reasoning)."
                )

            try:
                confidence_float = float(confidence)
            except (TypeError, ValueError) as e:
                raise CombinationLayerError(
                    f"Invalid confidence value for combination: {confidence}"
                ) from e

            # Tolerant validation
            start = text.find(text_span)
            actual_text_span = text_span
            validation_path = None

            if start != -1:
                validation_path = "exact"
            else:
                # insensitive
                lower_text = text.lower()
                lower_span = text_span.lower()
                start = lower_text.find(lower_span)
                if start != -1:
                    actual_text_span = text[start : start + len(text_span)]
                    validation_path = "insensitive"
                else:
                    # normalized
                    non_ws_span = re.sub(r"\s+", "", text_span)
                    if non_ws_span:
                        # Map back to original indices (rough approximation by finding sequence of chars)
                        match = re.search(r"\s*".join(map(re.escape, non_ws_span)), text)
                        if match:
                            start = match.start()
                            actual_text_span = match.group(0)
                            validation_path = "normalized"

            if validation_path is None:
                # reconstructed
                if len(valid_individual_findings) >= 2:
                    start = min(f.start for f in valid_individual_findings)
                    end = max(f.end for f in valid_individual_findings)
                    actual_text_span = text[start:end]
                    validation_path = "reconstructed"
                else:
                    logger.warning(
                        "Hallucination detected for combination span and insufficient valid signals to reconstruct: '%s'.",
                        text_span,
                    )
                    return findings

            if validation_path is not None:
                end = start + len(actual_text_span)
                findings.append(
                    Finding(
                        category=Category.KOMBINATION,
                        start=start,
                        end=end,
                        text_span=actual_text_span,
                        confidence=confidence_float,
                        source="context.kombination",
                        metadata={
                            "reasoning": reasoning,
                            "validation_path": validation_path,
                        },
                    )
                )

        return findings
