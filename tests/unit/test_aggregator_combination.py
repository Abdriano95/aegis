"""Unit tests for Aggregator combination logic and D5-correction (Issue #74).

Tests verify _determine_sensitivity() with kombinationslogik:
  a) article9.* findings → HIGH
  b) context.kombination with high_confidence_bypass → MEDIUM (bypass)
  c) context.kombination with Mekanism 3 evidence → MEDIUM
  d) context.kombination without sufficient evidence → falls through to LOW/NONE
  e) Isolated context.* findings (D5-correction) do not elevate sensitivity
  f) article4.* findings → LOW
  g) No findings → NONE
  h) Priority order: HIGH > MEDIUM > LOW
  i) Isolated context.* + article4 → LOW (D5 neither suppresses nor elevates)
"""

from __future__ import annotations

from gdpr_classifier.aggregator import Aggregator
from gdpr_classifier.core import Category, Finding, SensitivityLevel


def _make_finding(
    category: Category,
    start: int,
    end: int,
    *,
    confidence: float = 1.0,
    source: str = "test",
) -> Finding:
    """Helper to create a Finding with minimal boilerplate."""
    return Finding(
        category=category,
        start=start,
        end=end,
        text_span="x" * (end - start),
        confidence=confidence,
        source=source,
    )


class TestDetermineSensitivity:
    """Sensitivity determination with combination logic and D5-correction (SSOT §8)."""

    def test_article9_gives_high(self) -> None:
        """A single article9.* finding gives HIGH regardless of other findings."""
        halsodata = _make_finding(
            Category.HALSODATA,
            start=0,
            end=10,
            source="article9.halsodata",
        )
        email = _make_finding(
            Category.EMAIL,
            start=20,
            end=40,
            source="pattern.regex_email",
        )

        result = Aggregator().aggregate(
            findings=[halsodata, email],
            active_layers=["article9", "pattern"],
        )

        assert result.sensitivity == SensitivityLevel.HIGH

    def test_kombination_high_confidence_bypass_gives_medium(self) -> None:
        """context.kombination with confidence >= high_confidence_bypass gives MEDIUM."""
        kombination = _make_finding(
            Category.KOMBINATION,
            start=0,
            end=50,
            confidence=0.9,  # >= default high_confidence_bypass 0.85
            source="context.kombination",
        )

        result = Aggregator().aggregate(
            findings=[kombination],
            active_layers=["combination"],
        )

        assert result.sensitivity == SensitivityLevel.MEDIUM

    def test_kombination_mekanism3_sufficient_evidence_gives_medium(self) -> None:
        """context.kombination below bypass but with >= min_evidence_count L1/L2 overlaps gives MEDIUM."""
        kombination = _make_finding(
            Category.KOMBINATION,
            start=0,
            end=60,
            confidence=0.75,  # >= medium_threshold 0.7, < high_confidence_bypass 0.85
            source="context.kombination",
        )
        namn = _make_finding(
            Category.NAMN,
            start=0,
            end=15,
            source="entity.spacy_PRS",
        )
        email = _make_finding(
            Category.EMAIL,
            start=20,
            end=45,
            source="pattern.regex_email",
        )

        result = Aggregator().aggregate(
            findings=[kombination, namn, email],
            active_layers=["pattern", "entity", "combination"],
        )

        assert result.sensitivity == SensitivityLevel.MEDIUM

    def test_kombination_mekanism3_insufficient_evidence_with_article4_gives_low(self) -> None:
        """context.kombination below bypass with < min_evidence_count overlaps falls to LOW (article4 present)."""
        kombination = _make_finding(
            Category.KOMBINATION,
            start=0,
            end=60,
            confidence=0.75,  # >= medium_threshold 0.7, < high_confidence_bypass 0.85
            source="context.kombination",
        )
        # Only one overlapping L2 finding — below min_evidence_count=2
        namn = _make_finding(
            Category.NAMN,
            start=0,
            end=15,
            source="entity.spacy_PRS",
        )
        # article4 finding outside kombination span — no overlap, counts toward LOW
        email = _make_finding(
            Category.EMAIL,
            start=70,
            end=90,
            source="pattern.regex_email",
        )

        result = Aggregator().aggregate(
            findings=[kombination, namn, email],
            active_layers=["pattern", "entity", "combination"],
        )

        assert result.sensitivity == SensitivityLevel.LOW

    def test_isolated_context_signal_gives_none(self) -> None:
        """D5-correction: isolated context.* signal without kombination gives NONE."""
        organisation = _make_finding(
            Category.ORGANISATION,
            start=0,
            end=10,
            confidence=0.9,
            source="context.organisation",
        )

        result = Aggregator().aggregate(
            findings=[organisation],
            active_layers=["combination"],
        )

        assert result.sensitivity == SensitivityLevel.NONE

    def test_article4_without_kombination_gives_low(self) -> None:
        """article4.* finding without any kombination gives LOW."""
        email = _make_finding(
            Category.EMAIL,
            start=0,
            end=20,
            source="pattern.regex_email",
        )

        result = Aggregator().aggregate(
            findings=[email],
            active_layers=["pattern"],
        )

        assert result.sensitivity == SensitivityLevel.LOW

    def test_no_findings_gives_none(self) -> None:
        """Empty findings list gives NONE."""
        result = Aggregator().aggregate(
            findings=[],
            active_layers=["pattern"],
        )

        assert result.sensitivity == SensitivityLevel.NONE

    def test_high_trumps_medium(self) -> None:
        """article9.* finding gives HIGH even when a valid kombination is also present."""
        halsodata = _make_finding(
            Category.HALSODATA,
            start=0,
            end=10,
            source="article9.halsodata",
        )
        kombination = _make_finding(
            Category.KOMBINATION,
            start=0,
            end=50,
            confidence=0.9,  # would give MEDIUM alone
            source="context.kombination",
        )

        result = Aggregator().aggregate(
            findings=[halsodata, kombination],
            active_layers=["article9", "combination"],
        )

        assert result.sensitivity == SensitivityLevel.HIGH

    def test_isolated_context_with_article4_gives_low(self) -> None:
        """D5-correction: context.organisation + article4 gives LOW, not MEDIUM.

        Verifies that D5 neither suppresses the article4 LOW nor elevates
        sensitivity beyond what article4 findings alone warrant.
        """
        organisation = _make_finding(
            Category.ORGANISATION,
            start=0,
            end=15,
            confidence=0.9,
            source="context.organisation",
        )
        email = _make_finding(
            Category.EMAIL,
            start=20,
            end=45,
            source="pattern.regex_email",
        )

        result = Aggregator().aggregate(
            findings=[organisation, email],
            active_layers=["pattern", "combination"],
        )

        assert result.sensitivity == SensitivityLevel.LOW
