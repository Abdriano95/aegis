"""Unit tests for scripts/validate_combination_dataset.py."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.validate_combination_dataset import validate_entry

TEXT = "Anna Svensson arbetar som sjuksköterska vid Sahlgrenska sjukhuset i Göteborg."


def _finding(category, text_span, specificity_level=None, is_identifiable=None):
    start = TEXT.find(text_span)
    assert start != -1, f"'{text_span}' not found in TEXT"
    end = start + len(text_span)
    f = {"category": category, "text_span": text_span, "start": start, "end": end}
    if specificity_level is not None:
        f["specificity_level"] = specificity_level
    if is_identifiable is not None:
        f["is_identifiable"] = is_identifiable
    return f


def _aggregate(individual_findings):
    start = min(f["start"] for f in individual_findings)
    end = max(f["end"] for f in individual_findings)
    text_span = TEXT[start:end]
    return {
        "category": "context.kombination",
        "text_span": text_span,
        "start": start,
        "end": end,
        "is_identifiable": True,
    }


def test_valid_cell1_entry():
    """Entry with 2 individual findings + consistent aggregate — no errors."""
    yrke = _finding("context.yrke", "sjuksköterska", "hög")
    plats = _finding("context.plats", "Göteborg", "hög")
    agg = _aggregate([yrke, plats])
    entry = {
        "text": TEXT,
        "description": "Yrkestitel och stad.",
        "expected_findings": [yrke, plats, agg],
    }
    assert validate_entry(entry, 0) == []


def test_valid_cell3_entry():
    """Entry with empty expected_findings (Cell 3 negative) — no errors."""
    entry = {
        "text": TEXT,
        "description": "Ingen identifierbar information.",
        "expected_findings": [],
    }
    assert validate_entry(entry, 0) == []


def test_valid_cell4_entry():
    """Entry with 2 individual findings but no aggregate — no errors."""
    yrke = _finding("context.yrke", "sjuksköterska", "hög")
    plats = _finding("context.plats", "Göteborg", "hög")
    entry = {
        "text": TEXT,
        "description": "Separata signaler utan aggregat.",
        "expected_findings": [yrke, plats],
    }
    assert validate_entry(entry, 0) == []


def test_invalid_aggregate_consistency():
    """Aggregate whose start doesn't match min(individual starts) — error."""
    yrke = _finding("context.yrke", "sjuksköterska", "hög")
    plats = _finding("context.plats", "Göteborg", "hög")
    agg = _aggregate([yrke, plats])
    agg["start"] = agg["start"] + 2  # deliberately wrong
    agg["text_span"] = TEXT[agg["start"]:agg["end"]]
    entry = {
        "text": TEXT,
        "description": "Aggregat med fel start-offset.",
        "expected_findings": [yrke, plats, agg],
    }
    errors = validate_entry(entry, 0)
    assert any("aggregate start" in e for e in errors)


def test_invalid_text_span_offset():
    """text[start:end] doesn't match text_span — error."""
    yrke = _finding("context.yrke", "sjuksköterska", "hög")
    yrke["text_span"] = "sjuksköterskX"  # wrong span text
    entry = {
        "text": TEXT,
        "description": "Fel text_span.",
        "expected_findings": [yrke],
    }
    errors = validate_entry(entry, 0)
    assert any("not found at" in e for e in errors)


def test_invalid_specificity_level():
    """specificity_level value not in allowed set — error."""
    yrke = _finding("context.yrke", "sjuksköterska", "medium")  # invalid
    entry = {
        "text": TEXT,
        "description": "Ogiltig specificity_level.",
        "expected_findings": [yrke],
    }
    errors = validate_entry(entry, 0)
    assert any("specificity_level" in e for e in errors)


def test_aggregate_without_individual():
    """Aggregate finding with no individual signals — error."""
    agg = {
        "category": "context.kombination",
        "text_span": "sjuksköterska",
        "start": TEXT.find("sjuksköterska"),
        "end": TEXT.find("sjuksköterska") + len("sjuksköterska"),
        "is_identifiable": True,
    }
    entry = {
        "text": TEXT,
        "description": "Aggregat utan signaler.",
        "expected_findings": [agg],
    }
    errors = validate_entry(entry, 0)
    assert any("individual" in e for e in errors)


def test_multiple_aggregates_rejected():
    """Two aggregate findings in one entry — error."""
    yrke = _finding("context.yrke", "sjuksköterska", "hög")
    plats = _finding("context.plats", "Göteborg", "hög")
    agg1 = _aggregate([yrke, plats])
    agg2 = dict(agg1)
    entry = {
        "text": TEXT,
        "description": "Två aggregat.",
        "expected_findings": [yrke, plats, agg1, agg2],
    }
    errors = validate_entry(entry, 0)
    assert any("only one aggregate" in e for e in errors)
