"""Classification result and sensitivity level."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .finding import Finding


class SensitivityLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    HIGH = "high"


@dataclass(frozen=True)
class Classification:
    findings: list[Finding]
    sensitivity: SensitivityLevel
    active_layers: list[str]
    overlapping_findings: list[tuple[Finding, Finding]]
