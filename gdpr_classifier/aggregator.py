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
        filtered = self._apply_containment_rules(findings)
        overlaps = self._find_overlaps(filtered)
        sensitivity = self._determine_sensitivity(filtered)
        return Classification(
            findings=filtered,
            sensitivity=sensitivity,
            active_layers=active_layers,
            overlapping_findings=overlaps,
        )

    def _apply_containment_rules(
        self, findings: list[Finding],
    ) -> list[Finding]:
        """Remove telefon findings that overlap with IBAN findings.

        IBAN requires mod97 checksum validation and is strictly more specific
        than telefon regex matching.  A valid IBAN is never a phone number.
        This rule only targets IBAN-telefon overlap; all other recognizer
        combinations are left untouched.

        See SSOT arkitektur.md §8 and §14.1 for motivation.
        """
        iban_findings = [
            f for f in findings if f.category == Category.IBAN
        ]
        if not iban_findings:
            return findings

        telefon_to_remove: set[int] = set()
        for idx, f in enumerate(findings):
            if f.category != Category.TELEFONNUMMER:
                continue
            for iban in iban_findings:
                if f.start < iban.end and iban.start < f.end:
                    telefon_to_remove.add(idx)
                    break

        if not telefon_to_remove:
            return findings

        return [
            f for idx, f in enumerate(findings)
            if idx not in telefon_to_remove
        ]

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
        iteration 1 - aktiveras i iteration 2 när kontextuella
        indirekt-identifierare (pusselbitseffekten) införs via Lager 3.
        """
        if not findings:
            return SensitivityLevel.NONE
        for finding in findings:
            category: Category = finding.category
            if category.value.startswith(("article9.", "context.")):
                return SensitivityLevel.HIGH
        return SensitivityLevel.LOW
