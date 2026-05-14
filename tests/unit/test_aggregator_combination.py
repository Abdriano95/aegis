"""Unit tests for Aggregator combination logic and D5-correction.

Tests verify Aggregator.aggregate() with kombinationslogik (sensitivity via
_determine_dimensions + derive_sensitivity per Beslut 49 reviderad):
  a) article9.* + article4.* findings → HIGH (DIRECT + SPECIAL)
  b) article9.* alone (no identifiable person) → LOW (NONE + SPECIAL)
  c) context.kombination via bypass without article4 → LOW (INDIRECT + NONE)
  d) context.kombination via Mekanism 3 without article4 → LOW (INDIRECT + NONE)
  e) context.kombination + insufficient evidence + article4 → LOW (DIRECT + NONE)
  f) Isolated context.* findings (D5-correction) do not elevate sensitivity
  g) article4.* alone → LOW (DIRECT + NONE)
  h) No findings → NONE

TestDetermineDimensionsOutputs verifies that identifiability and data_class
fields on Classification populate consistently across all scenario variants
(article9 alone, article9 + article4, bypass, mechanism3, article4 alone,
article4 + kombination, empty).
"""

from __future__ import annotations

from gdpr_classifier.aggregator import Aggregator
from gdpr_classifier.core import (
    Category,
    DataClass,
    Finding,
    Identifiability,
    SensitivityLevel,
)


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

    def test_article9_with_article4_gives_high(self) -> None:
        """article9 + article4 → DIRECT + SPECIAL → HIGH."""
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

    def test_article9_alone_gives_low(self) -> None:
        """article9 utan identifierbar person → NONE + SPECIAL → LOW.

        Reviderad förväntan (Beslut 49 reviderad): utan identifierbarhet
        finns ingen personuppgift att skydda. Anonym text om känsliga
        kategorier ger LOW i nya kategoriska modellen.
        """
        halsodata = _make_finding(
            Category.HALSODATA,
            start=0,
            end=10,
            source="article9.halsodata",
        )

        result = Aggregator().aggregate(
            findings=[halsodata],
            active_layers=["article9"],
        )

        assert result.sensitivity == SensitivityLevel.LOW

    def test_kombination_high_confidence_bypass_gives_low(self) -> None:
        """context.kombination bypass utan article9 → INDIRECT + NONE → LOW.

        Reviderad förväntan (Beslut 49 reviderad): validerad kombination
        utan känsligt material ger INDIRECT identifierbarhet, men eftersom
        data_class är NONE blir sensitivity LOW (inte längre MEDIUM).
        """
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

        assert result.sensitivity == SensitivityLevel.LOW

    def test_kombination_mekanism3_sufficient_evidence_gives_low(self) -> None:
        """context.kombination Mekanism 3 utan article9 → INDIRECT + NONE → LOW.

        Reviderad förväntan (Beslut 49 reviderad): Mekanism 3 validerar
        identifierbarhet (INDIRECT) men utan article9 är data_class NONE
        och därmed sensitivity LOW. Notera att evidensfynden (pattern.email,
        entity.spacy_PRS) bidrar med article4 → identifiability DIRECT
        vilket vinner över INDIRECT, men sensitivity-utfallet är fortfarande
        LOW eftersom data_class=NONE.
        """
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

        assert result.sensitivity == SensitivityLevel.LOW

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
        # article4 finding outside kombination span — no overlap, counts toward DIRECT
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
        """article4.* finding without any kombination gives LOW (DIRECT + NONE)."""
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

    def test_high_trumps_indirect_when_article9_and_article4_present(self) -> None:
        """article9.* + article4.* + kombination → HIGH (DIRECT vinner, SPECIAL kvarstår)."""
        halsodata = _make_finding(
            Category.HALSODATA,
            start=0,
            end=10,
            source="article9.halsodata",
        )
        email = _make_finding(
            Category.EMAIL,
            start=15,
            end=35,
            source="pattern.regex_email",
        )
        kombination = _make_finding(
            Category.KOMBINATION,
            start=0,
            end=50,
            confidence=0.9,
            source="context.kombination",
        )

        result = Aggregator().aggregate(
            findings=[halsodata, email, kombination],
            active_layers=["article9", "pattern", "combination"],
        )

        assert result.sensitivity == SensitivityLevel.HIGH

    def test_isolated_context_with_article4_gives_low(self) -> None:
        """D5-correction: context.organisation + article4 gives LOW (DIRECT + NONE).

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


class TestDetermineDimensionsOutputs:
    """Identifiability och data_class populeras korrekt för varje scenario.

    Verifierar tvådimensionsoperationaliseringen (Beslut 37, Beslut 49 reviderad)
    populerar Classification.identifiability och Classification.data_class
    konsistent. Klassifikationen kommuniceras helt av paret — mechanism_used
    är borttaget från modellen.
    """

    def test_article9_alone_yields_none_identifiability_special_data(self) -> None:
        """article9 isolerat → identifiability=NONE, data_class=SPECIAL, sensitivity=LOW."""
        halsodata = _make_finding(
            Category.HALSODATA,
            start=0,
            end=10,
            source="article9.halsodata",
        )

        result = Aggregator().aggregate(
            findings=[halsodata],
            active_layers=["article9"],
        )

        assert result.identifiability == Identifiability.NONE
        assert result.data_class == DataClass.SPECIAL
        assert result.sensitivity == SensitivityLevel.LOW

    def test_article9_with_article4_yields_direct_identifiability_special_data(self) -> None:
        """article9 + article4 → identifiability=DIRECT, data_class=SPECIAL, sensitivity=HIGH."""
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

        assert result.identifiability == Identifiability.DIRECT
        assert result.data_class == DataClass.SPECIAL
        assert result.sensitivity == SensitivityLevel.HIGH

    def test_bypass_alone_yields_indirect_identifiability_none_data(self) -> None:
        """bypass-passerad kombination utan article4/article9 → INDIRECT + NONE → LOW."""
        kombination = _make_finding(
            Category.KOMBINATION,
            start=0,
            end=50,
            confidence=0.9,
            source="context.kombination",
        )

        result = Aggregator().aggregate(
            findings=[kombination],
            active_layers=["combination"],
        )

        assert result.identifiability == Identifiability.INDIRECT
        assert result.data_class == DataClass.NONE
        assert result.sensitivity == SensitivityLevel.LOW

    def test_mechanism3_alone_yields_indirect_identifiability_none_data(self) -> None:
        """Mekanism 3-passerad kombination utan article4/article9 → INDIRECT + NONE → LOW.

        Använder två context.organisation-fynd som evidence (source=entity.*
        räknas av Mekanism 3, category context.organisation triggar inte
        has_article4 eftersom prefix är context. inte article4.).
        """
        kombination = _make_finding(
            Category.KOMBINATION,
            start=0,
            end=60,
            confidence=0.75,
            source="context.kombination",
        )
        org1 = _make_finding(
            Category.ORGANISATION,
            start=0,
            end=15,
            source="entity.spacy_ORG",
        )
        org2 = _make_finding(
            Category.ORGANISATION,
            start=20,
            end=50,
            source="entity.spacy_ORG",
        )

        result = Aggregator().aggregate(
            findings=[kombination, org1, org2],
            active_layers=["entity", "combination"],
        )

        assert result.identifiability == Identifiability.INDIRECT
        assert result.data_class == DataClass.NONE
        assert result.sensitivity == SensitivityLevel.LOW

    def test_article4_alone_yields_direct_identifiability_none_data(self) -> None:
        """article4 isolerat → identifiability=DIRECT, data_class=NONE, sensitivity=LOW."""
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

        assert result.identifiability == Identifiability.DIRECT
        assert result.data_class == DataClass.NONE
        assert result.sensitivity == SensitivityLevel.LOW

    def test_article4_with_kombination_yields_direct_identifiability_none_data(self) -> None:
        """article4 + bypass-kombination → DIRECT vinner över INDIRECT, NONE data, LOW."""
        email = _make_finding(
            Category.EMAIL,
            start=70,
            end=90,
            source="pattern.regex_email",
        )
        kombination = _make_finding(
            Category.KOMBINATION,
            start=0,
            end=50,
            confidence=0.9,
            source="context.kombination",
        )

        result = Aggregator().aggregate(
            findings=[email, kombination],
            active_layers=["pattern", "combination"],
        )

        assert result.identifiability == Identifiability.DIRECT
        assert result.data_class == DataClass.NONE
        assert result.sensitivity == SensitivityLevel.LOW

    def test_no_findings_yields_none(self) -> None:
        """Inga fynd → identifiability=NONE, data_class=NONE, sensitivity=NONE."""
        result = Aggregator().aggregate(
            findings=[],
            active_layers=["pattern"],
        )

        assert result.identifiability == Identifiability.NONE
        assert result.data_class == DataClass.NONE
        assert result.sensitivity == SensitivityLevel.NONE
