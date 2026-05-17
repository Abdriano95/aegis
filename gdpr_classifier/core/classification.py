"""Classification result, sensitivity level and dimension enums."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from .finding import Finding


class SensitivityLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Identifiability(str, Enum):
    """Identifiability dimension (Beslut 37, Beslut 49 reviderad).

    Categorical classification of how a person is identified in the text:
    - NONE: no identification possible.
    - INDIRECT: indirect identification via the puzzle-piece effect
      (GDPR recital 26, validated context.kombination).
    - DIRECT: direct identification via an article 4 finding
      (name, personal ID number, email, etc.).

    When both direct and indirect identification apply, DIRECT wins.
    """

    NONE = "none"
    INDIRECT = "indirect"
    DIRECT = "direct"


class DataClass(str, Enum):
    """Data protection class dimension (Beslut 37, Beslut 49 reviderad).

    Categorical classification of the GDPR-legal data category:
    - NONE: no sensitive information.
    - SPECIAL: article 9 (special categories of personal data).
    - CRIMINAL: article 10 (passive in v0.3.0, Beslut 40 — structural
      marker for a future article 10 layer).

    An ORDINARY level was removed during the Beslut 49 revision as
    redundant. "Ordinary personal data" is a consequence of a person
    being identifiable without sensitive material — it is captured by
    the (DIRECT, NONE) and (INDIRECT, NONE) cells in the derivation
    table (see aggregator.derive_sensitivity) and does not need its own
    data-class level.
    """

    NONE = "none"
    SPECIAL = "special"
    CRIMINAL = "criminal"


@dataclass(frozen=True)
class Classification:
    findings: list[Finding]
    sensitivity: SensitivityLevel
    active_layers: list[str]
    overlapping_findings: list[tuple[Finding, Finding]]
    identifiability: Identifiability = Identifiability.NONE
    data_class: DataClass = DataClass.NONE
    weakest_evidence_basis: Literal[
        "structural_support",
        "high_confidence_no_support",
        "no_support_required",
    ] | None = None
    # Härlett sammandrag: svagaste evidence_basis bland de fynd som faktiskt
    # bar identifiability/data_class ("den svagaste länken i klassningen").
    # Sätts av aggregatorn enbart i cross_validating-läget; None i legacy och
    # när inga fynd bar dimensionerna (arkitektur.md §9.6.3). Duplicerar inte
    # per-fynd-värdet på Finding.evidence_basis och är inte sanningskälla.
