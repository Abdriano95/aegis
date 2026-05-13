"""Unit tests for dimension enums and Classification extension (I-5 Del 1).

Verifies that the new enums Identifiability and DataClass have the correct
shape (values, ordering, str inheritance, public export), and that
Classification remains frozen, is backwards-compatibly constructible with
defaults, and equality-compares across the new fields. Anchored in Beslut 37
(tvådimensionsoperationalisering enligt Variant 2).
"""

from __future__ import annotations

import dataclasses

import pytest

from gdpr_classifier.core import (
    Classification,
    DataClass,
    Identifiability,
    SensitivityLevel,
)
from gdpr_classifier.core import classification as classification_module


def _make_minimal_classification(
    *,
    sensitivity: SensitivityLevel = SensitivityLevel.NONE,
    identifiability: Identifiability | None = None,
    data_class: DataClass | None = None,
) -> Classification:
    """Construct a Classification with empty lists, allowing dimension overrides."""
    kwargs: dict = {
        "findings": [],
        "sensitivity": sensitivity,
        "active_layers": [],
        "overlapping_findings": [],
    }
    if identifiability is not None:
        kwargs["identifiability"] = identifiability
    if data_class is not None:
        kwargs["data_class"] = data_class
    return Classification(**kwargs)


class TestDimensionEnums:
    """Shape and import-path properties of Identifiability and DataClass."""

    def test_identifiability_values_and_order(self) -> None:
        """Identifiability has exactly four members in NONE/LOW/MEDIUM/HIGH order with lower-case values."""
        members = list(Identifiability)
        assert members == [
            Identifiability.NONE,
            Identifiability.LOW,
            Identifiability.MEDIUM,
            Identifiability.HIGH,
        ]
        assert Identifiability.NONE.value == "none"
        assert Identifiability.LOW.value == "low"
        assert Identifiability.MEDIUM.value == "medium"
        assert Identifiability.HIGH.value == "high"

    def test_data_class_values_and_order(self) -> None:
        """DataClass has exactly four members in NONE/ORDINARY/SPECIAL/CRIMINAL order with lower-case values."""
        members = list(DataClass)
        assert members == [
            DataClass.NONE,
            DataClass.ORDINARY,
            DataClass.SPECIAL,
            DataClass.CRIMINAL,
        ]
        assert DataClass.NONE.value == "none"
        assert DataClass.ORDINARY.value == "ordinary"
        assert DataClass.SPECIAL.value == "special"
        assert DataClass.CRIMINAL.value == "criminal"

    def test_identifiability_inherits_str(self) -> None:
        """Identifiability members are also str instances (mirrors SensitivityLevel pattern)."""
        for member in Identifiability:
            assert isinstance(member, str)

    def test_data_class_inherits_str(self) -> None:
        """DataClass members are also str instances (mirrors SensitivityLevel pattern)."""
        for member in DataClass:
            assert isinstance(member, str)

    def test_dual_import_paths_identifiability(self) -> None:
        """Identifiability is importable from gdpr_classifier.core and gdpr_classifier.core.classification (same object)."""
        assert Identifiability is classification_module.Identifiability

    def test_dual_import_paths_data_class(self) -> None:
        """DataClass is importable from gdpr_classifier.core and gdpr_classifier.core.classification (same object)."""
        assert DataClass is classification_module.DataClass


class TestClassificationWithDimensions:
    """Classification dataclass extended with identifiability and data_class fields."""

    def test_defaults_none_none_backwards_compatible(self) -> None:
        """Constructing Classification without the new fields yields Identifiability.NONE and DataClass.NONE."""
        result = Classification(
            findings=[],
            sensitivity=SensitivityLevel.NONE,
            active_layers=[],
            overlapping_findings=[],
        )
        assert result.identifiability == Identifiability.NONE
        assert result.data_class == DataClass.NONE
        assert result.mechanism_used is None

    def test_explicit_construction_preserves_values(self) -> None:
        """Explicit identifiability and data_class arguments are preserved on the instance."""
        result = Classification(
            findings=[],
            sensitivity=SensitivityLevel.MEDIUM,
            active_layers=["pattern", "combination"],
            overlapping_findings=[],
            mechanism_used="mechanism3",
            identifiability=Identifiability.MEDIUM,
            data_class=DataClass.ORDINARY,
        )
        assert result.sensitivity == SensitivityLevel.MEDIUM
        assert result.identifiability == Identifiability.MEDIUM
        assert result.data_class == DataClass.ORDINARY
        assert result.mechanism_used == "mechanism3"

    def test_frozen_dataclass_blocks_mutation(self) -> None:
        """Assigning to identifiability on an existing instance raises FrozenInstanceError."""
        instance = _make_minimal_classification()
        with pytest.raises(dataclasses.FrozenInstanceError):
            instance.identifiability = Identifiability.HIGH  # type: ignore[misc]

    def test_equality_includes_new_fields(self) -> None:
        """Two Classifications differing only on identifiability are not equal."""
        a = _make_minimal_classification(identifiability=Identifiability.LOW)
        b = _make_minimal_classification(identifiability=Identifiability.MEDIUM)
        assert a != b

    def test_equality_includes_data_class(self) -> None:
        """Two Classifications differing only on data_class are not equal."""
        a = _make_minimal_classification(data_class=DataClass.ORDINARY)
        b = _make_minimal_classification(data_class=DataClass.SPECIAL)
        assert a != b
