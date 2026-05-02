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
    def __init__(
        self,
        medium_threshold: float = 0.7,
        high_confidence_bypass: float = 0.85,
        min_evidence_count: int = 2,
    ) -> None:
        self.medium_threshold = medium_threshold
        self.high_confidence_bypass = high_confidence_bypass
        self.min_evidence_count = min_evidence_count

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
        """Bestämmer sammanfattande känslighetsnivå (SSOT arkitektur.md §8).

        HIGH:   minst ett article9.*-fynd (Lager 3, Article9Layer).
        MEDIUM: context.kombination-fynd med confidence >= medium_threshold
                som passerar hög-konfidens-bypass eller Mekanism 3.
        LOW:    article4.*-fynd utan HIGH- eller MEDIUM-triggar.
        NONE:   inga fynd.

        D5-korrigering: isolerade context.*-fynd (source != "context.kombination")
        ignoreras vid sensitivity-bestämning men bevaras i Classification.findings.
        """
        if any(f.category.value.startswith("article9.") for f in findings):
            return SensitivityLevel.HIGH

        kombination_candidates = [
            f for f in findings
            if f.source == "context.kombination"
            and f.confidence >= self.medium_threshold
        ]
        for kf in kombination_candidates:
            # Privacy by Design fail-safe: hög konfidens kringgår Mekanism 3 (Beslut 21, GDPR art. 25)
            if kf.confidence >= self.high_confidence_bypass:
                return SensitivityLevel.MEDIUM
            if self._passes_mechanism_3(kf, findings):
                return SensitivityLevel.MEDIUM

        if any(f.category.value.startswith("article4.") for f in findings):
            return SensitivityLevel.LOW

        return SensitivityLevel.NONE

    def _passes_mechanism_3(
        self, kombination: Finding, all_findings: list[Finding],
    ) -> bool:
        """Mekanism 3: verifiera att minst min_evidence_count Lager 1/2-fynd
        överlappar med kombination-fyndets span.

        CombinationLayer exponerar inga sub-spans i kombination-fyndet; metadata
        innehåller reasoning och validation_path. Individuella signaler returneras
        som separata Finding-objekt. Mekanism 3 räknar överlappande fynd från
        Lager 1 (source börjar på "pattern.") och Lager 2 (source börjar på
        "entity.") mot kombination-fyndets totala span.
        """
        evidence = [
            f for f in all_findings
            if (f.source.startswith("pattern.") or f.source.startswith("entity."))
            and f.start < kombination.end
            and kombination.start < f.end
        ]
        return len(evidence) >= self.min_evidence_count
