"""Aggregator that merges findings from all layers into a Classification."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from itertools import combinations
from typing import Literal

from gdpr_classifier.core import (
    Category,
    Classification,
    DataClass,
    Finding,
    Identifiability,
    SensitivityLevel,
)

EvidenceBasis = Literal[
    "structural_support",
    "high_confidence_no_support",
    "no_support_required",
]

# Ordning svagast → starkast (arkitektur.md §9.6.3, användarbeslut 2026-05-16):
# en fail-safe-bypass utan strukturellt stöd är den svagaste länken; ett
# självvaliderande fynd som inte ens kräver stöd (checksum-mönster, PRS,
# article9) är den starkaste.
_EVIDENCE_BASIS_RANK: dict[str, int] = {
    "high_confidence_no_support": 0,
    "structural_support": 1,
    "no_support_required": 2,
}


def derive_sensitivity(
    identifiability: Identifiability,
    data_class: DataClass,
) -> SensitivityLevel:
    """Ren funktion: härleder SensitivityLevel från (identifiability, data_class).

    Total över alla 9 (identifiability, data_class)-kombinationer. Beror enbart
    på inmatningarna — läser inte Aggregator-tillstånd eller trösklar.

    Härledningstabell (Beslut 37, Beslut 49 reviderad):

        identifiability \\ data_class | NONE | SPECIAL | CRIMINAL
        ------------------------------|------|---------|----------
        NONE                          | NONE | LOW     | LOW
        INDIRECT                      | LOW  | MEDIUM  | MEDIUM
        DIRECT                        | LOW  | HIGH    | HIGH

    Alla 9 celler är strukturellt definierade. Sensitivity är en
    UI-abstraktion för intressentvisning och V1:s konfigurerbara
    granskningsprioritering — inte en självständig dimension.
    """
    match (identifiability, data_class):
        case (Identifiability.NONE, DataClass.NONE):
            return SensitivityLevel.NONE
        case (Identifiability.DIRECT,
              DataClass.SPECIAL | DataClass.CRIMINAL):
            return SensitivityLevel.HIGH
        case (Identifiability.INDIRECT,
              DataClass.SPECIAL | DataClass.CRIMINAL):
            return SensitivityLevel.MEDIUM
        case _:
            return SensitivityLevel.LOW


class Aggregator:
    def __init__(
        self,
        medium_threshold: float = 0.7,
        high_confidence_bypass: float = 0.85,
        min_evidence_count: int = 2,
        cross_validation_mode: Literal[
            "legacy", "cross_validating"
        ] = "cross_validating",
    ) -> None:
        if not (0.0 <= medium_threshold <= 1.0):
            raise ValueError("medium_threshold must be between 0.0 and 1.0")
        if not (0.0 <= high_confidence_bypass <= 1.0):
            raise ValueError("high_confidence_bypass must be between 0.0 and 1.0")
        if high_confidence_bypass < medium_threshold:
            raise ValueError("high_confidence_bypass must be >= medium_threshold")
        if min_evidence_count < 1:
            raise ValueError("min_evidence_count must be a positive integer")
        if cross_validation_mode not in ("legacy", "cross_validating"):
            raise ValueError(
                "cross_validation_mode must be 'legacy' or 'cross_validating'"
            )

        self.medium_threshold = medium_threshold
        self.high_confidence_bypass = high_confidence_bypass
        self.min_evidence_count = min_evidence_count
        # Default "cross_validating" (I-7g, 2026-05-16): I-7f visade att de
        # två lägena ger byte-identiska klassifikationsutfall (0/159 sanity-
        # avvikelser, oförändrad konfusionsmatris) men att cross_validating
        # ger mer rättvisande evidensredovisning (5 TP context.kombination →
        # structural_support i stället för bypass-tagg). "legacy" är opt-in
        # via explicit cross_validation_mode="legacy" för bakåtkompatibilitet
        # och reproduktion av iteration 2- samt I-7d/pre-I-7f-baslinjer
        # (mätinstrumentpåverkan: kodanalys §10; arkitektur.md §9.6.4).
        self.cross_validation_mode = cross_validation_mode

    def aggregate(
        self,
        findings: list[Finding],
        active_layers: list[str],
    ) -> Classification:
        filtered = self._apply_containment_rules(findings)
        filtered = self._deduplicate_same_category_overlap(filtered)
        if self.cross_validation_mode == "cross_validating":
            filtered = self._apply_evidence_weighting(filtered)
        overlaps = self._find_overlaps(filtered)
        identifiability, data_class, weakest_evidence_basis = (
            self._determine_dimensions(filtered)
        )
        sensitivity = derive_sensitivity(identifiability, data_class)
        return Classification(
            findings=filtered,
            sensitivity=sensitivity,
            active_layers=active_layers,
            overlapping_findings=overlaps,
            identifiability=identifiability,
            data_class=data_class,
            weakest_evidence_basis=weakest_evidence_basis,
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

    def _apply_evidence_weighting(
        self, findings: list[Finding],
    ) -> list[Finding]:
        """Tagga evidence_basis per beslutstabell R1–R7 (arkitektur.md §9.6.2).

        Körs endast i cross_validating-läget, efter containment/dedup och
        före dimensionsbestämning (§9.6.3). Default evidence_basis är redan
        "no_support_required" (R1 pattern.*, R2/R3/R4 entity.*, R5
        article9.*, R7 isolerade context.*), så endast R6
        (context.kombination) kan ändra taggen. Returnerar en ny lista;
        ändrade fynd är taggade kopior via dataclasses.replace (samma mönster
        som _deduplicate_same_category_overlap), oförändrade fynd passeras
        igenom som samma objekt.

        Passen ändrar INTE vilka fynd som bidrar till dimensionsbestämningen
        — _has_validated_kombination och article4/article9-existenskollarna
        är oförändrade i båda lägena (prompt punkt e, §9.6.4). I-7b lägger
        transparenstaggar; den faktiska dimensions-/precisionsändringen hör
        till I-7c. R3/R4 (entity.spacy_LOC/_ORG) bidrar som strukturellt
        stöd för R6 via entity.*-prefixet i _count_structural_support —
        källdrivet, fungerar oavsett I-7c-mappning.
        """
        result: list[Finding] = []
        for f in findings:
            if f.source != "context.kombination":  # R1/R2/R3/R4/R5/R7
                result.append(f)  # default no_support_required, oförändrat
                continue
            # R6 context.kombination: generaliserad Mekanism 3.
            count = self._count_structural_support(
                f, findings, ("pattern.", "entity."),
            )
            if count >= self.min_evidence_count:
                result.append(
                    replace(f, evidence_basis="structural_support")
                )
            elif f.confidence >= self.high_confidence_bypass:
                result.append(
                    replace(f, evidence_basis="high_confidence_no_support")
                )
            else:
                # Passerar inte Mekanism 3 och ingen bypass: behåll default
                # "no_support_required". Bidrar ej till dimensionen
                # (_has_validated_kombination oförändrad).
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

    def _determine_dimensions(
        self, findings: list[Finding],
    ) -> tuple[Identifiability, DataClass, EvidenceBasis | None]:
        """Bestämmer (identifiability, data_class, weakest_evidence_basis).

        Identifiability:
            NONE     ingen article4.*-fynd och ingen validerad kombination.
            INDIRECT validerad context.kombination utan article4.*-fynd
                     (pusselbitseffekt, GDPR skäl 26).
            DIRECT   minst ett article4.*-fynd (oavsett kombination).
                     Direkt identifiering trumfar indirekt resonemang.

        Data_class:
            NONE     inget article9.*-fynd.
            SPECIAL  minst ett article9.*-fynd.
            CRIMINAL passiv i v0.3.0 (Beslut 40).

        weakest_evidence_basis: härlett sammandrag — svagaste evidence_basis
        bland de fynd som FAKTISKT bar identifiability/data_class
        (arkitektur.md §9.6.3). None i legacy och när inga fynd bar
        dimensionerna. Identifiability/data_class-logiken är oförändrad mot
        legacy: I-7b lägger enbart transparenstaggar + sammandrag, den
        faktiska dimensions-/precisionsändringen hör till I-7c.

        mechanism_used är borttagen från modellen (Beslut 49 reviderad) —
        klassifikationen kommuniceras helt av paret.

        D5-korrigering: isolerade context.*-fynd (source != "context.kombination")
        ignoreras vid dimensionsbestämning men bevaras i Classification.findings
        (Beslut 11, Loggbok iteration 1; Beslut 19, Loggbok iteration 2).
        """
        article4_findings = [
            f for f in findings if f.category.value.startswith("article4.")
        ]
        article9_findings = [
            f for f in findings if f.category.value.startswith("article9.")
        ]

        if article4_findings:
            identifiability = Identifiability.DIRECT
        elif self._has_validated_kombination(findings):
            identifiability = Identifiability.INDIRECT
        else:
            identifiability = Identifiability.NONE

        if article9_findings:
            data_class = DataClass.SPECIAL
        else:
            data_class = DataClass.NONE

        weakest_evidence_basis = self._derive_weakest_evidence_basis(
            findings,
            identifiability,
            data_class,
            article4_findings,
            article9_findings,
        )
        return identifiability, data_class, weakest_evidence_basis

    def _has_validated_kombination(
        self, findings: list[Finding],
    ) -> bool:
        """Returnerar True om någon context.kombination passerar Mekanism 3
        eller hög-konfidens-bypass.

        Båda valideringsvägarna mappas till INDIRECT identifiability eftersom
        de validerar samma kombinationsclaim genom olika mekanismer (Mekanism
        3 = evidensräkning, bypass = hög konfidens som fail-safe enligt
        Beslut 21, GDPR artikel 25).
        """
        candidates = [
            f for f in findings
            if f.source == "context.kombination"
            and f.confidence >= self.medium_threshold
        ]
        for kf in candidates:
            if kf.confidence >= self.high_confidence_bypass:
                return True
            if self._passes_mechanism_3(kf, findings):
                return True
        return False

    def _validated_kombination_findings(
        self, findings: list[Finding],
    ) -> list[Finding]:
        """De context.kombination-fynd som faktiskt validerar (bär INDIRECT).

        Speglar avsiktligt _has_validated_kombination-predikatet
        (medium_threshold-golv + bypass eller Mekanism 3) men returnerar de
        bidragande fynden i stället för en bool, för weakest_evidence_basis-
        härledningen (arkitektur.md §9.6.3). _has_validated_kombination
        lämnas oförändrad (prompt punkt e); detta är en separat ren läsväg
        utan sidoeffekt på legacy.
        """
        return [
            f for f in findings
            if f.source == "context.kombination"
            and f.confidence >= self.medium_threshold
            and (
                f.confidence >= self.high_confidence_bypass
                or self._passes_mechanism_3(f, findings)
            )
        ]

    def _derive_weakest_evidence_basis(
        self,
        findings: list[Finding],
        identifiability: Identifiability,
        data_class: DataClass,
        article4_findings: list[Finding],
        article9_findings: list[Finding],
    ) -> EvidenceBasis | None:
        """Svagaste evidence_basis bland fynd som FAKTISKT bar slutdimensionen.

        Endast i cross_validating-läget; None i legacy och när ingen
        dimension bars (arkitektur.md §9.6.3, användarbeslut 2026-05-16).

        Bidragande mängd (de fynd som faktiskt bar slutvärdet):
          - DIRECT   → article4.*-fynden. En context.kombination som
                       trumfats av DIRECT ingår INTE (bar inte
                       identifiability).
          - INDIRECT → de context.kombination-fynd som faktiskt validerade.
          - SPECIAL  → article9.*-fynden (union, oberoende av
                       identifiability).

        Svagast → starkast enligt _EVIDENCE_BASIS_RANK:
        high_confidence_no_support < structural_support < no_support_required.
        """
        if self.cross_validation_mode != "cross_validating":
            return None

        contributing: list[Finding] = []
        if identifiability == Identifiability.DIRECT:
            contributing.extend(article4_findings)
        elif identifiability == Identifiability.INDIRECT:
            contributing.extend(
                self._validated_kombination_findings(findings)
            )
        if data_class == DataClass.SPECIAL:
            contributing.extend(article9_findings)

        if not contributing:
            return None

        return min(
            (f.evidence_basis for f in contributing),
            key=lambda eb: _EVIDENCE_BASIS_RANK[eb],
        )

    def _count_structural_support(
        self,
        target: Finding,
        all_findings: list[Finding],
        valid_source_prefixes: tuple[str, ...],
    ) -> int:
        """Antal fynd vars source matchar valid_source_prefixes och vars
        span strikt överlappar target-spannet.

        Generaliserad evidensräknings-primitiv (arkitektur.md §9.6.5).
        Mekanism 3 (Beslut 19) blir en konfigurerad instans av denna
        primitiv via _passes_mechanism_3. Stöddefinitionen är strikt
        span-överlapp, inget närhetsbaserat stöd (designprincip 2).

        I cross_validating-läget konsulteras även
        ``f.metadata["deduplicated_sources"]`` (I-7e): en source-tagg som
        _deduplicate_same_category_overlap tog bort vid
        same-category-källkollaps återupptäcks så att Mekanism 3 ser
        stödet igen. Mode-gaten är ett medvetet avsteg från primitivens
        annars källdrivna, mode-agnostiska karaktär; utan den skulle
        tillägget ändra legacy-lägets identifiability-beslut (via
        _has_validated_kombination → _passes_mechanism_3) och bryta
        bakåtkompatibilitet (I-7e:s acceptanskriterium, alternativ iii).
        Ett fynd räknas högst en gång (``continue`` efter primärträff).

        Containment-borttagning (t.ex. _remove_context_covered_by_article9)
        propagerar inte source och fångas INTE av denna mekanism — en
        parallell, oadresserad kollaps-väg, öppen punkt för framtida
        arbete (ev. I-7g). Defensiv metadata-läsning: ``metadata`` kan
        vara None eller sakna nyckeln (fynd som inte dedupats).
        """
        count = 0
        for f in all_findings:
            if not (f.start < target.end and target.start < f.end):
                continue
            if f.source.startswith(valid_source_prefixes):
                count += 1
                continue
            if self.cross_validation_mode == "cross_validating":
                dedup_sources = (f.metadata or {}).get(
                    "deduplicated_sources", []
                )
                if any(
                    s.startswith(valid_source_prefixes)
                    for s in dedup_sources
                ):
                    count += 1
        return count

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

        Tunn anropare av _count_structural_support (arkitektur.md §9.6.5):
        context.kombination är en konfigurerad instans med
        valid_source_prefixes=("pattern.", "entity."). Semantik oförändrad,
        Beslut 19 bevarad.
        """
        count = self._count_structural_support(
            kombination, all_findings, ("pattern.", "entity."),
        )
        return count >= self.min_evidence_count
