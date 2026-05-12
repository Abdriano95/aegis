"""Aggregator that merges findings from all layers into a Classification."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
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
        if not (0.0 <= medium_threshold <= 1.0):
            raise ValueError("medium_threshold must be between 0.0 and 1.0")
        if not (0.0 <= high_confidence_bypass <= 1.0):
            raise ValueError("high_confidence_bypass must be between 0.0 and 1.0")
        if high_confidence_bypass < medium_threshold:
            raise ValueError("high_confidence_bypass must be >= medium_threshold")
        if min_evidence_count < 1:
            raise ValueError("min_evidence_count must be a positive integer")
        
        self.medium_threshold = medium_threshold
        self.high_confidence_bypass = high_confidence_bypass
        self.min_evidence_count = min_evidence_count

    def aggregate(
        self,
        findings: list[Finding],
        active_layers: list[str],
    ) -> Classification:
        filtered = self._apply_containment_rules(findings)
        filtered = self._deduplicate_same_category_overlap(filtered)
        overlaps = self._find_overlaps(filtered)
        sensitivity, mechanism = self._determine_sensitivity(filtered)
        return Classification(
            findings=filtered,
            sensitivity=sensitivity,
            active_layers=active_layers,
            overlapping_findings=overlaps,
            mechanism_used=mechanism,
        )

    def _apply_containment_rules(
        self, findings: list[Finding],
    ) -> list[Finding]:
        """Apply all containment rules in sequence.

        Rule 1 — IBAN-telefon: remove telefon findings that overlap with IBAN
        findings (IBAN is strictly more specific via mod97 checksum).

        Rule 2 — article9-context: remove context.organisation and
        context.yrke findings whose span is completely covered by an
        article9.* finding. Fackföreningar och religiösa organisationer
        detekteras korrekt av Article9Layer; a parallel context.organisation
        finding on the same span is a false positive.

        See SSOT arkitektur.md §8 and §14.1 for motivation.
        """
        filtered = self._remove_telefon_covered_by_iban(findings)
        return self._remove_context_covered_by_article9(filtered)

    def _remove_telefon_covered_by_iban(
        self, findings: list[Finding],
    ) -> list[Finding]:
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

    def _remove_context_covered_by_article9(
        self, findings: list[Finding],
    ) -> list[Finding]:
        article9_findings = [
            f for f in findings if f.category.value.startswith("article9.")
        ]
        if not article9_findings:
            return findings

        _context_signal_categories = {Category.ORGANISATION, Category.YRKE}
        to_remove: set[int] = set()
        for idx, f in enumerate(findings):
            if f.category not in _context_signal_categories:
                continue
            for a9 in article9_findings:
                if a9.start <= f.start and f.end <= a9.end:
                    to_remove.add(idx)
                    break

        if not to_remove:
            return findings

        return [
            f for idx, f in enumerate(findings)
            if idx not in to_remove
        ]

    def _deduplicate_same_category_overlap(
        self, findings: list[Finding],
    ) -> list[Finding]:
        """Merge same-category findings with overlapping spans (Issue #103).

        När EntityLayer och CombinationLayer detekterar samma organisationsnamn
        parallellt skapas redundans i Classification.findings. Denna metod
        behåller fyndet med högst confidence och propagerar borttaget fynds
        ``source`` till behållet fynds ``metadata["deduplicated_sources"]``.

        Tiebreaker vid lika confidence: stabil ordning — det fynd som kommer
        först i ``findings`` behålls. Cross-category overlaps (ADRESS+PLATS,
        article9+context etc.) påverkas inte.

        Körs efter ``_apply_containment_rules`` och före ``_find_overlaps``.
        See SSOT arkitektur.md §8 för motivation.
        """
        by_category: dict[Category, list[tuple[int, Finding]]] = defaultdict(list)
        for idx, f in enumerate(findings):
            by_category[f.category].append((idx, f))

        to_remove: set[int] = set()
        sources_to_propagate: dict[int, list[str]] = defaultdict(list)

        for group in by_category.values():
            if len(group) < 2:
                continue
            # Stabil sortering: confidence desc, behåller input-ordning vid lika.
            sorted_group = sorted(group, key=lambda t: -t[1].confidence)
            for i in range(len(sorted_group)):
                kept_idx, kept_f = sorted_group[i]
                if kept_idx in to_remove:
                    continue
                for j in range(i + 1, len(sorted_group)):
                    other_idx, other_f = sorted_group[j]
                    if other_idx in to_remove:
                        continue
                    if kept_f.start < other_f.end and other_f.start < kept_f.end:
                        to_remove.add(other_idx)
                        sources_to_propagate[kept_idx].append(other_f.source)

        if not to_remove:
            return findings

        result: list[Finding] = []
        for idx, f in enumerate(findings):
            if idx in to_remove:
                continue
            if idx in sources_to_propagate:
                new_metadata = dict(f.metadata) if f.metadata else {}
                existing = new_metadata.get("deduplicated_sources", [])
                new_metadata["deduplicated_sources"] = (
                    existing + sources_to_propagate[idx]
                )
                f = replace(f, metadata=new_metadata)
            result.append(f)
        return result

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
    ) -> tuple[SensitivityLevel, str]:
        """Bestämmer sammanfattande känslighetsnivå (SSOT arkitektur.md §8).

        HIGH:   minst ett article9.*-fynd (Lager 3, Article9Layer).
        MEDIUM: context.kombination-fynd med confidence >= medium_threshold
                som passerar hög-konfidens-bypass eller Mekanism 3.
        LOW:    article4.*-fynd utan HIGH- eller MEDIUM-triggar.
        NONE:   inga fynd.

        D5-korrigering: isolerade context.*-fynd (source != "context.kombination")
        ignoreras vid sensitivity-bestämning men bevaras i Classification.findings.

        Returnerar (SensitivityLevel, mechanism_used) där mechanism_used är en
        av "article9", "bypass", "mechanism3", "low", "none".
        """
        if any(f.category.value.startswith("article9.") for f in findings):
            return SensitivityLevel.HIGH, "article9"

        kombination_candidates = [
            f for f in findings
            if f.source == "context.kombination"
            and f.confidence >= self.medium_threshold
        ]
        for kf in kombination_candidates:
            # Privacy by Design fail-safe: hög konfidens kringgår Mekanism 3 (Beslut 21, GDPR art. 25)
            if kf.confidence >= self.high_confidence_bypass:
                return SensitivityLevel.MEDIUM, "bypass"
            if self._passes_mechanism_3(kf, findings):
                return SensitivityLevel.MEDIUM, "mechanism3"

        if any(f.category.value.startswith("article4.") for f in findings):
            return SensitivityLevel.LOW, "low"

        return SensitivityLevel.NONE, "none"

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
