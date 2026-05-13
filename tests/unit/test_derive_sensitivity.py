"""Uttömmande tester för derive_sensitivity (I-5 Del 2).

Verifierar att den rena derivatfunktionen producerar förväntad
SensitivityLevel för alla 16 (identifiability, data_class)-kombinationer
enligt härledningstabellen i SSOT §8. Förankrat i Beslut 37 och Beslut 49.
"""

from __future__ import annotations

import pytest

from gdpr_classifier.aggregator import derive_sensitivity
from gdpr_classifier.core import DataClass, Identifiability, SensitivityLevel


class TestDeriveSensitivitySpecial:
    """SPECIAL-data_class ger HIGH oavsett identifiability."""

    @pytest.mark.parametrize("ident", list(Identifiability))
    def test_special_gives_high(self, ident: Identifiability) -> None:
        assert derive_sensitivity(ident, DataClass.SPECIAL) == SensitivityLevel.HIGH


class TestDeriveSensitivityCriminal:
    """CRIMINAL-data_class ger HIGH oavsett identifiability (passiv i v0.3.0)."""

    @pytest.mark.parametrize("ident", list(Identifiability))
    def test_criminal_gives_high(self, ident: Identifiability) -> None:
        assert derive_sensitivity(ident, DataClass.CRIMINAL) == SensitivityLevel.HIGH


class TestDeriveSensitivityOrdinary:
    """ORDINARY-data_class mappar via identifiability."""

    def test_none_ordinary_gives_low_failsafe(self) -> None:
        # (NONE, ORDINARY) är icke-producerbar; Beslut 21 fail-safe → LOW.
        assert (
            derive_sensitivity(Identifiability.NONE, DataClass.ORDINARY)
            == SensitivityLevel.LOW
        )

    def test_low_ordinary_gives_low(self) -> None:
        assert (
            derive_sensitivity(Identifiability.LOW, DataClass.ORDINARY)
            == SensitivityLevel.LOW
        )

    def test_medium_ordinary_gives_medium(self) -> None:
        assert (
            derive_sensitivity(Identifiability.MEDIUM, DataClass.ORDINARY)
            == SensitivityLevel.MEDIUM
        )

    def test_high_ordinary_gives_medium(self) -> None:
        assert (
            derive_sensitivity(Identifiability.HIGH, DataClass.ORDINARY)
            == SensitivityLevel.MEDIUM
        )


class TestDeriveSensitivityNoneDataClass:
    """data_class.NONE: bara (NONE, NONE) ger NONE; övriga är fail-safe LOW."""

    def test_none_none_gives_none(self) -> None:
        assert (
            derive_sensitivity(Identifiability.NONE, DataClass.NONE)
            == SensitivityLevel.NONE
        )

    def test_low_none_gives_low_failsafe(self) -> None:
        # Beslut 21 Privacy by Design fail-safe — icke-producerbar kombination.
        assert (
            derive_sensitivity(Identifiability.LOW, DataClass.NONE)
            == SensitivityLevel.LOW
        )

    def test_medium_none_gives_low_failsafe(self) -> None:
        assert (
            derive_sensitivity(Identifiability.MEDIUM, DataClass.NONE)
            == SensitivityLevel.LOW
        )

    def test_high_none_gives_low_failsafe(self) -> None:
        assert (
            derive_sensitivity(Identifiability.HIGH, DataClass.NONE)
            == SensitivityLevel.LOW
        )
