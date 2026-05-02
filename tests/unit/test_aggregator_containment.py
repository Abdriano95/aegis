"""Unit tests for Aggregator containment rules (Issue #76).

Tests verify that the IBAN-telefon containment rule correctly handles:
  a) Overlapping IBAN + telefon → telefon removed, IBAN kept
  b) Non-overlapping IBAN + telefon → both kept
  c) Overlapping findings of other categories → rule not applied, both kept
"""

from __future__ import annotations

import pytest

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


class TestContainmentIbanTelefon:
    """IBAN-telefon containment rule (SSOT §8, §14.1)."""

    def test_overlapping_iban_telefon_removes_telefon(self) -> None:
        """When telefon span overlaps with IBAN span, telefon is removed."""
        # Simulates: IBAN "SE96 5000 0000 0555 5555 55" at [0, 26)
        #            telefon "0555 5555 55" at [15, 26)  — fully contained
        iban = _make_finding(
            Category.IBAN,
            start=0,
            end=26,
            confidence=1.0,
            source="pattern.checksum_iban",
        )
        telefon = _make_finding(
            Category.TELEFONNUMMER,
            start=15,
            end=26,
            confidence=0.9,
            source="pattern.regex_telefon",
        )

        result = Aggregator().aggregate(
            findings=[iban, telefon],
            active_layers=["pattern"],
        )

        assert iban in result.findings
        assert telefon not in result.findings
        assert len(result.findings) == 1

    def test_non_overlapping_iban_telefon_both_kept(self) -> None:
        """IBAN and telefon with disjoint spans are both preserved."""
        iban = _make_finding(
            Category.IBAN,
            start=0,
            end=26,
            confidence=1.0,
            source="pattern.checksum_iban",
        )
        telefon = _make_finding(
            Category.TELEFONNUMMER,
            start=50,
            end=64,
            confidence=0.9,
            source="pattern.regex_telefon",
        )

        result = Aggregator().aggregate(
            findings=[iban, telefon],
            active_layers=["pattern"],
        )

        assert iban in result.findings
        assert telefon in result.findings
        assert len(result.findings) == 2

    def test_boundary_touching_iban_telefon_both_kept(self) -> None:
        """Boundary-touching intervals (telefon.start == iban.end) are not overlapping."""
        iban = _make_finding(
            Category.IBAN,
            start=0,
            end=26,
            confidence=1.0,
            source="pattern.checksum_iban",
        )
        telefon = _make_finding(
            Category.TELEFONNUMMER,
            start=26,
            end=40,
            confidence=0.9,
            source="pattern.regex_telefon",
        )

        result = Aggregator().aggregate(
            findings=[iban, telefon],
            active_layers=["pattern"],
        )

        assert iban in result.findings
        assert telefon in result.findings
        assert len(result.findings) == 2

    def test_overlapping_other_categories_both_kept(self) -> None:
        """Overlap between non-IBAN/telefon categories is not affected."""
        personnummer = _make_finding(
            Category.PERSONNUMMER,
            start=10,
            end=23,
            confidence=1.0,
            source="pattern.luhn_personnummer",
        )
        email = _make_finding(
            Category.EMAIL,
            start=15,
            end=38,
            confidence=1.0,
            source="pattern.regex_email",
        )

        result = Aggregator().aggregate(
            findings=[personnummer, email],
            active_layers=["pattern"],
        )

        assert personnummer in result.findings
        assert email in result.findings
        assert len(result.findings) == 2

    def test_multiple_telefon_overlapping_same_iban(self) -> None:
        """All telefon findings overlapping the same IBAN are removed."""
        iban = _make_finding(
            Category.IBAN,
            start=0,
            end=30,
            confidence=1.0,
            source="pattern.checksum_iban",
        )
        telefon_1 = _make_finding(
            Category.TELEFONNUMMER,
            start=10,
            end=22,
            confidence=0.9,
            source="pattern.regex_telefon",
        )
        telefon_2 = _make_finding(
            Category.TELEFONNUMMER,
            start=18,
            end=30,
            confidence=0.9,
            source="pattern.regex_telefon",
        )

        result = Aggregator().aggregate(
            findings=[iban, telefon_1, telefon_2],
            active_layers=["pattern"],
        )

        assert iban in result.findings
        assert telefon_1 not in result.findings
        assert telefon_2 not in result.findings
        assert len(result.findings) == 1

    def test_sensitivity_not_affected_by_removed_telefon(self) -> None:
        """Sensitivity should be LOW (article4 IBAN), not inflated by the removed telefon."""
        iban = _make_finding(
            Category.IBAN,
            start=0,
            end=26,
            confidence=1.0,
            source="pattern.checksum_iban",
        )
        telefon = _make_finding(
            Category.TELEFONNUMMER,
            start=15,
            end=26,
            confidence=0.9,
            source="pattern.regex_telefon",
        )

        result = Aggregator().aggregate(
            findings=[iban, telefon],
            active_layers=["pattern"],
        )

        assert result.sensitivity == SensitivityLevel.LOW

    def test_overlapping_findings_excludes_removed_telefon(self) -> None:
        """Removed telefon should not appear in overlapping_findings pairs."""
        iban = _make_finding(
            Category.IBAN,
            start=0,
            end=26,
            confidence=1.0,
            source="pattern.checksum_iban",
        )
        telefon = _make_finding(
            Category.TELEFONNUMMER,
            start=15,
            end=26,
            confidence=0.9,
            source="pattern.regex_telefon",
        )

        result = Aggregator().aggregate(
            findings=[iban, telefon],
            active_layers=["pattern"],
        )

        assert result.overlapping_findings == []
