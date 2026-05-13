"""Classification result, sensitivity level and dimension enums."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .finding import Finding


class SensitivityLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Identifiability(str, Enum):
    """Identifiability dimension (Beslut 37, Loggbok iteration 3).

    HIGH is passive in v0.3.0 — reserved for a future layer extension that
    detects direct identifiers without contextual mechanism. The level is
    included structurally per the Open-Closed Principle (Martin 2003) so
    the type can be extended without breaking changes.
    """

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DataClass(str, Enum):
    """Data protection class dimension (Beslut 37, Loggbok iteration 3).

    CRIMINAL is passive in v0.3.0 (Beslut 40) — a structural marker for a
    future Article 10 layer (data on criminal convictions and offences).
    The level is included structurally per the Open-Closed Principle
    (Martin 2003) so the type can be extended without breaking changes.
    """

    NONE = "none"
    ORDINARY = "ordinary"
    SPECIAL = "special"
    CRIMINAL = "criminal"


@dataclass(frozen=True)
class Classification:
    findings: list[Finding]
    sensitivity: SensitivityLevel
    active_layers: list[str]
    overlapping_findings: list[tuple[Finding, Finding]]
    mechanism_used: str | None = None
    identifiability: Identifiability = Identifiability.NONE
    data_class: DataClass = DataClass.NONE
