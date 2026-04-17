"""GDPR category enumeration."""

from __future__ import annotations

from enum import Enum


class Category(str, Enum):
    PERSONNUMMER = "article4.personnummer"
    EMAIL = "article4.email"
    TELEFONNUMMER = "article4.telefonnummer"
    IBAN = "article4.iban"
    NAMN = "article4.namn"
    ADRESS = "article4.adress"
    POSTORT = "article4.postort"
    POSTNUMMER = "article4.postnummer"
    KORTNUMMER = "article4.kortnummer"
    CVV = "article4.cvv"
    EXPIRY_DATE = "article4.expiry_date"
    SECURITY_CODE = "article4.security_code"

    HALSODATA = "article9.halsodata"
    ETNISKT_URSPRUNG = "article9.etniskt_ursprung"
    POLITISK_ASIKT = "article9.politisk_asikt"
    RELIGIOS_OVERTYGELSE = "article9.religios_overtygelse"
    FACKMEDLEMSKAP = "article9.fackmedlemskap"
    BIOMETRISK_DATA = "article9.biometrisk_data"
    SEXUELL_LAGGNING = "article9.sexuell_laggning"

    KONTEXTUELLT_KANSLIG = "context.identifierbar"
