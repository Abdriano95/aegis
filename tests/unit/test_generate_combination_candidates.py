"""Unit tests for guide-parser and aggregate helpers in generate_combination_candidates.py."""
from __future__ import annotations

import sys
from pathlib import Path

# scripts/ is not a package; add it to sys.path for direct import
_SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

import generate_combination_candidates as gcc  # noqa: E402

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_GUIDE_PATH = _PROJECT_ROOT / "docs" / "combination_annotation_guidelines.md"


# ---------------------------------------------------------------------------
# extract_guide_sections
# ---------------------------------------------------------------------------

def test_extract_guide_sections_returns_nonempty_dict():
    sections = gcc.extract_guide_sections(_GUIDE_PATH)
    assert isinstance(sections, dict)
    assert len(sections) > 0


def test_extract_guide_sections_contains_section_3():
    sections = gcc.extract_guide_sections(_GUIDE_PATH)
    assert any(k.startswith("3") for k in sections), (
        "Expected section '3' or sub-sections ('3.1', '3.2', ...) in result"
    )


def test_extract_guide_sections_section_3_text_contains_yrke():
    sections = gcc.extract_guide_sections(_GUIDE_PATH)
    section_3 = sections.get("3", "") or sections.get("3.1", "")
    assert "yrke" in section_3.lower() or "Yrke" in section_3


def test_extract_guide_sections_has_section_52():
    sections = gcc.extract_guide_sections(_GUIDE_PATH)
    assert "5.2" in sections, "Section 5.2 (combination rules) must be present"


# ---------------------------------------------------------------------------
# extract_combination_rule
# ---------------------------------------------------------------------------

def test_extract_combination_rule_a_nonempty():
    text = gcc.extract_combination_rule(_GUIDE_PATH, "A")
    assert text != "", "Rule A text should not be empty"


def test_extract_combination_rule_a_contains_label():
    text = gcc.extract_combination_rule(_GUIDE_PATH, "A")
    assert "Regel A" in text


def test_extract_combination_rule_b_contains_label():
    text = gcc.extract_combination_rule(_GUIDE_PATH, "B")
    assert "Regel B" in text


def test_extract_combination_rule_c_contains_label():
    text = gcc.extract_combination_rule(_GUIDE_PATH, "C")
    assert "Regel C" in text


def test_extract_combination_rule_d_contains_label():
    text = gcc.extract_combination_rule(_GUIDE_PATH, "D")
    assert "Regel D" in text


def test_extract_combination_rule_a_does_not_contain_rule_b():
    text = gcc.extract_combination_rule(_GUIDE_PATH, "A")
    assert "Regel B" not in text, "Rule A extract should not bleed into Rule B"


# ---------------------------------------------------------------------------
# compute_aggregate_span
# ---------------------------------------------------------------------------

def test_compute_aggregate_span_full_string():
    """'chef' at 0 and 'Göteborg' at end → aggregate covers full string."""
    text = "chef på Volvo i Göteborg"
    findings = [{"text_span": "chef"}, {"text_span": "Göteborg"}]
    result = gcc.compute_aggregate_span(text, findings)
    assert result["category"] == "context.kombination"
    assert result["text_span"] == text
    assert result["start"] == 0
    assert result["end"] == len(text)
    assert result["is_identifiable"] is True


def test_compute_aggregate_span_partial():
    """Middle span: aggregate covers from first to last signal."""
    text = "Ekonomichefen på Borås Stad jobbar övertid"
    findings = [{"text_span": "Ekonomichefen"}, {"text_span": "Borås Stad"}]
    result = gcc.compute_aggregate_span(text, findings)
    assert result["text_span"] == "Ekonomichefen på Borås Stad"
    assert result["start"] == 0
    assert result["end"] == len("Ekonomichefen på Borås Stad")


def test_compute_aggregate_span_no_specificity_level():
    """Aggregate dict must NOT contain specificity_level (intentional design)."""
    text = "VD på Hvitfeldtska gymnasiets musiklinje"
    findings = [{"text_span": "VD"}, {"text_span": "Hvitfeldtska gymnasiets musiklinje"}]
    result = gcc.compute_aggregate_span(text, findings)
    assert "specificity_level" not in result, (
        "Aggregate finding must not carry specificity_level; "
        "only individual signals carry this field (FAS B annotators verify at signal level)"
    )


# ---------------------------------------------------------------------------
# _should_add_aggregate_cell2
# ---------------------------------------------------------------------------

def test_cell2_rule_a_two_high():
    findings = [
        {"text_span": "VD", "specificity_level": "hög"},
        {"text_span": "Hjo", "specificity_level": "hög"},
    ]
    assert gcc._should_add_aggregate_cell2(findings) is True


def test_cell2_rule_b_three_mellan():
    findings = [
        {"text_span": "barnmorska", "specificity_level": "mellan"},
        {"text_span": "Borås", "specificity_level": "mellan"},
        {"text_span": "Borås Stad", "specificity_level": "mellan"},
    ]
    assert gcc._should_add_aggregate_cell2(findings) is True


def test_cell2_no_trigger_two_mellan():
    """Two mellan signals → Rule B not met (needs ≥3); Rule A not met (needs 2 hög)."""
    findings = [
        {"text_span": "barnmorska", "specificity_level": "mellan"},
        {"text_span": "Borås", "specificity_level": "mellan"},
    ]
    assert gcc._should_add_aggregate_cell2(findings) is False


def test_cell2_no_trigger_one_high_one_low():
    findings = [
        {"text_span": "VD", "specificity_level": "hög"},
        {"text_span": "Stockholm", "specificity_level": "låg"},
    ]
    assert gcc._should_add_aggregate_cell2(findings) is False
