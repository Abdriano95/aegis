"""Unit tests for matcher."""

from __future__ import annotations

from gdpr_classifier.core.category import Category
from gdpr_classifier.core.finding import Finding
from evaluation.dataset.labeled_finding import LabeledFinding
from evaluation.matcher import _are_aliased, match


def test_match_exact():
    """Test standard exact match on category and position."""
    e1 = LabeledFinding(category=Category.PERSONNUMMER, start=10, end=20, text_span="850101-1234")
    p1 = Finding(category=Category.PERSONNUMMER, start=10, end=20, text_span="850101-1234", confidence=1.0, source="test")
    
    result = match([p1], [e1])
    
    assert len(result.true_positives) == 1
    assert result.true_positives[0] == (p1, e1)
    assert len(result.false_positives) == 0
    assert len(result.false_negatives) == 0


def test_match_partial_overlap():
    """Test that overlapping spans match even if start/end are not identical."""
    e1 = LabeledFinding(category=Category.EMAIL, start=10, end=30, text_span="anna.svensson@mail.se")
    p1 = Finding(category=Category.EMAIL, start=12, end=28, text_span="na.svensson@mail", confidence=0.9, source="test")
    
    result = match([p1], [e1])
    
    assert len(result.true_positives) == 1
    assert len(result.false_positives) == 0
    assert len(result.false_negatives) == 0


def test_no_overlap():
    """Test no overlap resulting in 1 FP, 1 FN."""
    e1 = LabeledFinding(category=Category.TELEFONNUMMER, start=5, end=15, text_span="070-1234567")
    p1 = Finding(category=Category.TELEFONNUMMER, start=20, end=30, text_span="070-7654321", confidence=0.9, source="test")
    
    result = match([p1], [e1])
    
    assert len(result.true_positives) == 0
    assert len(result.false_positives) == 1
    assert result.false_positives[0] == p1
    assert len(result.false_negatives) == 1
    assert result.false_negatives[0] == e1


def test_category_mismatch():
    """Test identical spans with different categories fail to match."""
    e1 = LabeledFinding(category=Category.EMAIL, start=10, end=20, text_span="anna@t.se")
    p1 = Finding(category=Category.NAMN, start=10, end=20, text_span="anna@t.se", confidence=0.9, source="test")
    
    result = match([p1], [e1])
    
    assert len(result.true_positives) == 0
    assert len(result.false_positives) == 1
    assert len(result.false_negatives) == 1


def test_duplicate_coverage_highest_confidence_wins():
    """Test that two predictions overlapping the same target resolves to highest confidence."""
    e1 = LabeledFinding(category=Category.IBAN, start=10, end=30, text_span="SE1234567890")
    
    # Both predictions have same category and overlap
    p_low = Finding(category=Category.IBAN, start=8, end=25, text_span="12345", confidence=0.5, source="low")
    p_high = Finding(category=Category.IBAN, start=12, end=32, text_span="67890", confidence=0.9, source="high")
    
    result = match([p_low, p_high], [e1])
    
    # Highest confidence wins the claim
    assert len(result.true_positives) == 1
    assert result.true_positives[0][0] == p_high
    assert result.true_positives[0][1] == e1
    
    # Lower confidence falls through
    assert len(result.false_positives) == 1
    assert result.false_positives[0] == p_low
    assert len(result.false_negatives) == 0


def test_multiple_expecteds_handled_correctly():
    """Test multiple predictions and expected findings resolving correctly."""
    e1 = LabeledFinding(category=Category.PERSONNUMMER, start=0, end=5, text_span="e1")
    e2 = LabeledFinding(category=Category.PERSONNUMMER, start=10, end=15, text_span="e2")

    p1 = Finding(category=Category.PERSONNUMMER, start=0, end=5, text_span="p1", confidence=1.0, source="")
    p2 = Finding(category=Category.PERSONNUMMER, start=10, end=15, text_span="p2", confidence=0.8, source="")

    result = match([p1, p2], [e1, e2])

    assert len(result.true_positives) == 2
    assert len(result.false_positives) == 0
    assert len(result.false_negatives) == 0


def test_alias_adress_pred_vs_plats_expected():
    """Predikterad ADRESS mot förväntad PLATS med överlappande spans → 1 TP."""
    e1 = LabeledFinding(category=Category.PLATS, start=10, end=15, text_span="Malmö")
    p1 = Finding(category=Category.ADRESS, start=10, end=15, text_span="Malmö", confidence=0.9, source="entity.spacy_LOC")

    result = match([p1], [e1])

    assert len(result.true_positives) == 1
    assert result.true_positives[0] == (p1, e1)
    assert result.true_positives[0][1].category == Category.PLATS
    assert len(result.false_positives) == 0
    assert len(result.false_negatives) == 0


def test_alias_plats_pred_vs_adress_expected():
    """Predikterad PLATS mot förväntad ADRESS (omvänd riktning) → 1 TP."""
    e1 = LabeledFinding(category=Category.ADRESS, start=20, end=27, text_span="Storgatan")
    p1 = Finding(category=Category.PLATS, start=20, end=27, text_span="Storgatan", confidence=0.85, source="context.kombination")

    result = match([p1], [e1])

    assert len(result.true_positives) == 1
    assert result.true_positives[0] == (p1, e1)
    assert result.true_positives[0][1].category == Category.ADRESS
    assert len(result.false_positives) == 0
    assert len(result.false_negatives) == 0


def test_exact_match_priority_over_alias():
    """Exakt kategori-match vinner över alias-match — ordningskänsligt-säkert."""
    p1 = Finding(category=Category.ADRESS, start=10, end=20, text_span="Drottninggatan", confidence=0.9, source="entity.spacy_LOC")

    # Kör med båda orderingar av expected för att garantera att Pass 1 scannar
    # hela listan innan Pass 2 ens övervägs.
    for expected_order in (
        [
            LabeledFinding(category=Category.ADRESS, start=10, end=20, text_span="Drottninggatan"),
            LabeledFinding(category=Category.PLATS, start=10, end=20, text_span="Drottninggatan"),
        ],
        [
            LabeledFinding(category=Category.PLATS, start=10, end=20, text_span="Drottninggatan"),
            LabeledFinding(category=Category.ADRESS, start=10, end=20, text_span="Drottninggatan"),
        ],
    ):
        result = match([p1], expected_order)

        assert len(result.true_positives) == 1
        assert result.true_positives[0][0] == p1
        assert result.true_positives[0][1].category == Category.ADRESS
        # Alias-expected ska bli FN eftersom det inte matchas av p1
        assert len(result.false_positives) == 0
        assert len(result.false_negatives) == 1
        assert result.false_negatives[0].category == Category.PLATS


def test_no_alias_for_unrelated_categories():
    """Predikterad ADRESS mot förväntad NAMN (inte alias-par) → FP+FN."""
    e1 = LabeledFinding(category=Category.NAMN, start=10, end=20, text_span="Anna Svensson")
    p1 = Finding(category=Category.ADRESS, start=10, end=20, text_span="Anna Svensson", confidence=0.9, source="entity.spacy_LOC")

    result = match([p1], [e1])

    assert len(result.true_positives) == 0
    assert len(result.false_positives) == 1
    assert result.false_positives[0] == p1
    assert len(result.false_negatives) == 1
    assert result.false_negatives[0] == e1


def test_are_aliased_symmetry():
    """_are_aliased är symmetrisk, returnerar False för obesläktade och för self-aliasing."""
    assert _are_aliased(Category.ADRESS, Category.PLATS) is True
    assert _are_aliased(Category.PLATS, Category.ADRESS) is True
    assert _are_aliased(Category.ADRESS, Category.NAMN) is False
    assert _are_aliased(Category.NAMN, Category.ADRESS) is False
    # Self-aliasing returnerar False (exakt-fall hanteras i Pass 1)
    assert _are_aliased(Category.ADRESS, Category.ADRESS) is False
    assert _are_aliased(Category.PLATS, Category.PLATS) is False


def test_alias_match_does_not_steal_from_exact():
    """Confidence-edge-case: hög-conf P1 alias-matchar, lägre-conf P2 exakt-matchar — båda blir TP."""
    e_addr = LabeledFinding(category=Category.ADRESS, start=0, end=10, text_span="Storgatan")
    e_plats = LabeledFinding(category=Category.PLATS, start=20, end=30, text_span="Stockholm")

    # P1 (hög conf, ADRESS) överlappar bara e_plats — måste alias-matcha
    p1_high = Finding(category=Category.ADRESS, start=20, end=30, text_span="Stockholm", confidence=0.95, source="entity.spacy_LOC")
    # P2 (lägre conf, ADRESS) överlappar bara e_addr — måste exakt-matcha
    p2_low = Finding(category=Category.ADRESS, start=0, end=10, text_span="Storgatan", confidence=0.6, source="entity.spacy_LOC")

    result = match([p1_high, p2_low], [e_addr, e_plats])

    assert len(result.true_positives) == 2
    assert len(result.false_positives) == 0
    assert len(result.false_negatives) == 0

    # Verifiera att rätt par bildades
    pairs = {(tp[0], tp[1]) for tp in result.true_positives}
    assert (p1_high, e_plats) in pairs
    assert (p2_low, e_addr) in pairs
