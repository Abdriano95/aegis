"""Uttömmande tester för derive_sensitivity.

Verifierar att den rena derivatfunktionen producerar förväntad
SensitivityLevel för alla 9 (identifiability, data_class)-kombinationer
enligt härledningstabellen i SSOT §8. Förankrat i Beslut 37 och Beslut 49
reviderad (kategorisk modell: Identifiability NONE/INDIRECT/DIRECT,
DataClass NONE/SPECIAL/CRIMINAL, sensitivity som UI-abstraktion).
"""

from __future__ import annotations

from gdpr_classifier.aggregator import derive_sensitivity
from gdpr_classifier.core import DataClass, Identifiability, SensitivityLevel


class TestDeriveSensitivityCellMapping:
    """Verifierar derive_sensitivity för alla 9 celler i härledningstabellen."""

    def test_none_none(self) -> None:
        assert (
            derive_sensitivity(Identifiability.NONE, DataClass.NONE)
            == SensitivityLevel.NONE
        )

    def test_none_special(self) -> None:
        assert (
            derive_sensitivity(Identifiability.NONE, DataClass.SPECIAL)
            == SensitivityLevel.LOW
        )

    def test_none_criminal(self) -> None:
        assert (
            derive_sensitivity(Identifiability.NONE, DataClass.CRIMINAL)
            == SensitivityLevel.LOW
        )

    def test_indirect_none(self) -> None:
        assert (
            derive_sensitivity(Identifiability.INDIRECT, DataClass.NONE)
            == SensitivityLevel.LOW
        )

    def test_indirect_special(self) -> None:
        assert (
            derive_sensitivity(Identifiability.INDIRECT, DataClass.SPECIAL)
            == SensitivityLevel.MEDIUM
        )

    def test_indirect_criminal(self) -> None:
        assert (
            derive_sensitivity(Identifiability.INDIRECT, DataClass.CRIMINAL)
            == SensitivityLevel.MEDIUM
        )

    def test_direct_none(self) -> None:
        assert (
            derive_sensitivity(Identifiability.DIRECT, DataClass.NONE)
            == SensitivityLevel.LOW
        )

    def test_direct_special(self) -> None:
        assert (
            derive_sensitivity(Identifiability.DIRECT, DataClass.SPECIAL)
            == SensitivityLevel.HIGH
        )

    def test_direct_criminal(self) -> None:
        assert (
            derive_sensitivity(Identifiability.DIRECT, DataClass.CRIMINAL)
            == SensitivityLevel.HIGH
        )
