"""Unit tests for the evaluation dataset loader."""

from __future__ import annotations

import json
import pytest

from gdpr_classifier.core.category import Category
from evaluation.dataset.loader import load_dataset


def test_load_dataset_success(tmp_path):
    """Verify that a correctly formatted JSON loads into Python objects."""
    data = [
        {
            "text": "Kontakta mig på anna.svensson@mail.se, mitt personnummer är 850101-1234.",
            "description": "Text med e-post och personnummer",
            "expected_findings": [
                {
                    "category": "article4.email",
                    "start": 19,
                    "end": 42,
                    "text_span": "anna.svensson@mail.se"
                },
                {
                    "category": "article4.personnummer",
                    "start": 62,
                    "end": 73,
                    "text_span": "850101-1234"
                }
            ]
        },
        {
            "text": "Mötet börjar klockan 14:00 i konferensrum B.",
            "description": "Okänslig text utan personuppgifter",
            "expected_findings": []
        }
    ]

    test_file = tmp_path / "test_success.json"
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(data, f)
        
    dataset = load_dataset(str(test_file))
    
    assert len(dataset) == 2
    
    # Check first item
    assert dataset[0].text == "Kontakta mig på anna.svensson@mail.se, mitt personnummer är 850101-1234."
    assert dataset[0].description == "Text med e-post och personnummer"
    assert len(dataset[0].expected_findings) == 2
    
    # Check first finding
    finding1 = dataset[0].expected_findings[0]
    assert finding1.category == Category.EMAIL
    assert finding1.start == 19
    assert finding1.end == 42
    assert finding1.text_span == "anna.svensson@mail.se"
    
    # Check second finding
    finding2 = dataset[0].expected_findings[1]
    assert finding2.category == Category.PERSONNUMMER
    assert finding2.start == 62
    assert finding2.end == 73
    assert finding2.text_span == "850101-1234"
    
    # Check second item
    assert dataset[1].text == "Mötet börjar klockan 14:00 i konferensrum B."
    assert dataset[1].description == "Okänslig text utan personuppgifter"
    assert len(dataset[1].expected_findings) == 0


def test_load_dataset_invalid_category_raises_error(tmp_path):
    """Verify that an invalid category in the JSON raises ValueError."""
    data = [
        {
            "text": "Some text",
            "expected_findings": [
                {
                    "category": "article4.ogiltig",
                    "start": 0,
                    "end": 4,
                    "text_span": "Some"
                }
            ]
        }
    ]

    test_file = tmp_path / "test_invalid.json"
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(data, f)
        
    with pytest.raises(ValueError) as excinfo:
        load_dataset(str(test_file))
        
    assert "Invalid category 'article4.ogiltig' found in dataset." in str(excinfo.value)
