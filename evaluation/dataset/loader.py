"""Dataset loader.

Loads labeled evaluation data from JSON files into LabeledText and
LabeledFinding instances for use by the evaluation runner.
"""
from __future__ import annotations

import json
from typing import Any

from gdpr_classifier.core.category import Category
from .labeled_finding import LabeledFinding
from .labeled_text import LabeledText


def load_dataset(path: str) -> list[LabeledText]:
    """Load evaluation dataset from a JSON file.

    Args:
        path: Path to the JSON dataset file.

    Returns:
        List of LabeledText instances.

    Raises:
        ValueError: If an invalid category string is found in the JSON.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = []
    for item in data:
        expected_findings = []
        for finding_data in item.get("expected_findings", []):
            try:
                category = Category(finding_data["category"])
            except ValueError as e:
                raise ValueError(
                    f"Invalid category '{finding_data['category']}' found in dataset."
                ) from e

            finding = LabeledFinding(
                category=category,
                start=finding_data["start"],
                end=finding_data["end"],
                text_span=finding_data["text_span"],
            )
            expected_findings.append(finding)

        labeled_text = LabeledText(
            text=item["text"],
            expected_findings=expected_findings,
            description=item.get("description", ""),
        )
        result.append(labeled_text)

    return result
