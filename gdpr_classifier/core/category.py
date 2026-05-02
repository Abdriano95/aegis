"""GDPR category enumeration."""

from __future__ import annotations

from enum import Enum


class Category(str, Enum):
    # Artikel 4: Personuppgifter
    PERSONNUMMER = "article4.personnummer"
    EMAIL = "article4.email"
    TELEFONNUMMER = "article4.telefonnummer"
    IBAN = "article4.iban"
    NAMN = "article4.namn"
    ADRESS = "article4.adress"
    POSTORT = "article4.postort"
    POSTNUMMER = "article4.postnummer"
    BETALKORT = "article4.betalkort"
    
    # Artikel 9: Särskilda behandlingar av personuppgifter
    HALSODATA = "article9.halsodata"
    ETNISKT_URSPRUNG = "article9.etniskt_ursprung"
    POLITISK_ASIKT = "article9.politisk_asikt"
    RELIGIOS_OVERTYGELSE = "article9.religios_overtygelse"
    FACKMEDLEMSKAP = "article9.fackmedlemskap"
    BIOMETRISK_DATA = "article9.biometrisk_data"
    GENETISK_DATA = "article9.genetisk_data"
    SEXUELL_LAGGNING = "article9.sexuell_laggning"

    # Kontextsignaler: inte art 4-data i sig, bidrar till klassificering i kombination
    ORGANISATION = "context.organisation"
    YRKE = "context.yrke"
    PLATS = "context.plats"
    KOMBINATION = "context.kombination"

    # Kontextuellt känsligt data
    KONTEXTUELLT_KANSLIG = "context.identifierbar"
