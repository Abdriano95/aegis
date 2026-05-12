"""Unit tests for Aggregator same-category deduplication (Issue #103).

Tests verify that ``_deduplicate_same_category_overlap`` correctly handles:
  a) Same-category overlap from different layers → higher confidence kept,
     lower removed, source propagated to metadata.
  b) Same-category disjoint spans → both kept.
  c) Cross-category overlap → both kept (out-of-scope guard).
  d) Tiebreaker at equal confidence → stable input order.
  e) Chained same-category overlap → highest confidence kept, sources merged.
  f) Sensitivity unaffected by same-category dedup.

See SSOT arkitektur.md §8 and docs/iteration_2_utvardering.md Del 7 for
motivation.
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


class TestSameCategoryDedup:
    """Same-category dedup (SSOT §8, Issue #103)."""

    def test_same_category_overlap_keeps_higher_confidence(self) -> None:
        """EntityLayer + CombinationLayer parallel ORG detection → higher kept."""
        entity_org = _make_finding(
            Category.ORGANISATION,
            start=0,
            end=10,
            confidence=0.8,
            source="entity.spacy_ORG",
        )
        kombination_org = _make_finding(
            Category.ORGANISATION,
            start=0,
            end=10,
            confidence=0.95,
            source="context.organisation",
        )

        result = Aggregator().aggregate(
            findings=[entity_org, kombination_org],
            active_layers=["entity", "combination"],
        )

        assert len(result.findings) == 1
        kept = result.findings[0]
        assert kept.confidence == 0.95
        assert kept.source == "context.organisation"
        assert kept.metadata is not None
        assert kept.metadata["deduplicated_sources"] == ["entity.spacy_ORG"]
        # Same-category overlap removed from overlapping_findings.
        assert result.overlapping_findings == []

    def test_same_category_disjoint_spans_both_kept(self) -> None:
        """Two ORGANISATION findings with non-overlapping spans → both kept."""
        org_a = _make_finding(
            Category.ORGANISATION,
            start=0,
            end=10,
            confidence=0.9,
            source="entity.spacy_ORG",
        )
        org_b = _make_finding(
            Category.ORGANISATION,
            start=20,
            end=30,
            confidence=0.8,
            source="context.organisation",
        )

        result = Aggregator().aggregate(
            findings=[org_a, org_b],
            active_layers=["entity", "combination"],
        )

        assert org_a in result.findings
        assert org_b in result.findings
        assert len(result.findings) == 2
        # No metadata mutation when nothing was removed.
        assert all(f.metadata is None for f in result.findings)

    def test_cross_category_overlap_both_kept(self) -> None:
        """ADRESS + PLATS on overlapping span → both kept (scope guard)."""
        adress = _make_finding(
            Category.ADRESS,
            start=0,
            end=20,
            confidence=0.9,
            source="entity.spacy_LOC",
        )
        plats = _make_finding(
            Category.PLATS,
            start=5,
            end=20,
            confidence=0.85,
            source="context.plats",
        )

        result = Aggregator().aggregate(
            findings=[adress, plats],
            active_layers=["entity", "combination"],
        )

        assert adress in result.findings
        assert plats in result.findings
        assert len(result.findings) == 2

    def test_tiebreaker_stable_order_at_equal_confidence(self) -> None:
        """Equal confidence + overlapping span → first in input list kept."""
        first = _make_finding(
            Category.ORGANISATION,
            start=0,
            end=10,
            confidence=0.85,
            source="entity.spacy_ORG",
        )
        second = _make_finding(
            Category.ORGANISATION,
            start=0,
            end=10,
            confidence=0.85,
            source="context.organisation",
        )

        result = Aggregator().aggregate(
            findings=[first, second],
            active_layers=["entity", "combination"],
        )

        assert len(result.findings) == 1
        kept = result.findings[0]
        assert kept.source == "entity.spacy_ORG"
        assert kept.metadata is not None
        assert kept.metadata["deduplicated_sources"] == ["context.organisation"]

    def test_chain_overlap_all_pairwise_overlapping(self) -> None:
        """Three ORGANISATION findings, all pairwise overlapping → top kept."""
        a = _make_finding(
            Category.ORGANISATION,
            start=0,
            end=30,
            confidence=0.95,
            source="context.organisation",
        )
        b = _make_finding(
            Category.ORGANISATION,
            start=10,
            end=40,
            confidence=0.85,
            source="entity.spacy_ORG",
        )
        c = _make_finding(
            Category.ORGANISATION,
            start=20,
            end=50,
            confidence=0.80,
            source="entity.spacy_NORP",
        )

        result = Aggregator().aggregate(
            findings=[a, b, c],
            active_layers=["entity", "combination"],
        )

        assert len(result.findings) == 1
        kept = result.findings[0]
        assert kept.confidence == 0.95
        assert kept.source == "context.organisation"
        assert kept.metadata is not None
        assert set(kept.metadata["deduplicated_sources"]) == {
            "entity.spacy_ORG",
            "entity.spacy_NORP",
        }
        assert result.overlapping_findings == []

    def test_chain_overlap_transitive_without_AC_overlap(self) -> None:
        """A-B and B-C overlap but A-C disjoint → A and C kept; B removed.

        Algoritmen är pairwise: när A (högsta confidence) konsumerar B,
        bevaras C eftersom A-C inte överlappar. Detta dokumenterar
        semantiken explicit.
        """
        a = _make_finding(
            Category.ORGANISATION,
            start=0,
            end=15,
            confidence=0.95,
            source="context.organisation",
        )
        b = _make_finding(
            Category.ORGANISATION,
            start=10,
            end=30,
            confidence=0.85,
            source="entity.spacy_ORG",
        )
        c = _make_finding(
            Category.ORGANISATION,
            start=25,
            end=40,
            confidence=0.80,
            source="entity.spacy_NORP",
        )

        result = Aggregator().aggregate(
            findings=[a, b, c],
            active_layers=["entity", "combination"],
        )

        assert len(result.findings) == 2
        kept_sources = {f.source for f in result.findings}
        assert kept_sources == {"context.organisation", "entity.spacy_NORP"}

        kept_a = next(f for f in result.findings if f.source == "context.organisation")
        assert kept_a.metadata is not None
        assert kept_a.metadata["deduplicated_sources"] == ["entity.spacy_ORG"]

        kept_c = next(f for f in result.findings if f.source == "entity.spacy_NORP")
        assert kept_c.metadata is None

    def test_sensitivity_unchanged_by_dedup(self) -> None:
        """Dedup of context.organisation pair does not change sensitivity."""
        entity_org = _make_finding(
            Category.ORGANISATION,
            start=0,
            end=10,
            confidence=0.8,
            source="entity.spacy_ORG",
        )
        signal_org = _make_finding(
            Category.ORGANISATION,
            start=0,
            end=10,
            confidence=0.85,
            source="context.organisation",
        )

        result = Aggregator().aggregate(
            findings=[entity_org, signal_org],
            active_layers=["entity", "combination"],
        )

        # Without article9/article4/context.kombination, sensitivity stays NONE
        # both before and after dedup — kategori bevaras, antal fynd minskar.
        assert result.sensitivity == SensitivityLevel.NONE
        assert len(result.findings) == 1
