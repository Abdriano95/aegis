"""Tests for the markdown parser in the candidate generation script."""

import pytest
from scripts.generate_article9_candidates import extract_guideline_section


@pytest.fixture
def sample_markdown():
    return """# Title

## 1. Introduction
This is the intro.

## 2. Categories

### 4.1 First Category
Here is info about the first category.
- Point 1
- Point 2

### 4.2 Second Category
Info about the second category.

## 5. Principles
These are the principles.
They apply broadly.

## 6. Next section
More text.
"""

def test_extract_guideline_section_found(sample_markdown):
    """Test extracting a specific section."""
    section = extract_guideline_section(sample_markdown, "4.1")
    assert "Here is info about the first category." in section
    assert "Point 1" in section
    assert "### 4.2" not in section

def test_extract_guideline_section_end_of_doc(sample_markdown):
    """Test extracting a section that goes to the end or next same-level header."""
    section = extract_guideline_section(sample_markdown, "5")
    assert "These are the principles." in section
    assert "## 6." not in section

def test_extract_guideline_section_not_found(sample_markdown):
    """Test extracting a non-existent section."""
    section = extract_guideline_section(sample_markdown, "9.9")
    assert section == ""

def test_extract_guideline_section_handles_different_header_levels():
    """Test that extraction stops at a header of the same or higher level."""
    md = """
### 4.1 Target
Some text.
#### Detail
More text.
## 5. Next major
Stop here.
"""
    section = extract_guideline_section(md, "4.1")
    assert "Some text." in section
    assert "#### Detail" in section
    assert "More text." in section
    assert "## 5. Next major" not in section
