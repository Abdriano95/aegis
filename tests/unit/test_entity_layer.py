"""Unit tests for EntityLayer's SpaCy label mapping.

Covers Issue I-7c (arkitektur.md §5, §9.6.6, §9.6.7): SpaCy's ``LOC``
label maps to ``Category.PLATS`` (``context.plats``), not the former
``Category.ADRESS`` (``article4.adress``). The ``entity.spacy_LOC``
source tag is intentionally preserved so the generalized Mekanism 3
keeps counting LOC findings as structural support via the ``entity.*``
prefix (verified at the aggregator level in
test_aggregator_evidence_weighting.py).

The real ``sv_core_news_lg`` model is loaded once at module import
(same dependency as tests/integration/test_end_to_end.py). The
structural ``_label_map`` assertion is the deterministic backstop;
the detect() test additionally exercises the mapping end-to-end on a
sentence where ``sv_core_news_lg`` reliably tags a city as ``LOC``.
"""

from __future__ import annotations

from gdpr_classifier.core import Category
from gdpr_classifier.layers.entity import EntityLayer

# Load the SpaCy model once for the whole module (model load is the
# dominant cost; the mapping under test is constructed in __init__).
_LAYER = EntityLayer()


def test_label_map_loc_maps_to_context_plats() -> None:
    """Structural backstop: LOC is mapped to Category.PLATS with the
    preserved entity.spacy_LOC source tag. Robust against SpaCy NER
    variation since it inspects the mapping directly."""
    assert _LAYER._label_map["LOC"] == (Category.PLATS, "entity.spacy_LOC")
    # I-7c does not touch PRS/ORG.
    assert _LAYER._label_map["PRS"] == (Category.NAMN, "entity.spacy_PRS")
    assert _LAYER._label_map["ORG"] == (
        Category.ORGANISATION,
        "entity.spacy_ORG",
    )


def test_loc_maps_to_context_plats() -> None:
    """End-to-end: a city name produces a Category.PLATS finding with
    source entity.spacy_LOC, never Category.ADRESS (the pre-I-7c
    mapping)."""
    findings = _LAYER.detect("Jag bor i Göteborg")

    plats_findings = [
        f for f in findings if f.category == Category.PLATS
    ]
    assert plats_findings, (
        f"Expected a Category.PLATS finding for the city name; "
        f"got {[(f.category, f.text_span, f.source) for f in findings]}"
    )
    assert all(f.source == "entity.spacy_LOC" for f in plats_findings)
    # The pre-I-7c article4.adress mapping must no longer occur.
    assert all(f.category != Category.ADRESS for f in findings)
