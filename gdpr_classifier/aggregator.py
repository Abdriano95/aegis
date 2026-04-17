"""Aggregator that merges findings from all layers into a Classification."""

from __future__ import annotations

from itertools import combinations

from gdpr_classifier.core import (
    Category,
    Classification,
    Finding,
    SensitivityLevel,
)


class Aggregator:
    def aggregate(
        self,
        findings: list[Finding],
        active_layers: list[str],
    ) -> Classification:
        overlaps = self._find_overlaps(findings)
        sensitivity = self._determine_sensitivity(findings)
        return Classification(
            findings=findings,
            sensitivity=sensitivity,
            active_layers=active_layers,
            overlapping_findings=overlaps,
        )

    def _find_overlaps(
        self, findings: list[Finding],
    ) -> list[tuple[Finding, Finding]]:
        """Identifierar unika par av fynd vars textavsnitt överlappar.

        Två findings överlappar om ``a.start < b.end and b.start < a.end``.
        Endast unika par returneras (combinations, inte permutations): för
        varje par (a, b) finns alltså aldrig motsvarande (b, a) i resultatet.
        """
        overlaps: list[tuple[Finding, Finding]] = []
        for a, b in combinations(findings, 2):
            if a.start < b.end and b.start < a.end:
                overlaps.append((a, b))
        return overlaps

    def _determine_sensitivity(
        self, findings: list[Finding],
    ) -> SensitivityLevel:
        """Bestämmer sammanfattande känslighetsnivå.

        NONE: inga findings.
        LOW:  enbart Artikel 4-fynd.
        HIGH: minst ett Artikel 9-fynd eller kontextuellt känsligt fynd.

        MEDIUM är definierad i ``SensitivityLevel`` men tilldelas aldrig i
        iteration 1 - används först när kontextuella indirekt-identifierare
        (pusselbitseffekten) införs i iteration 3.
        """
        if not findings:
            return SensitivityLevel.NONE
        for finding in findings:
            category: Category = finding.category
            if category.value.startswith(("article9.", "context.")):
                return SensitivityLevel.HIGH
        return SensitivityLevel.LOW
