"""Tests for the Article 9 test dataset schema."""

import json
from pathlib import Path

import pytest

from evaluation.dataset.loader import load_dataset
from gdpr_classifier.core.category import Category


DATA_DIR = Path(__file__).parent.parent / "data" / "iteration_2"
DATASET_PATH = DATA_DIR / "article9_dataset.json"
CANDIDATES_PATH = DATA_DIR / "article9_dataset_candidates.json"


def test_dataset_schema_empty():
    """Verify that the empty placeholder dataset is valid."""
    assert DATASET_PATH.exists(), "Dataset file is missing."
    
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list)
    
    # Should not raise any errors
    loaded = load_dataset(str(DATASET_PATH))
    assert isinstance(loaded, list)


@pytest.mark.skipif(not CANDIDATES_PATH.exists(), reason="Candidates dataset not generated yet.")
def test_candidates_schema_valid():
    """Verify that the generated candidates conform to the schema."""
    # First ensure the loader can parse it
    try:
        loaded = load_dataset(str(CANDIDATES_PATH))
    except Exception as e:
        pytest.fail(f"load_dataset failed on candidates: {e}")
        
    assert len(loaded) > 0, "Candidates file is empty."
    
    # Then do strict checking on text spans (loader doesn't enforce substring match)
    with open(CANDIDATES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    for i, item in enumerate(data):
        text = item["text"]
        
        # Verify it has a description
        assert "description" in item
        assert isinstance(item["description"], str)
        
        for j, finding in enumerate(item.get("expected_findings", [])):
            # category is already validated by loader
            start = finding["start"]
            end = finding["end"]
            text_span = finding["text_span"]
            
            assert isinstance(start, int), f"Item {i}, Finding {j}: start is not int"
            assert isinstance(end, int), f"Item {i}, Finding {j}: end is not int"
            assert start >= 0, f"Item {i}, Finding {j}: start < 0"
            assert end <= len(text), f"Item {i}, Finding {j}: end > text length"
            assert start < end, f"Item {i}, Finding {j}: start >= end"
            
            actual_span = text[start:end]
            assert actual_span == text_span, f"Item {i}, Finding {j}: text_span mismatch. Expected '{text_span}', got '{actual_span}'"
