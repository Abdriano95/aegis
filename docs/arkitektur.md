# Arkitekturdokument: GDPR-klassificerare

**Projekt:** Examensarbete HT26 - Automatiserad klassificering av textinnehåll enligt GDPR  
**Författare:** Abdulla Mehdi & Johanna Gull  
**Handledare:** Johannes Sahlin, Högskolan i Borås  
**Version:** 0.1.1 (Iteration 1)  
**Senast uppdaterad:** 2026-04-20

---

## 1. Syfte och avgränsning

Artefakten identifierar och klassificerar textinnehåll (mail, prompts, chattmeddelanden, dokument) utifrån GDPR:s känslighetskategorier. Artefakten är ett beslutsstöd för förklassificering. Den ersätter inte juridisk eller mänsklig bedömning, utan skalar upp förmågan att upptäcka potentiellt känslig data.

Artefakten klassificerar. Den dirigerar inte, maskerar inte och anonymiserar inte. Om spår av routing-språk förekommer i detta dokument är det ett fel.

**GDPR-scope:**

- Iteration 1: Artikel 4 (personuppgifter) - personnummer, e-post, telefonnummer, IBAN, betalkort
- Iteration 2-3: Artikel 9 (särskilda kategorier) - hälsodata, etniskt ursprung, politiska åsikter, fackmedlemskap, biometrisk data, sexuell läggning, religiös övertygelse


## 2. Arkitekturell grund

### 2.1 Underbyggnad från litteraturen

Arkitekturen vilar på två typer av underbyggnad.

**Empirisk konvergens i forskningsområdet:** Flera oberoende studier har byggt flerstegs-arkitekturer för detektion av känslig data, där regelbaserad matchning kompletteras med semantisk analys. Mishra, Pagare & Sharma (2025) kombinerar regex med custom NER i en sekventiell pipeline för PII-detektion i finansiella dokument. Karras et al. (2025) rekommenderar hybridpipelines där regler filtrerar 85-90% och LLM hanterar residualen. Zhou et al. (2025) beskriver mönstermatchning som första steg följt av semantisk analys som andra steg. Zhan et al. (2025, PRISM) bygger en flerstegsarkitektur med NER-baserad känslighetsbedömning som kärna. Chaplia & Klym (2025) designar sin containeriserade arkitektur med utbytbara lager och tydliga gränser mellan komponenter.

**Arkitekturella mönster från mjukvaruvetenskapen (kernel theory):** Lageruppdelningen som mönster har sitt ursprung i Buschmann et al. (1996) Pattern-Oriented Software Architecture (POSA), Layers pattern. Pipeline-flödet motsvarar Pipes and Filters i samma volym. Utbytbarhet på lagernivå via ett gemensamt protokoll är Strategy pattern (Gamma et al., 1994). Separationen mellan domänobjekt och implementationsdetaljer följer Evans (2003) Domain-Driven Design.

**Spårbarhet** motiveras både av GDPR:s ansvarighetsprincip (artikel 5.2) och av Carrasco (2025) samt Thaldar (2026) som argumenterar för inbakad dokumentation och provenance metadata i AI-system.

*Notering: kernel theory-förankringen (POSA, Fowler, GoF) ska stärkas med exakta sidnummer innan slutrapporten. De empiriska källorna är verifierade.*

### 2.2 Designprinciper (preliminära, formaliseras i fas 4)

Följande designprinciper kodifieras av arkitekturen och formaliseras enligt Gregor, Chandra Kruse & Seidel (2020) efter avslutade BIE-cykler:

1. **Lagerseparation:** Mönsterbaserad, entitetsbaserad och kontextuell detektion separeras i oberoende lager som inte känner till varandra.
2. **Utbytbarhet:** Varje lager kan bytas ut utan att röra resten av systemet, så länge det implementerar det gemensamma protokollet.
3. **Spårbarhet:** Varje fynd bär med sig vilken regel och vilket lager som producerade det, så att klassificeringsbeslutet kan motiveras i efterhand.
4. **Progressiv utbyggnad:** Arkitekturen stöder att artefakten växer kumulativt över tre BIE-cykler utan omdesign.
5. **Recall-prioritering:** Designen optimerar för att inte missa känslig data (minimera falska negativa) snarare än att minimera falska positiva.


## 3. Systemöversikt

### 3.1 Övergripande dataflöde

```
Indata (text)
      │
      ├──────────┬──────────┬──────────┐
      ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Lager 1  │ │ Lager 2  │ │ Lager 3  │ │ Lager 4  │
│ Mönster  │ │Entiteter │ │Article9  │ │Kombination│
│ Regex,   │ │ NER      │ │ LLM      │ │ Pussel-  │
│ Luhn     │ │          │ │          │ │  bitar   │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
     │             │             │             │
     │       list[Finding] per lager           │
     │             │             │             │
     └─────────────┼─────────────┴─────────────┘
                   ▼
           ┌──────────────┐
           │  Aggregator  │
           │  Samlar fynd │
           │  Hanterar    │
           │  överlapp    │
           └──────┬───────┘
                  ▼
         ┌────────────────┐
         │ Classification │
         │ Kategori, fynd │
         │ spårning       │
         └────────────────┘
```

Alla fyra lager får samma text som input, oberoende av varandra. Varje lager returnerar en `list[Finding]`. Aggregatorn samlar alla fynd och producerar en `Classification`.


### 3.2 Komponentansvar

**Pipeline** instansierar och kör aktiva lager i sekvens. Den är ansvarig för att skicka samma text till varje lager och samla in fynd. Den innehåller ingen klassificeringslogik.

**Lager 1 (Mönster)** identifierar strukturerad data via deterministiska regler. Varje mönster implementeras som en separat recognizer. Personnummer valideras med Luhn-algoritmen för att minska falska positiva. Lagret producerar fynd med hög konfidens (regelbaserade matchningar är binära).

**Lager 2 (Entiteter)** identifierar namngivna entiteter (personer, platser, organisationer) via NER. Producerar fynd med varierande konfidens beroende på modellens säkerhet. Stub i iteration 1.

**Lager 3 (Article9Layer)** detekterar direkt uttryckta kategoriuppgifter enligt GDPR artikel 9 (hälsodata, religiös övertygelse, politisk åskådning, sexuell läggning, etniskt ursprung, biometriska data, fackföreningsmedlemskap) via en lokal LLM med utbytbar provider (Beslut 17, se avsnitt 6.1). Stub i iteration 1. Implementeras i iteration 2.

**Lager 4 (CombinationLayer)** bedömer om kombinationer av kontextsignaler skapar indirekt identifierbarhet — pusselbitseffekten (GDPR skäl 26). Exempel: "Min chef på lagret i Eskilstuna trakasserar mig" innehåller inga direkta identifierare men kan vara indirekt identifierbar via kombination av roll, plats och organisation (se avsnitt 6.2). Stub i iteration 1. Implementeras i iteration 2.

**Aggregator** samlar fynd från alla lager och producerar en klassificering. Hanterar överlappande fynd (se avsnitt 3.4). Bestämmer sammanfattande känslighetsnivå.


### 3.3 Domänmodell

#### Category (enum)

Representerar GDPR:s känslighetskategorier. Struktureras hierarkiskt med artikel som toppnivå.

```python
from enum import Enum

class Category(Enum):
    # Artikel 4: Personuppgifter
    PERSONNUMMER    = "article4.personnummer"
    EMAIL           = "article4.email"
    TELEFONNUMMER   = "article4.telefonnummer"
    IBAN            = "article4.iban"
    NAMN            = "article4.namn"
    ADRESS          = "article4.adress"
    POSTORT         = "article4.postort"
    POSTNUMMER      = "article4.postnummer"
    BETALKORT       = "article4.betalkort"

    # Artikel 9: Särskilda kategorier (iteration 2-3)
    HALSODATA             = "article9.halsodata"
    ETNISKT_URSPRUNG      = "article9.etniskt_ursprung"
    POLITISK_ASIKT        = "article9.politisk_asikt"
    RELIGIOS_OVERTYGELSE  = "article9.religios_overtygelse"
    FACKMEDLEMSKAP        = "article9.fackmedlemskap"
    BIOMETRISK_DATA       = "article9.biometrisk_data"
    SEXUELL_LAGGNING      = "article9.sexuell_laggning"

    # Kontextsignaler: inte art 4-data i sig, bidrar till klassificering i kombination
    ORGANISATION          = "context.organisation"
    YRKE                  = "context.yrke"
    PLATS                 = "context.plats"
    KOMBINATION           = "context.kombination"

    # Kontextuellt känslig (identifierbar indirekt, iteration 3)
    KONTEXTUELLT_KANSLIG  = "context.identifierbar"
```

Prefix-konventionen i `Category`-värdet kodar GDPR-status för kategorin. `article4.*` markerar direkta personuppgifter enligt artikel 4 (kategorier som i sig identifierar en fysisk person). `article9.*` markerar särskilda kategorier enligt artikel 9 (känsliga uppgifter som kräver rättslig grund enligt art 9.2). `context.*` markerar kontextsignaler som inte i sig är art 4-data men som bidrar till sensitivity-bedömningen i kombination med andra fynd (pusselbitseffekten; se `SensitivityLevel` nedan och avsnitt 8 för hur sensitivity bestäms). Aggregatorn kan diskriminera på prefix utan att känna till enskilda kategorinamn.

#### Finding (värdeobjekt)

Representerar en enskild detektion. Oföränderlig efter skapande.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Finding:
    category: Category
    start: int                # startposition i originaltexten
    end: int                  # slutposition i originaltexten
    text_span: str            # den exakta strängen som matchades
    confidence: float         # 0.0 - 1.0
    source: str               # "pattern.luhn_personnummer", "entity.spacy_PRS", etc.
    metadata: dict | None = None  # lagerspecifik extradata
```

Fältet `source` är centralt för spårbarhet. Det kodar både lager och specifik regel i formatet `{lager}.{regel}`. Detta möjliggör aggregering av utvärderingsmetriker per lager och per regel.

#### Classification (värdeobjekt)

Aggregerat resultat för en hel text.

```python
from dataclasses import dataclass, field
from enum import Enum

class SensitivityLevel(Enum):
    NONE   = "none"
    LOW    = "low"      # Artikel 4-data hittad
    MEDIUM = "medium"   # Indirekta identifierare eller kombinationer (pusselbitseffekten)
    HIGH   = "high"     # Artikel 9-data hittad

@dataclass(frozen=True)
class Classification:
    findings: list[Finding]
    sensitivity: SensitivityLevel
    active_layers: list[str]        # vilka lager som kördes
    overlapping_findings: list[tuple[Finding, Finding]]  # par av överlappande fynd
```


### 3.4 Överlappande fynd

När två lager rapporterar fynd som överlappar i samma textavsnitt bevaras båda fynden i listan. Aggregatorn markerar överlapp explicit i `overlapping_findings`. Motivering: spårbarhet är viktigare än kompakthet i en forskningsartefakt. Överlappen ger dessutom underlag för analys av hur lagren förstärker eller motsäger varandra, vilket är råmaterial för designprinciper i fas 4 (Formalization of Learning).

**Överlappskriterium:** Två fynd överlappar om deras textavsnitt har gemensamma teckenpositioner (start/end-intervallen skär varandra).


### 3.5 Layer-protokoll

Alla lager implementerar samma protokoll. Detta är den enda kontraktpunkt som binder lagren till domänen.

```python
from typing import Protocol

class Layer(Protocol):
    @property
    def name(self) -> str:
        """Unikt namn för lagret, t.ex. 'pattern', 'entity', 'context'."""
        ...

    def detect(self, text: str) -> list[Finding]:
        """Analyserar text och returnerar en lista med fynd."""
        ...
```

Varje lager implementerar `detect(text) -> list[Finding]`. Lagret ansvarar för att skapa korrekta `Finding`-objekt med rätt `source`-fält.


## 4. Lager 1: Mönsterigenkänning (Regex + Luhn)

### 4.1 Recognizer-arkitektur

Lager 1 delegerar till enskilda recognizers, var och en ansvarig för exakt en typ av mönster. Varje recognizer implementerar samma gränssnitt:

```python
class Recognizer(Protocol):
    @property
    def category(self) -> Category:
        ...

    @property
    def source_name(self) -> str:
        """T.ex. 'luhn_personnummer', 'regex_email'."""
        ...

    def recognize(self, text: str) -> list[Finding]:
        ...
```

`PatternLayer` itererar över sina registrerade recognizers och samlar ihop alla fynd.

### 4.2 Recognizers för iteration 1

**Personnummer** (`personnummer.py`):
- Matchar formaten YYMMDD-XXXX, YYMMDDXXXX, YYYYMMDD-XXXX, YYYYMMDDXXXX.
- Validerar kontrollsiffran med Luhn-algoritmen. Detta minskar falska positiva (Mishra et al., 2025).
- Validerar att datum-delen är ett giltigt datum.
- `source`: `"pattern.luhn_personnummer"`
- `confidence`: 1.0. Endast Luhn-validerade träffar emitteras i iteration 1; kandidater som inte passerar Luhn filtreras bort.

**E-post** (`email.py`):
- Matchar standardformat via regex.
- Teckenklasser i lokal- och domändel accepterar svenska bokstäver (å, ä, ö) för att stödja IDN-domäner som `företaget.se`. Punycode/xn-- ligger utanför iteration 1.
- `source`: `"pattern.regex_email"`
- `confidence`: 1.0

**Telefonnummer** (`telefon.py`):
- Matchar svenska telefonnummer (07X-XXX XX XX, +46-XXX-XXX XX XX, varianter).
- Stödjer valfria balanserade parenteser runt landskoden (t.ex. `(+46)70 999 88 77`, `(0046)...`); domestikt prefix `0` omfattas inte av parentes-varianten.
- `source`: `"pattern.regex_telefon"`
- `confidence`: 0.9 (telefonnummer-regex ger fler falska positiva än Luhn-validerade personnummer).

**IBAN** (`iban.py`):
- Matchar IBAN-format, validerar kontrollsiffror (mod 97).
- `source`: `"pattern.checksum_iban"`
- `confidence`: 1.0 vid lyckad kontrollsiffervalidering.

**Betalkort** (`betalkort.py`):
- Matchar betalkortsnummer (PAN) på 13-16 siffror.
- Validerar siffrorna med Luhn-algoritmen för att hantera bl.a. Visa, Mastercard och Amex.
- `source`: `"pattern.luhn_betalkort"`
- `confidence`: 1.0 vid lyckad Luhn-validering.


## 5. Lager 2: Entitetsigenkänning (NER)

Implementeras i iteration 1 med SpaCy-modellen `sv_core_news_lg` för svenska NER. Lagret är aktivt i pipelinen från och med v0.1.1.

**Entitetsmappning:**

- `PRS` → `Category.NAMN`, `source="entity.spacy_PRS"`
- `LOC` → `Category.ADRESS`, `source="entity.spacy_LOC"`
- `ORG` → `Category.ORGANISATION`, `source="entity.spacy_ORG"`

ORG mappas medvetet till `Category.ORGANISATION` med prefixet `context.*`, inte till en `article4.*`-kategori. Organisationer är inte personuppgifter enligt GDPR artikel 4. De fungerar däremot som pusselbitar i sensitivity-bedömningen: ett företagsnamn tillsammans med en roll eller en ort kan göra en enskild individ identifierbar även när inga direkta identifierare förekommer (pusselbitseffekten, avsnitt 3.3). Att hålla ORG separat från `article4.namn` gör dessutom att utvärderingsmetriker per kategori blir meningsfulla - person-prestanda blandas inte med ORG-prestanda.

**Konfidens:** SpaCy exponerar inte per-entitets-konfidens via ett enkelt API i `sv_core_news_lg`. I iteration 1 sätts `Finding.confidence = 0.8` som fast värde för alla NER-fynd. Detta är ett medvetet iteration-1-val och kan revideras i iteration 2 om kalibreringsmetriker motiverar det (t.ex. via per-token-sannolikheter eller byte till KB-BERT).

**Källformat:** `source`-fältet är `"entity.spacy_{LABEL}"` där `{LABEL}` är SpaCys råetikett (`PRS`/`LOC`/`ORG`). Detta bevarar lager-prefix-konventionen (`entity.*`) och gör det möjligt att filtrera utvärderingsrapporten per NER-etikett utan att inspektera `metadata`.

Modellen `sv_core_news_lg` använder SUC3-taggsetet; person-entiteter labellas `PRS`, inte `PER` (CoNLL). Mappningen och source-taggen speglar detta.


## 6. Lager 3 och 4: Kontextuell analys (Iteration 2)

Iteration 2 implementerar kontextuell analys i två separata lager med tydligt avgränsade ansvarsområden enligt Single Responsibility Principle (Beslut 18, Loggbok iteration 2).

### 6.1 Lager 3: Article9Layer (Artikel 9-detektion)

Implementeras i iteration 2. Article9Layer detekterar direkt uttryckta kategoriuppgifter enligt GDPR artikel 9: hälsodata, religiös övertygelse, politisk åskådning, sexuell läggning, etniskt ursprung, biometriska data och fackföreningsmedlemskap.

*Notering:* Genetiska data (GDPR artikel 9.1) saknas i nuvarande `Category`-enum (`gdpr_classifier/core/category.py`). Tillägg av `GENETISK_DATA` är en kodändring som hanteras i Issue #70 eller separat scope-item, inte i denna dokumentationsrevision.

**Ansvar:** Att identifiera explicita förekomster av artikel 9-data i text. Lagret klassificerar vad som nämnts, inte om personen är identifierbar. Det är Article9Layer:s fynd som triggar `HIGH`-känslighetsnivå i aggregatorn (se avsnitt 8).

**LLM-implementation:** Lagret använder en lokal LLM via en utbytbar `LLMProvider`-abstraktion (se avsnitt 10 för filstruktur). Lokal exekveringsmiljö är primär; molnprovider är sekundär och utbytbar utan ändringar i lagret. Beslut 17 (Loggbok iteration 2) motiverar detta val. Modellstorlek och arkitektur väljs baserat på prestanda mot artikel 9-kategorier i svenska texter och fastställs iterativt.

**Output:**
- `Finding.category` ∈ `{article9.halsodata, article9.religios_overtygelse, article9.politisk_asikt, article9.sexuell_laggning, article9.etniskt_ursprung, article9.biometrisk_data, article9.fackmedlemskap}`
- `Finding.source`: `"article9.{kategori}"` (t.ex. `"article9.halsodata"`)
- `Finding.confidence`: modellens rapporterade säkerhet, 0.0–1.0

Beslut 18 (Loggbok iteration 2) motiverar varför artikel 9-detektion separeras från kombinationslogik i ett eget lager.

### 6.2 Lager 4: CombinationLayer (Pusselbitsbedömning)

Implementeras i iteration 2. CombinationLayer bedömer om kombinationer av kontextsignaler i texten skapar indirekt identifierbarhet — pusselbitseffekten (GDPR skäl 26). En enskild kontextsignal (t.ex. yrke, organisation eller ort) är inte en personuppgift. I kombination kan de göra en individ identifierbar även utan direkta identifierare.

**Ansvar:** Att identifiera textavsnitt som i kombination ökar identifieringsrisken. Lagret producerar tre typer av utfall:

1. **Individuella signaler** (`context.{signal}`): Varje kontextsignal som bidrar till kombinationen rapporteras som ett separat fynd (t.ex. `context.organisation`, `context.yrke`, `context.plats`). Dessa fynd möjliggör spårbarhet per signal.

2. **Kombinationsfynd** (`context.kombination`): Om kombinationen bedöms tillräcklig emitterar lagret ett aggregerat fynd som täcker kombinationens samlade span. Det är detta fynd som aggregatorn evaluerar mot Mekanism 1 och Mekanism 3 (se avsnitt 8).

3. **Inga fynd:** Om texten inte innehåller tillräckliga signaler returneras tom lista.

**Source-format:**
- Individuella signaler: `"context.{signal}"` (t.ex. `"context.organisation"`)
- Aggregerat kombinationsfynd: `"context.kombination"`

Beslut 18 och 19 (Loggbok iteration 2) motiverar att kombinationslogiken implementeras i ett eget lager (Lager 4) medan aggregatorn ansvarar för mekanisk validering av kombinationsfynden.


## 7. Pipeline

Pipelinen tar en lista av aktiva lager, kör varje lager mot indatan, och skickar alla fynd till aggregatorn. I iteration 2 körs fyra lager parallellt mot samma input-text: Lager 1 (Mönster), Lager 2 (Entiteter), Lager 3 (Article9Layer) och Lager 4 (CombinationLayer). Inget lager ser ett annat lagers fynd — principen om ömsesidig lagerovetskap (avsnitt 2.2, princip 1) bevaras oförändrad.

```python
class Pipeline:
    def __init__(self, layers: list[Layer], aggregator: Aggregator):
        self.layers = layers
        self.aggregator = aggregator

    def classify(self, text: str) -> Classification:
        all_findings: list[Finding] = []
        for layer in self.layers:
            findings = layer.detect(text)
            all_findings.extend(findings)
        return self.aggregator.aggregate(
            findings=all_findings,
            active_layers=[layer.name for layer in self.layers]
        )
```

Konfiguration av aktiva lager sker via `config.py`. I iteration 1 är Lager 1 och Lager 2 aktiva; i iteration 2 aktiveras Lager 3 och Lager 4.


## 8. Aggregator

```python
class Aggregator:
    def __init__(
        self,
        medium_threshold: float = 0.7,
        high_confidence_bypass: float = 0.85,
        min_evidence_count: int = 2
    ):
        self.medium_threshold = medium_threshold
        self.high_confidence_bypass = high_confidence_bypass
        self.min_evidence_count = min_evidence_count

    def aggregate(
        self,
        findings: list[Finding],
        active_layers: list[str]
    ) -> Classification:
        overlaps = self._find_overlaps(findings)
        sensitivity = self._determine_sensitivity(findings)
        return Classification(
            findings=findings,
            sensitivity=sensitivity,
            active_layers=active_layers,
            overlapping_findings=overlaps
        )

    def _find_overlaps(
        self, findings: list[Finding]
    ) -> list[tuple[Finding, Finding]]:
        """Identifierar par av fynd vars textavsnitt överlappar."""
        ...

    def _determine_sensitivity(
        self, findings: list[Finding]
    ) -> SensitivityLevel:
        """
        HIGH:   minst ett article9.*-fynd (Lager 3, Article9Layer).
        MEDIUM: context.kombination-fynd som passerar Mekanism 1 (span-validering)
                och antingen Mekanism 3 (evidens >= min_evidence_count) eller
                hög-konfidens-bypass (confidence >= high_confidence_bypass).
        LOW:    article4.*-fynd utan HIGH- eller MEDIUM-triggar.
        NONE:   inga fynd.

        D5-korrigering: isolerade context.*-fynd utan ett matchande
        context.kombination-fynd triggar inte sensitivity-höjning (Beslut 11,
        Loggbok iteration 1; Beslut 19, Loggbok iteration 2).
        """
        # HIGH: direkt artikel 9-data hittad (Lager 3)
        if any(f.category.value.startswith("article9.") for f in findings):
            return SensitivityLevel.HIGH

        # MEDIUM: kombinationsfynd som passerar validering
        kombination_findings = [
            f for f in findings
            if f.source == "context.kombination"
            and f.confidence >= self.medium_threshold
        ]
        for kf in kombination_findings:
            # Hög-konfidens-bypass: Privacy by Design fail-safe (Beslut 21, GDPR art. 25)
            if kf.confidence >= self.high_confidence_bypass:
                return SensitivityLevel.MEDIUM
            # Mekanism 3: minimum evidence
            if self._passes_mechanism_3(kf, findings):
                return SensitivityLevel.MEDIUM

        # LOW: artikel 4-data hittad
        if any(f.category.value.startswith("article4.") for f in findings):
            return SensitivityLevel.LOW

        return SensitivityLevel.NONE

    def _passes_mechanism_3(
        self, kombination: Finding, all_findings: list[Finding]
    ) -> bool:
        """
        Mekanism 3: Minst min_evidence_count evidens-span korresponderar med
        fynd från Lager 1/2 eller förekommer ordagrant i originaltexten.
        Implementationsdetaljer fastställs i Issue #74.
        """
        ...
```

**Konfigurerbara trösklar (Beslut 20, Loggbok iteration 2):**

- `medium_threshold` (default `0.7`): minimumkonfidens för att ett `context.kombination`-fynd evalueras mot Mekanism 3 eller bypass.
- `high_confidence_bypass` (default `0.85`): konfidens som kringgår Mekanism 3. Privacy by Design som fail-safe-princip (Beslut 21, GDPR artikel 25): ett falskt negativt (missad identifierbar person) är allvarligare än ett falskt positivt. Kringgåendet är medvetet och spårbart via source-fältet.
- `min_evidence_count` (default `2`): minimumanatal evidens-span som krävs för att Mekanism 3 ska passera.

Slutgiltig kalibrering av trösklarna sker baserat på iteration 2:s kvantitativa utvärdering (Issue #75 / I-8).

**Mekanism 1 (span-validering):** Delegeras till Lager 4 (CombinationLayer) som producerar `context.kombination`-fynd med valida span-positioner. Aggregatorn kan verifiera span-integriteten vid behov utan att re-implementera logiken.

**D5-korrigering:** Isolerade `context.*`-fynd — alltså individuella signaler från Lager 4 utan ett matchande `context.kombination`-fynd — triggar inte sensitivity-höjning. Motivering: en enskild kontextsignal ökar inte identifieringsrisken utan kombination med andra signaler (Beslut 11, Loggbok iteration 1; Beslut 19, Loggbok iteration 2). Isolerade `context.*`-fynd bevaras i `Classification.findings` för spårbarhet men påverkar inte `sensitivity`.

I iteration 1 tilldelas endast `NONE`, `LOW` och `HIGH`. `MEDIUM` används från och med iteration 2 när Lager 3 och Lager 4 är aktiva.


## 9. Utvärdering

### 9.1 Ramverk

Utvärderingen följer FEDS (Venable, Pries-Heje & Baskerville, 2016) med artificiell (kvantitativ) och naturalistisk (kvalitativ) utvärdering efter varje BIE-cykel.

### 9.2 Kvantitativ utvärdering

**Matchningsnivå:** Spannivå (inte dokumentnivå). Varje enskilt fynd jämförs mot fasit-fynden. Matchningskriterium: samma kategori plus överlappande textavsnitt (start/end-intervallen skär varandra).

**Definitioner:**
- TP: predikterat fynd matchar ett fasit-fynd (kategori + överlappande span).
- FP: predikterat fynd saknar matchande fasit-fynd.
- FN: fasit-fynd saknar matchande predikterat fynd.
- TN: appliceras på dokumentnivå (text utan känslig data korrekt klassificerad som icke-känslig) - *Notera: Implementeras ej i klassificeringens ConfusionMatrix i iteration 1 då alla mätvärden (Recall, Precision, F1) beräknas på spannivå och ej kräver TN.*

**Mätvärden:**
- Recall = TP / (TP + FN). Primärt mätvärde. Missad känslig data innebär potentiellt lagbrott (Opitz, 2024).
- Precision = TP / (TP + FP). Sekundärt mätvärde. Överklassificering skapar ohanterlig administrativ börda.
- F1 = 2 * (Precision * Recall) / (Precision + Recall). Kompletterande balanserat mått.

**Aggregering:** Metriker rapporteras totalt, per GDPR-kategori, per lager och per regel (möjligt tack vare `Finding.source`).

### 9.3 Utvärderingsdatamodell

```python
@dataclass(frozen=True)
class LabeledFinding:
    """Fasit-fynd: vad som SKA hittas i texten."""
    category: Category
    start: int
    end: int
    text_span: str

@dataclass(frozen=True)
class LabeledText:
    """En text med tillhörande fasit."""
    text: str
    expected_findings: list[LabeledFinding]
    description: str = ""
```

`LabeledFinding` återanvänder samma `Category`-enum som artefakten. Om en ny kategori läggs till i `Category` måste testdata också uppdateras.

### 9.4 Utvärderingsflöde

```
Märkt testdataset (LabeledText[])
         │
         ▼
  Pipeline.classify(text)
         │
         ▼ predikterade Finding[]
         │
    Matcher: jämför Finding[] mot LabeledFinding[]
         │
         ▼
    ConfusionMatrix: TP, FP, FN
         │
         ▼
    Rapport: Recall, Precision, F1 (totalt + per kategori + per lager)
```

### 9.5 Testdata

Testdata skapas av Johanna och struktureras i JSON-format:

```json
[
  {
    "text": "Kontakta mig på anna.svensson@mail.se, mitt personnummer är 850101-1234.",
    "description": "Text med e-post och personnummer",
    "expected_findings": [
      {
        "category": "article4.email",
        "start": 19,
        "end": 42,
        "text_span": "anna.svensson@mail.se"
      },
      {
        "category": "article4.personnummer",
        "start": 62,
        "end": 73,
        "text_span": "850101-1234"
      }
    ]
  },
  {
    "text": "Mötet börjar klockan 14:00 i konferensrum B.",
    "description": "Okänslig text utan personuppgifter",
    "expected_findings": []
  }
]
```


## 10. Filstruktur

```
gdpr_classifier/
    __init__.py
    core/
        __init__.py
        category.py              # Category enum
        finding.py               # Finding dataclass
        classification.py        # Classification + SensitivityLevel
        layer.py                 # Layer Protocol
    layers/
        __init__.py
        pattern/
            __init__.py
            pattern_layer.py     # PatternLayer (itererar recognizers)
            recognizer.py        # Recognizer Protocol
            recognizers/
                __init__.py
                personnummer.py  # Regex + Luhn
                email.py         # Regex
                telefon.py       # Regex
                iban.py          # Regex + mod97
                betalkort.py     # Regex + Luhn (PAN 13-16 siffror)
        entity/
            __init__.py
            entity_layer.py      # EntityLayer (SpaCy sv_core_news_lg, aktiv från v0.1.1)
        context/                 # stub iteration 1, avskaffas i iteration 2
        article9/                # Article9Layer (iteration 2)
        combination/             # CombinationLayer (iteration 2)
        llm/                     # LLMProvider-abstraktion (iteration 2)
    pipeline.py                  # Pipeline
    aggregator.py                # Aggregator
    config.py                    # Aktiva lager, trösklar
evaluation/
    __init__.py
    dataset/
        __init__.py
        labeled_text.py          # LabeledText dataclass
        labeled_finding.py       # LabeledFinding dataclass
        loader.py                # Läser in testdata från JSON
    matcher.py                   # Jämför predikterade fynd mot fasit
    confusion_matrix.py          # ConfusionMatrix
    metrics.py                   # recall(), precision(), f1()
    runner.py                    # Kör pipeline mot dataset
    report.py                    # Sammanställer rapport
tests/
    unit/
        test_betalkort.py
        test_evaluation_flow.py
        test_loader.py
        test_matcher.py
        test_metrics.py
    integration/
        test_end_to_end.py
    dataset/
        test_dataset_offsets.py
    data/
        iteration_1/
            test_dataset.json    # Johannas testdata
pyproject.toml
README.md
```


## 11. Iterationsplan

### Iteration 1 (v15-v17): Mönsterigenkänning

**Bygger:**
- `core/` komplett (Category, Finding, Classification, Layer-protokoll)
- `layers/pattern/` med alla fem recognizers
- `layers/entity/` och `layers/context/` som stubs
- `pipeline.py` och `aggregator.py`
- `evaluation/` komplett

**Utvärderar:**
- Kvantitativt: Konfusionsmatris mot testdata med Artikel 4-kategorier
- Kvalitativt: Demo och semistrukturerad intervju med intressenter

**Förväntade resultat:**
- Hög recall för personnummer (Luhn-validering) och e-post (regex)
- Låg precision (förväntat p.g.a. regex-mönstrens generella natur, bekräftat av Mishra et al.)
- Inga fynd för Artikel 9 (kontextuell analys saknas)

### Iteration 2 (v17-v19): Kontextuell analys och kombinationslogik

**Bygger:**
- `layers/article9/` med Article9Layer (direkt Artikel 9-detektion via lokal LLM)
- `layers/combination/` med CombinationLayer (pusselbitsbedömning)
- `layers/llm/` med LLMProvider-abstraktion (utbytbar lokal/moln-provider, Beslut 17)
- `layers/context/` avskaffas; iteration 1-stubben ersätts av ovanstående lager
- Aggregatorns kombinationslogik: Mekanism 1, Mekanism 3, hög-konfidens-bypass och D5-korrigering (Beslut 19, 20, 21)
- Containment-regel i aggregatorn för cross-recognizer-överlapp (avsnitt 14.1)
- Förbättringar baserat på iteration 1-feedback (Tema B: testdata-utökning med artikel 9-texter och pusselbitseffekt-texter)

**Utvärderar:**
- Kvantitativt: Fullt dataset inklusive artikel 9-texter, pusselbitseffekt-texter och längre realistiska texter. Per-mekanism-rapport från utvärderingsmodulen (Mekanism 1, Mekanism 3, hög-konfidens-bypass-statistik per kategori).
- Kvalitativt: Demo med Lager 3 och Lager 4 plus Mekanism-visualisering i demo-gränssnittet. Semistrukturerad intervju med intressenter (V1, V2, V4) enligt `docs/iteration_2_utvardering.md`.

### Iteration 3 (v19-v21): Förfining och formalisering

**Hanterar:**
- Feedback från designcykel 2:s utvärdering
- Formalisering av designprinciper (Generalized Outcomes)
- Empirisk kalibrering av trösklar (medium_threshold, high_confidence_bypass, min_evidence_count) baserat på iteration 2:s utvärderingsresultat

**Utvärderar:**
- Kvantitativt: Komplett dataset med alla lager aktiva
- Kvalitativt: Slutgiltig demo och intervju


## 12. Beslut att dokumentera i loggboken

Följande designbeslut ska dokumenteras löpande, som råmaterial för designprinciper (delfråga 1.1) och arkitekturell lösning (delfråga 1.2):

- Varför lageruppdelning valdes framför monolitisk klassificering
- Varför alla lager får samma input (parallell pipeline) istället för sekventiell kedja
- Varför överlappande fynd bevaras istället för att filtreras
- Val av recognizer-gränssnitt och dess påverkan på utbytbarhet
- Presidios roll: inspiration (se avsnitt 13)
- Val av matchningsnivå i utvärderingen (span vs dokument)
- Teknikval inom varje lager och motivering
- Beslut om `context.*`-prefix och ORG-kategorisering (full motivering i repots Loggbok)
- Upptäckt av SUC3 vs CoNLL-tagg-konvention i `sv_core_news_lg` (iteration 1, demoförberedelse)
- Beslut 16: Omdisponering av Lager 3 (kontextuell analys) från designcykel 3 till designcykel 2 (full motivering i repots Loggbok)
- Beslut 17 (Loggbok iteration 2): Lokal LLM som primär exekveringsmiljö med utbytbar molnprovider
- Beslut 18 (Loggbok iteration 2): Lager 3 splittas i Article9Layer och CombinationLayer — Single Responsibility Principle
- Beslut 19 (Loggbok iteration 2): Kombinationslogik i CombinationLayer, aggregatorn validerar mekaniskt via Mekanism 1 och Mekanism 3
- Beslut 20 (Loggbok iteration 2): Konfigurerbara trösklar för aggregatorns kombinationslogik (medium_threshold, high_confidence_bypass, min_evidence_count)
- Beslut 21 (Loggbok iteration 2): Privacy by Design som fail-safe-princip i valideringslogiken (GDPR artikel 25)

Dokumentationsformatet ska följa mönstret: *beslut, alternativ som övervägdes, motivering, koppling till GDPR-krav eller empiriskt stöd.*


## 13. Öppna designfrågor

### 13.1 Presidio

Presidio ska inte användas, varken som hela ramverket eller som implementationen bakom lager 1 och 2. Vi ska bygga allt själva men kan använda Presidio som inspiration på grund av dess liknande användningsområde. Den del av Presidio som "motsvarar" vår artefakt heter Presidio Analyzer och identifierar personuppgifter i text utan att klassificera dem enligt GDPR. 

### 13.2 Konfidensaggregering

Ska aggregatorn vikta fynd baserat på konfidens? I iteration 1 är alla fynd binära (regex matchar eller matchar inte). I iteration 2-3, när NER och LLM producerar varierande konfidens, behöver en aggregeringsstrategi fastställas. Alternativ: max-konfidens, viktad summa, enkel tröskel.

### 13.3 Flerkategori-fynd

Kan en textbit tillhöra flera GDPR-kategorier samtidigt? Exempelvis ett namn som också avslöjar etniskt ursprung (Artikel 4 + Artikel 9). Nuvarande modell stöder detta genom att flera fynd kan rapporteras med överlappande span men olika kategorier.


## 14. Kända begränsningar (iteration 1)

Utvärderingen på testdatat i iteration 1 identifierar ett antal falska positiva som inte är buggar i enskilda recognizers eller modeller, utan konsekvenser av hur lagren och deras komponenter interagerar. Begränsningarna grupperas nedan per grundorsak. Ingen av dem åtgärdas i iteration 1; varje block beskriver fenomenet, konkreta exempel från testdatat, rotorsak och planerad åtgärd.

### 14.1 Cross-recognizer-överlapp

Två falska positiva i iteration 1:s utvärdering härrör från cross-recognizer-överlapp. Telefon-recognizern (`pattern.regex_telefon`) matchar siffersekvenser som också ingår i fynd från IBAN-recognizern (`pattern.checksum_iban`), eftersom svenska telefonnummer och IBAN:ens BBAN-segment delar numerisk struktur (sifferblock separerade med mellanslag). Fenomenet är alltså inte en felaktighet i telefon-regexen i isolation, utan en konsekvens av att två recognizers arbetar oberoende på samma text.

Konkret rör det följande två fall i testdatat: textspanet `"0555 5555 55"` matchas som telefonnummer inom IBAN-fyndet `SE96 5000 0000 0555 5555 55`, och textspanet `"05 1234 5678"` matchas som telefonnummer inom IBAN-fyndet `SE05 1234 5678 9012 3456 78`. Båda telefon-fynden ligger helt inneslutna i respektive IBAN-fynd.

Grundorsaken sitter på aggregator-nivå, inte på recognizer-nivå. Varje recognizer i `PatternLayer` är designmässigt oberoende av övriga och känner inte till deras fynd (avsnitt 4.1). Aggregatorn registrerar överlapp mellan fynd i `overlapping_findings` (avsnitt 3.4) men reducerar inte fyndmängden utifrån detta - den beslutar om känslighetsnivå, inte om deduplicering. Telefon-fynden rapporteras därför som fullvärdiga fynd trots att de är inneslutna i ett fynd med högre konfidens.

Begränsningen åtgärdas inte i iteration 1 eftersom en lösning kräver en aktiv reduktionsregel i aggregatorn, vilket är en arkitekturförändring som berör designprincip 3 (spårbarhet): ett filtrerat fynd får inte försvinna tyst utan måste fortfarande vara synligt i utvärderingen. En sådan förändring behöver dessutom diskuteras med intressenter under demon innan den implementeras, eftersom den påverkar vilken bild av artefaktens falska positiva som presenteras.

Planerad åtgärd i iteration 2 (BIE-cykel 2): `Aggregator` utökas med en containment-regel som tar bort ett fynd från `findings` om det är helt inneslutet i ett fynd från en annan recognizer med strikt högre konfidens (till exempel 1.0 över 0.9). Det borttagna fyndet bevaras i `overlapping_findings` så spårbarheten mot designprincip 3 upprätthålls. Samma mekanism föreslås för 14.2:s NER-FPs, eventuellt kompletterad med pre-filtrering; beslut om kombinationen fattas i iteration 2:s planering.

### 14.2 NER modell-feldetekteringar

Entity-lagret (SpaCy `sv_core_news_lg`) producerar i iteration 1:s utvärdering åtta falska positiva som alla har samma grundorsak: modellen triggar på textpositioner där språkliga eller ortografiska signaler liknar det modellen är tränad att känna igen som entiteter, även när den faktiska semantiken inte är en entitet. Till skillnad från cross-recognizer-överlappet (avsnitt 14.1) handlar det inte om interaktion mellan komponenter utan om modellens egenskaper i isolation. Fenomenet är konsistent med Mishra et al. (2025) och Karras et al. (2025): statistiska NER-modeller utan domänspecifik finjustering producerar regelmässigt falska positiva i texttyper som avviker från träningsdistributionen.

Tre underkategorier av feldetekteringar observeras i testdatat. För det första klassar modellen isolerade tokens utan semantisk kontext felaktigt som entiteter; exempel är `"2222"` och `"070"` som labellas som `PRS` (person), samt `"Anna"` utan efternamn som labellas som `PRS`. För det andra klassas domännamn i e-postadresser som organisationer; `anna.svensson@foretag.se` och `lars.berg@privat.se` resulterar i `ORG`-fynd på domändelen. För det tredje klassar modellen numeriska sekvenser som platser i vissa kontexter; `"9001010009"` (ett personnummer utan avgränsare) labellas som `LOC`.

Rotorsaken är att entity-lagret kör oberoende av pattern-lagret (avsnitt 4.1, 5) och saknar pre-filtrering av text som redan har identifierats av strukturerade recognizers. En e-postadress som pattern-lagret har fångat med `confidence=1.0` ses av entity-lagret som fri text, vilket öppnar för feldetektering av domännamn som organisation. Samma arkitektoniska problem som i 14.1 men med omvänd riktning: där 14.1 handlar om att ett lågkonfidens-fynd ligger inuti ett högkonfidens-fynd, handlar 14.2 om att ett nytt lågkonfidens-fynd produceras ovanpå ett redan identifierat högkonfidens-fynd. Planerad åtgärd i iteration 2 är densamma containment-regel som föreslås i 14.1, kompletterad med en pre-filtreringsmekanism som döljer redan-identifierade spans innan entity-lagret analyserar texten. Beslutet om vilken av dessa mekanismer som är primär tas utifrån intressentfeedback under demon.


## 15. Referenser

Buschmann, F., Meunier, R., Rohnert, H., Sommerlad, P. & Stal, M. (1996). *Pattern-Oriented Software Architecture: A System of Patterns*. Chichester: Wiley.

Carrasco, M. (2025). Mitigating Bias and Advocating for Data Sovereignty.

Chaplia, O. & Klym, Y. (2025). Private Microservice with Retrieval-Augmented Generation.

Evans, E. (2003). *Domain-Driven Design: Tackling Complexity in the Heart of Software*. Boston: Addison-Wesley.

Gamma, E., Helm, R., Johnson, R. & Vlissides, J. (1994). *Design Patterns: Elements of Reusable Object-Oriented Software*. Reading: Addison-Wesley.

Gregor, S., Chandra Kruse, L. & Seidel, S. (2020). The Anatomy of a Design Principle. *Journal of the Association for Information Systems*, 21(6), s. 1622-1652.

Gregor, S. & Jones, D. (2007). The Anatomy of a Design Theory. *Journal of the Association for Information Systems*, 8(5), s. 312-335.

Hevner, A.R. (2007). A Three Cycle View of Design Science Research. *Scandinavian Journal of Information Systems*, 19(2), s. 87-92.

Hevner, A.R., March, S.T., Park, J. & Ram, S. (2004). Design Science in Information Systems Research. *MIS Quarterly*, 28(1), s. 75-105.

Karras, C. et al. (2025). LLMs for Cybersecurity.

Mishra, S., Pagare, A. & Sharma, K. (2025). A Hybrid Rule-based NLP Approach for PII Detection.

Opitz, J. (2024). A closer look at classification evaluation metrics. *Transactions of the Association for Computational Linguistics*, 12, s. 820-836.

Sein, M.K., Henfridsson, O., Purao, S., Rossi, M. & Lindgren, R. (2011). Action Design Research. *MIS Quarterly*, 35(1), s. 37-56.

Thaldar, D. (2026). Data Visiting Governance.

Venable, J., Pries-Heje, J. & Baskerville, R. (2016). FEDS: a Framework for Evaluation in Design Science Research. *European Journal of Information Systems*, 25(1), s. 77-89.

Zhan, T. et al. (2025). PRISM: Privacy-Preserving Inference via Sensitivity Mapping.

Zhou, X. et al. (2025). Multi-stage detection for sensitive data.
