"""Unit tests for the Cross-Validating Aggregator evidence-weighting policy.

Verifies Issue I-7b implementation of arkitektur.md §9.6:

- §9.6.2 decision table R1–R7: per (lager, source) evidence_basis tagging
  in cross_validating mode.
- §9.6.3 Finding.evidence_basis + Classification.weakest_evidence_basis
  ("the weakest link in the classification").
- §9.6.4 cross_validation_mode with default "legacy" → unchanged behavior.
- §9.6.5 generalized Mekanism 3 via _count_structural_support.

Confirmed interpretation (user, 2026-05-16):
  1. In I-7b, cross_validating yields IDENTICAL identifiability/data_class/
     sensitivity as legacy; only evidence_basis tags and
     weakest_evidence_basis differ. The dimension/precision change lands
     with I-7c.
  2. weakest_evidence_basis is derived only over the findings that ACTUALLY
     bore the final dimension values (an article4 finding making DIRECT
     overrides — and excludes — an otherwise-validated context.kombination).

Fixtures that do not explicitly set cross_validation_mode use the
Aggregator() default ("legacy"), per the 2026-05-15 user decision.
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


def _f(
    category: Category,
    start: int,
    end: int,
    *,
    confidence: float = 1.0,
    source: str = "test",
) -> Finding:
    """Create a Finding with minimal boilerplate (mirrors the helper in
    test_aggregator_combination.py)."""
    return Finding(
        category=category,
        start=start,
        end=end,
        text_span="x" * (end - start),
        confidence=confidence,
        source=source,
    )


def _cv() -> Aggregator:
    return Aggregator(cross_validation_mode="cross_validating")


class TestDecisionTableTagging:
    """§9.6.2 R1–R7: evidence_basis tagging per (lager, source)."""

    def test_R1_pattern_no_support_required(self) -> None:
        """R1: a pattern.* finding is tagged no_support_required (self-
        validating, no support required)."""
        email = _f(Category.EMAIL, 0, 20, source="pattern.regex_email")

        result = _cv().aggregate([email], ["pattern"])

        assert result.findings[0].evidence_basis == "no_support_required"

    def test_R2_entity_prs_no_support_required(self) -> None:
        """R2: entity.spacy_PRS → article4.namn is tagged
        no_support_required (no support required)."""
        namn = _f(Category.NAMN, 0, 15, source="entity.spacy_PRS")

        result = _cv().aggregate([namn], ["entity"])

        assert result.findings[0].evidence_basis == "no_support_required"

    def test_R3_R4_entity_loc_org_as_support(self) -> None:
        """R3/R4: entity.spacy_LOC and entity.spacy_ORG are not tagged
        themselves (stay no_support_required) but count as structural
        support for an overlapping context.kombination via the entity.*
        prefix in the generalized Mekanism 3 (source-driven, works
        regardless of the I-7c category mapping)."""
        kombination = _f(
            Category.KOMBINATION, 0, 60,
            confidence=0.75,  # >= medium_threshold, < high_confidence_bypass
            source="context.kombination",
        )
        loc = _f(Category.PLATS, 0, 15, source="entity.spacy_LOC")
        org = _f(Category.ORGANISATION, 20, 50, source="entity.spacy_ORG")

        agg = _cv()
        findings = [kombination, loc, org]

        # LOC + ORG count as structural support for the kombination span.
        assert agg._count_structural_support(
            kombination, findings, ("pattern.", "entity."),
        ) == 2

        result = agg.aggregate(findings, ["entity", "combination"])

        komb = next(
            f for f in result.findings if f.source == "context.kombination"
        )
        assert komb.evidence_basis == "structural_support"
        # The LOC/ORG signals themselves are context signals, not triggers.
        for f in result.findings:
            if f.source in ("entity.spacy_LOC", "entity.spacy_ORG"):
                assert f.evidence_basis == "no_support_required"

    def test_R5_article9_no_support_required_no_threshold(self) -> None:
        """R5: an article9.* finding is tagged no_support_required even at
        confidence 0.0 — no support requirement and no bypass threshold
        (§9.6.2.1, recall-priority total, no recall regression vs legacy)."""
        halsodata = _f(
            Category.HALSODATA, 0, 10,
            confidence=0.0,
            source="article9.halsodata",
        )

        result = _cv().aggregate([halsodata], ["article9"])

        assert result.findings[0].evidence_basis == "no_support_required"
        # Still detected — no recall loss vs legacy.
        assert result.data_class == DataClass.SPECIAL

    def test_R6_structural_support(self) -> None:
        """R6: context.kombination with >= min_evidence_count overlapping
        pattern/entity support findings is tagged structural_support."""
        kombination = _f(
            Category.KOMBINATION, 0, 60,
            confidence=0.75,
            source="context.kombination",
        )
        org1 = _f(Category.ORGANISATION, 0, 15, source="entity.spacy_ORG")
        org2 = _f(Category.ORGANISATION, 20, 50, source="entity.spacy_ORG")

        result = _cv().aggregate(
            [kombination, org1, org2], ["entity", "combination"],
        )

        komb = next(
            f for f in result.findings if f.source == "context.kombination"
        )
        assert komb.evidence_basis == "structural_support"
        assert result.identifiability == Identifiability.INDIRECT
        assert result.weakest_evidence_basis == "structural_support"

    def test_R6_high_confidence_bypass(self) -> None:
        """R6: context.kombination without structural support but with
        confidence >= high_confidence_bypass (0.85) is tagged
        high_confidence_no_support (Beslut 21 fail-safe, now traceable)."""
        kombination = _f(
            Category.KOMBINATION, 0, 50,
            confidence=0.9,  # >= high_confidence_bypass 0.85
            source="context.kombination",
        )

        result = _cv().aggregate([kombination], ["combination"])

        assert result.findings[0].evidence_basis == "high_confidence_no_support"
        assert result.identifiability == Identifiability.INDIRECT
        assert result.weakest_evidence_basis == "high_confidence_no_support"

    def test_R6_no_support_no_bypass(self) -> None:
        """R6: context.kombination without structural support and below the
        bypass threshold keeps the default no_support_required and does not
        contribute to the dimension (unchanged _has_validated_kombination
        behavior)."""
        kombination = _f(
            Category.KOMBINATION, 0, 50,
            confidence=0.75,  # >= medium_threshold, < high_confidence_bypass
            source="context.kombination",
        )

        result = _cv().aggregate([kombination], ["combination"])

        assert result.findings[0].evidence_basis == "no_support_required"
        assert result.identifiability == Identifiability.NONE
        assert result.sensitivity == SensitivityLevel.NONE
        assert result.weakest_evidence_basis is None

    def test_R7_isolated_context_signals(self) -> None:
        """R7: an isolated context.yrke without a matching
        context.kombination does not elevate sensitivity (D5 preserved);
        it is kept in findings with default no_support_required."""
        yrke = _f(
            Category.YRKE, 0, 12,
            confidence=0.9,
            source="context.yrke",
        )

        result = _cv().aggregate([yrke], ["combination"])

        assert result.sensitivity == SensitivityLevel.NONE
        assert result.identifiability == Identifiability.NONE
        assert result.findings[0].evidence_basis == "no_support_required"
        assert result.weakest_evidence_basis is None


class TestLegacyParity:
    """§9.6.4: default legacy mode is byte-for-byte behavior-unchanged."""

    def test_legacy_mode_unchanged(self) -> None:
        """A representative fixture yields exactly the same
        (identifiability, data_class, sensitivity) as the pre-I-7b
        aggregator, weakest_evidence_basis is None, and all findings keep
        the default evidence_basis (the weighting pass is never called)."""
        # Fixture A: kombination via bypass (known legacy result:
        # INDIRECT + NONE → LOW).
        kombination = _f(
            Category.KOMBINATION, 0, 50,
            confidence=0.9,
            source="context.kombination",
        )
        result_a = Aggregator().aggregate([kombination], ["combination"])

        assert result_a.identifiability == Identifiability.INDIRECT
        assert result_a.data_class == DataClass.NONE
        assert result_a.sensitivity == SensitivityLevel.LOW
        assert result_a.weakest_evidence_basis is None
        assert all(
            f.evidence_basis == "no_support_required"
            for f in result_a.findings
        )

        # Fixture B: kombination validated via Mekanism 3 + article9
        # (known legacy result: INDIRECT + SPECIAL → MEDIUM).
        komb_b = _f(
            Category.KOMBINATION, 0, 60,
            confidence=0.75,
            source="context.kombination",
        )
        org1 = _f(Category.ORGANISATION, 0, 15, source="entity.spacy_ORG")
        org2 = _f(Category.ORGANISATION, 20, 50, source="entity.spacy_ORG")
        a9 = _f(Category.HALSODATA, 70, 80, source="article9.halsodata")
        result_b = Aggregator().aggregate(
            [komb_b, org1, org2, a9], ["entity", "article9", "combination"],
        )

        assert result_b.identifiability == Identifiability.INDIRECT
        assert result_b.data_class == DataClass.SPECIAL
        assert result_b.sensitivity == SensitivityLevel.MEDIUM
        assert result_b.weakest_evidence_basis is None
        assert all(
            f.evidence_basis == "no_support_required"
            for f in result_b.findings
        )


class TestWeakestEvidenceBasisDerivation:
    """§9.6.3: weakest_evidence_basis = the weakest link among the findings
    that actually bore the final dimension values."""

    def test_weakest_evidence_basis_derivation(self) -> None:
        """A Classification whose contributing findings include at least one
        high_confidence_no_support gets weakest_evidence_basis =
        high_confidence_no_support (rank 0 < structural_support <
        no_support_required)."""
        # Bypass-validated kombination (INDIRECT, high_confidence_no_support)
        # + article9 (SPECIAL, no_support_required). Both bear a final
        # dimension; the weakest link is the bypass kombination.
        kombination = _f(
            Category.KOMBINATION, 0, 50,
            confidence=0.9,  # bypass, no structural support
            source="context.kombination",
        )
        halsodata = _f(
            Category.HALSODATA, 60, 70,
            source="article9.halsodata",
        )

        result = _cv().aggregate(
            [kombination, halsodata], ["combination", "article9"],
        )

        assert result.identifiability == Identifiability.INDIRECT
        assert result.data_class == DataClass.SPECIAL
        assert result.weakest_evidence_basis == "high_confidence_no_support"

    def test_direct_overrides_excludes_kombination_from_weakest(self) -> None:
        """Confirmed interpretation 2: when an article4 finding makes
        identifiability DIRECT and overrides an otherwise-validated
        context.kombination, the overridden kombination is NOT counted
        toward weakest_evidence_basis — only the article4 finding (which
        actually bore DIRECT) is."""
        email = _f(Category.EMAIL, 70, 90, source="pattern.regex_email")
        kombination = _f(
            Category.KOMBINATION, 0, 50,
            confidence=0.9,  # would validate via bypass if not overridden
            source="context.kombination",
        )

        result = _cv().aggregate(
            [email, kombination], ["pattern", "combination"],
        )

        assert result.identifiability == Identifiability.DIRECT
        # Only the article4 email (no_support_required) bore DIRECT; the
        # bypass kombination (high_confidence_no_support) is excluded.
        assert result.weakest_evidence_basis == "no_support_required"


class TestI7cLocAsKombinationSupport:
    """Issue I-7c (arkitektur.md §5, §9.6.7 Degerfors-fallet): after the
    LOC → context.plats remapping, a LOC finding keeps its
    entity.spacy_LOC source and therefore still counts as structural
    support for an overlapping context.kombination via the entity.*
    prefix in the generalized Mekanism 3. The place signal moves from a
    spurious DIRECT trigger to its correct role as a puzzle piece that
    strengthens INDIRECT identifiability — it is not lost."""

    def test_loc_supports_kombination_via_mekanism_3(self) -> None:
        """Degerfors-like case in cross_validating mode: a medium-
        confidence context.kombination (>= medium_threshold, <
        high_confidence_bypass) is validated ONLY because the
        entity.spacy_LOC place finding (now Category.PLATS) counts as
        structural support alongside one more overlapping entity signal.
        The aggregator returns INDIRECT and the kombination's
        evidence_basis is structural_support."""
        kombination = _f(
            Category.KOMBINATION, 0, 60,
            confidence=0.75,  # >= medium_threshold 0.7, < bypass 0.85
            source="context.kombination",
        )
        # "Degerfors": post-I-7c this is Category.PLATS, source unchanged.
        plats = _f(
            Category.PLATS, 0, 15,
            source="entity.spacy_LOC",
        )
        org = _f(
            Category.ORGANISATION, 20, 50,
            source="entity.spacy_ORG",
        )

        agg = _cv()
        findings = [kombination, plats, org]

        # The LOC place finding is load-bearing: with ORG alone the
        # support count is 1 (< min_evidence_count); the entity.spacy_LOC
        # finding tips it to 2 and makes Mekanism 3 pass.
        assert agg._count_structural_support(
            kombination, [kombination, org], ("pattern.", "entity."),
        ) == 1
        assert agg._count_structural_support(
            kombination, findings, ("pattern.", "entity."),
        ) == 2

        result = agg.aggregate(findings, ["entity", "combination"])

        komb = next(
            f for f in result.findings
            if f.source == "context.kombination"
        )
        assert komb.evidence_basis == "structural_support"
        # No article4.* finding: place is INDIRECT support, not a DIRECT
        # trigger (the I-7c behavior change).
        assert result.identifiability == Identifiability.INDIRECT
        assert result.weakest_evidence_basis == "structural_support"
        # The place signal itself stays a context signal, not a trigger.
        plats_out = next(
            f for f in result.findings
            if f.source == "entity.spacy_LOC"
        )
        assert plats_out.category == Category.PLATS
        assert plats_out.evidence_basis == "no_support_required"


class TestI7eSourceAwareEvidenceCounting:
    """Issue I-7e (arkitektur.md §9.6.5, Loggbok it. 3, #138): i
    cross_validating-läget konsulterar _count_structural_support även
    finding.metadata["deduplicated_sources"], så ett stödfynd som
    _deduplicate_same_category_overlap tog bort vid
    same-category-källkollaps återupptäcks. Mode-gateat — legacy är
    oförändrat (alternativ iii). Fixturerna saknar article9 så
    _remove_context_covered_by_article9 inte fyrar, utom test_e som
    avsiktligt exercerar containment-vägen."""

    def test_a_dedup_kollision_via_propagerad_source(self) -> None:
        """(a) Två dedup-dödade entity-källor: context.plats absorberar
        entity.spacy_LOC, context.organisation absorberar
        entity.spacy_ORG. I cross_validating räknas båda via
        deduplicated_sources → count = 2 = min_evidence_count →
        kombinationen får structural_support och bär INDIRECT."""
        kombination = _f(
            Category.KOMBINATION, 0, 60,
            confidence=0.75,  # >= medium_threshold 0.7, < bypass 0.85
            source="context.kombination",
        )
        plats_llm = _f(
            Category.PLATS, 0, 15, confidence=0.98, source="context.plats",
        )
        plats_spacy = _f(
            Category.PLATS, 0, 15, confidence=0.80,
            source="entity.spacy_LOC",
        )
        org_llm = _f(
            Category.ORGANISATION, 20, 50, confidence=0.95,
            source="context.organisation",
        )
        org_spacy = _f(
            Category.ORGANISATION, 20, 50, confidence=0.80,
            source="entity.spacy_ORG",
        )

        result = _cv().aggregate(
            [kombination, plats_llm, plats_spacy, org_llm, org_spacy],
            ["entity", "combination"],
        )

        # Dedup behöll LLM-fynden (högre confidence) och propagerade de
        # borttagna entity-källorna till metadata.
        plats_out = next(
            f for f in result.findings if f.category == Category.PLATS
        )
        org_out = next(
            f for f in result.findings
            if f.category == Category.ORGANISATION
        )
        assert plats_out.source == "context.plats"
        assert plats_out.metadata["deduplicated_sources"] == [
            "entity.spacy_LOC"
        ]
        assert org_out.source == "context.organisation"
        assert org_out.metadata["deduplicated_sources"] == [
            "entity.spacy_ORG"
        ]

        komb = next(
            f for f in result.findings
            if f.source == "context.kombination"
        )
        assert komb.evidence_basis == "structural_support"
        assert result.identifiability == Identifiability.INDIRECT
        assert result.data_class == DataClass.NONE
        assert result.weakest_evidence_basis == "structural_support"

    def test_anna_lindstrom_article4_support_unchanged(self) -> None:
        """(b) Icke-kategorikrockande fall: stödfynden bär sina
        entity.*-source direkt (ingen dedup, ingen deduplicated_sources).
        Fixen är rent additiv — structural_support triggas via den
        oförändrade primärsource-grenen. Två direkta stöd krävs eftersom
        min_evidence_count = 2."""
        kombination = _f(
            Category.KOMBINATION, 0, 60, confidence=0.75,
            source="context.kombination",
        )
        # "Anna Lindström" → article4.namn, source entity.spacy_PRS.
        namn = _f(
            Category.NAMN, 0, 14, confidence=0.80,
            source="entity.spacy_PRS",
        )
        # Andra direkt entity-stödet (ingen context-tvilling → ingen
        # dedup); behövs för att nå min_evidence_count.
        plats = _f(
            Category.PLATS, 20, 35, confidence=0.80,
            source="entity.spacy_LOC",
        )

        result = _cv().aggregate(
            [kombination, namn, plats], ["entity", "combination"],
        )

        # Ingen dedup skedde → inget fynd bär deduplicated_sources.
        for f in result.findings:
            assert not (f.metadata or {}).get("deduplicated_sources")

        komb = next(
            f for f in result.findings
            if f.source == "context.kombination"
        )
        assert komb.evidence_basis == "structural_support"
        # article4.namn närvarande → DIRECT trumfar (oförändrad
        # dimensionslogik; structural_support kom via primärsource).
        assert result.identifiability == Identifiability.DIRECT

    def test_isolated_kombination_no_phantom_support(self) -> None:
        """(c) Endast en context.kombination utan stödsignaler. Fixen
        får inte trolla fram fantomstöd ur frånvarande/tom metadata:
        evidence_basis förblir no_support_required (varken
        structural_support eller bypass; conf < 0.85)."""
        kombination = _f(
            Category.KOMBINATION, 0, 50, confidence=0.75,
            source="context.kombination",
        )

        result = _cv().aggregate([kombination], ["combination"])

        assert result.findings[0].evidence_basis == "no_support_required"
        assert result.identifiability == Identifiability.NONE
        assert result.weakest_evidence_basis is None

    def test_d_legacy_mode_byte_identical_after_fix(self) -> None:
        """(d) Hela poängen med alternativ iii: fixtur identisk med
        test_a men kört i legacy. Mode-gaten gör att
        deduplicated_sources INTE konsulteras → _count_structural_support
        = 0 → _passes_mechanism_3 False → identifiability NONE.
        Byte-identiskt med pre-I-7e legacy (NONE/NONE/NONE) och alla fynd
        behåller default evidence_basis (weighting-passet ej anropat)."""
        kombination = _f(
            Category.KOMBINATION, 0, 60, confidence=0.75,
            source="context.kombination",
        )
        plats_llm = _f(
            Category.PLATS, 0, 15, confidence=0.98, source="context.plats",
        )
        plats_spacy = _f(
            Category.PLATS, 0, 15, confidence=0.80,
            source="entity.spacy_LOC",
        )
        org_llm = _f(
            Category.ORGANISATION, 20, 50, confidence=0.95,
            source="context.organisation",
        )
        org_spacy = _f(
            Category.ORGANISATION, 20, 50, confidence=0.80,
            source="entity.spacy_ORG",
        )

        result = Aggregator().aggregate(
            [kombination, plats_llm, plats_spacy, org_llm, org_spacy],
            ["entity", "combination"],
        )

        assert result.identifiability == Identifiability.NONE
        assert result.data_class == DataClass.NONE
        assert result.sensitivity == SensitivityLevel.NONE
        assert result.weakest_evidence_basis is None
        assert all(
            f.evidence_basis == "no_support_required"
            for f in result.findings
        )

    def test_e_containment_does_not_propagate_source(self) -> None:
        """(e) Regression-tripwire: en entity.spacy_ORG som tas bort av
        _remove_context_covered_by_article9-containment propagerar INTE
        sin source (till skillnad från dedup). A'-fixen kan därför inte
        rädda den — kombinationen får INTE structural_support. Fryser den
        parallella, oadresserade containment-kollaps-vägen; om containment
        någon gång börjar propagera source ska detta test medvetet
        brytas."""
        kombination = _f(
            Category.KOMBINATION, 0, 70, confidence=0.75,
            source="context.kombination",
        )
        a9 = _f(
            Category.POLITISK_ASIKT, 40, 70, confidence=0.98,
            source="article9.politisk_asikt",
        )
        # context.organisation (50,65) täcks helt av article9 (40,70) →
        # _remove_context_covered_by_article9 tar bort den UTAN att
        # propagera source.
        org_spacy = _f(
            Category.ORGANISATION, 50, 65, confidence=0.80,
            source="entity.spacy_ORG",
        )

        result = _cv().aggregate(
            [kombination, a9, org_spacy],
            ["entity", "article9", "combination"],
        )

        # Containment droppade org-fyndet spårlöst.
        assert all(
            f.source != "entity.spacy_ORG" for f in result.findings
        )
        for f in result.findings:
            assert "entity.spacy_ORG" not in (
                (f.metadata or {}).get("deduplicated_sources", [])
            )
        komb = next(
            f for f in result.findings
            if f.source == "context.kombination"
        )
        # Fixen räddar INTE en containment-kollapsad källa.
        assert komb.evidence_basis == "no_support_required"
        assert result.identifiability == Identifiability.NONE
        assert result.data_class == DataClass.SPECIAL  # article9 kvar
