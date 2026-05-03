"""Unit tests for Aggregator article9-context containment rule (Omgång 3).

Tests verify that context.organisation and context.yrke findings whose span
is completely covered by an article9.* finding are removed, while:
  a) Non-overlapping context signals are kept
  b) article4.* findings are not affected
  c) Partially overlapping context signals are kept (only full containment triggers)
  d) article9 findings themselves are always kept
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
    return Finding(
        category=category,
        start=start,
        end=end,
        text_span="x" * (end - start),
        confidence=confidence,
        source=source,
    )


class TestContainmentArticle9ContextSignals:
    """article9-context containment rule (SSOT §8, §14.1)."""

    def test_organisation_fully_covered_by_article9_removed(self) -> None:
        """context.organisation span completely inside article9 span → removed."""
        # Simulates: "Unionen" at [10,17) fully inside article9.fackmedlemskap [0,40)
        article9 = _make_finding(
            Category.FACKMEDLEMSKAP,
            start=0,
            end=40,
            confidence=0.95,
            source="article9.fackmedlemskap",
        )
        org = _make_finding(
            Category.ORGANISATION,
            start=10,
            end=17,
            confidence=0.9,
            source="context.organisation",
        )

        result = Aggregator().aggregate(
            findings=[article9, org],
            active_layers=["article9", "combination"],
        )

        assert article9 in result.findings
        assert org not in result.findings
        assert len(result.findings) == 1

    def test_organisation_not_overlapping_article9_kept(self) -> None:
        """context.organisation with disjoint span from article9 → both kept."""
        article9 = _make_finding(
            Category.FACKMEDLEMSKAP,
            start=0,
            end=30,
            confidence=0.95,
            source="article9.fackmedlemskap",
        )
        org = _make_finding(
            Category.ORGANISATION,
            start=50,
            end=70,
            confidence=0.9,
            source="context.organisation",
        )

        result = Aggregator().aggregate(
            findings=[article9, org],
            active_layers=["article9", "combination"],
        )

        assert article9 in result.findings
        assert org in result.findings
        assert len(result.findings) == 2

    def test_article4_not_affected_by_article9(self) -> None:
        """article4.* findings whose span overlaps article9 are never removed."""
        article9 = _make_finding(
            Category.FACKMEDLEMSKAP,
            start=0,
            end=30,
            confidence=0.95,
            source="article9.fackmedlemskap",
        )
        personnummer = _make_finding(
            Category.PERSONNUMMER,
            start=5,
            end=16,
            confidence=1.0,
            source="pattern.luhn_personnummer",
        )

        result = Aggregator().aggregate(
            findings=[article9, personnummer],
            active_layers=["pattern", "article9"],
        )

        assert article9 in result.findings
        assert personnummer in result.findings
        assert len(result.findings) == 2

    def test_partial_overlap_organisation_kept(self) -> None:
        """context.organisation extending beyond article9 span → kept (not full containment)."""
        # article9 is inside organisation, not the other way around
        article9 = _make_finding(
            Category.FACKMEDLEMSKAP,
            start=10,
            end=30,
            confidence=0.95,
            source="article9.fackmedlemskap",
        )
        org = _make_finding(
            Category.ORGANISATION,
            start=0,
            end=40,
            confidence=0.9,
            source="context.organisation",
        )

        result = Aggregator().aggregate(
            findings=[article9, org],
            active_layers=["article9", "combination"],
        )

        assert article9 in result.findings
        assert org in result.findings
        assert len(result.findings) == 2

    def test_yrke_fully_covered_by_article9_removed(self) -> None:
        """context.yrke span completely inside article9 span → removed."""
        article9 = _make_finding(
            Category.RELIGIOS_OVERTYGELSE,
            start=0,
            end=50,
            confidence=0.95,
            source="article9.religios_overtygelse",
        )
        yrke = _make_finding(
            Category.YRKE,
            start=5,
            end=25,
            confidence=0.8,
            source="context.yrke",
        )

        result = Aggregator().aggregate(
            findings=[article9, yrke],
            active_layers=["article9", "combination"],
        )

        assert article9 in result.findings
        assert yrke not in result.findings
        assert len(result.findings) == 1

    def test_sensitivity_high_after_article9_filter(self) -> None:
        """Sensitivity remains HIGH after context signal is removed by article9 filter."""
        article9 = _make_finding(
            Category.FACKMEDLEMSKAP,
            start=0,
            end=40,
            confidence=0.95,
            source="article9.fackmedlemskap",
        )
        org = _make_finding(
            Category.ORGANISATION,
            start=5,
            end=30,
            confidence=0.9,
            source="context.organisation",
        )

        result = Aggregator().aggregate(
            findings=[article9, org],
            active_layers=["article9", "combination"],
        )

        assert result.sensitivity == SensitivityLevel.HIGH
        assert org not in result.findings
