# Iteration 1: Planering och arbetsfördelning

**Projekt:** gdpr-classifier  
**Iteration:** 1 (v0.1.0)  
**Period:** v15-v17  
**Metodik:** Scrumban (kanban-board i GitHub Projects)

---

## Repo och miljö

- **Repo:** https://github.com/Abdriano95/gdpr-classifier
- **Branch-strategi:** Jobba direkt på `main`. Committa ofta, korta meddelanden.
- **Stäng issues:** Använd `fixes #N` i commit-meddelanden så uppdateras boarden automatiskt.
- **WIP-gräns:** Max 2 kort i "In progress" per person.

### Miljösetup

```bash
git clone https://github.com/Abdriano95/aegis.git
cd aegis
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest --co -q
```

---

## Arbetsfördelning

### Dag 1: Tillsammans

Parprogrammera `core/`. Det är fyra filer och tar max en timme, men det är grunden som allt annat importerar. Båda måste förstå domänmodellen.

| Issue | Fil | Innehåll |
|-------|-----|----------|
| #1 | `core/category.py` | Category enum (Article 4-kategorier) |
| #2 | `core/finding.py` | Finding dataclass |
| #3 | `core/classification.py` | Classification dataclass + SensitivityLevel |
| #4 | `core/layer.py` | Layer protocol |

**Regel:** Ändra aldrig `core/` utan att den andra vet om det. Om du lägger till en Category eller ändrar ett fält i Finding går den andras kod sönder.

### Abdulla: Pipeline path

Bygg i den här ordningen (varje steg beror på det föregående):

| Steg | Issue | Fil | Vad |
|------|-------|-----|-----|
| 1 | #9 | `layers/pattern/recognizer.py` | Recognizer protocol |
| 2 | #5 | `layers/pattern/recognizers/personnummer.py` | Regex + Luhn-validering |
| 3 | #6 | `layers/pattern/recognizers/email.py` | Regex för e-post |
| 4 | #7 | `layers/pattern/recognizers/telefon.py` | Regex för svenska telefonnummer |
| 5 | #8 | `layers/pattern/recognizers/iban.py` | Regex + mod97 |
| 6 | #10 | `layers/pattern/pattern_layer.py` | Itererar recognizers, samlar fynd |
| 7 | #11 | `layers/entity/entity_layer.py`, `layers/context/context_layer.py` | Stubs, returnerar tom lista |
| 8 | #12 | `pipeline.py` | Kör aktiva lager, samlar findings |
| 9 | #13 | `aggregator.py` | Identifierar överlapp, bestämmer känslighetsnivå |

### Johanna: Evaluation path

Bygg i den här ordningen. Du kan testa allt med fejkade Finding-objekt utan att vänta på Abdullas pipeline.

| Steg | Issue | Fil | Vad |
|------|-------|-----|-----|
| 1 | #14 | `evaluation/dataset/labeled_finding.py` | LabeledFinding dataclass |
| 1 | #14 | `evaluation/dataset/labeled_text.py` | LabeledText dataclass |
| 1 | #14 | `evaluation/dataset/loader.py` | Läser JSON, returnerar list[LabeledText] |
| 2 | #15 | `evaluation/matcher.py` | Jämför predikterade fynd mot fasit (spannivå) |
| 3 | #16 | `evaluation/metrics.py` | recall(), precision(), f1() |
| 4 | #17 | `evaluation/runner.py` | Kör pipeline mot dataset, bygger rapport |
| 5 | #18 | `tests/data/iteration_1/` | Minst 10 texter med personnummer |
| 5 | #19 | `tests/data/iteration_1/` | Minst 5 texter med e-post, telefon, IBAN vardera |
| 5 | #20 | `tests/data/iteration_1/` | Minst 10 okänsliga texter |

Testdata (steg 5) kan byggas parallellt med steg 1-4.

---

## Johanna: Detaljerade instruktioner

### LabeledFinding och LabeledText

```python
# evaluation/dataset/labeled_finding.py
@dataclass(frozen=True)
class LabeledFinding:
    category: Category    # importera från core
    start: int
    end: int
    text_span: str

# evaluation/dataset/labeled_text.py
@dataclass(frozen=True)
class LabeledText:
    text: str
    expected_findings: list[LabeledFinding]
    description: str = ""
```

### Loader

En funktion `load_dataset(path: str) -> list[LabeledText]` som läser JSON. Category-strängen i JSON (t.ex. `"article4.personnummer"`) ska mappas till Category-enumen. Okänd kategori = tydligt felmeddelande.

### Matcher (viktigast)

```python
def match(predicted: list[Finding], expected: list[LabeledFinding]) -> MatchResult
```

MatchResult innehåller:
- `true_positives: list[tuple[Finding, LabeledFinding]]`
- `false_positives: list[Finding]`
- `false_negatives: list[LabeledFinding]`

Matchningsregler:
- Ett predikterat fynd matchar ett fasit-fynd om: samma category OCH överlappande textposition.
- Överlapp = `predicted.start < expected.end AND expected.start < predicted.end`
- Varje fasit-fynd kan bara matchas en gång. Vid dubbletter: ta det med högst confidence.
- Fasit-fynd utan match = FN. Predikterade fynd utan match = FP.

Testa med fejkade findings:

```python
from gdpr_classifier.core.finding import Finding
from gdpr_classifier.core.category import Category

fake = Finding(
    category=Category.PERSONNUMMER,
    start=21, end=32,
    text_span="850101-1234",
    confidence=1.0,
    source="pattern.luhn_personnummer"
)
```

### ConfusionMatrix

Ackumulerar resultat från flera MatchResults. Ska kunna aggregera per kategori och totalt.

### Metrics

Tre rena funktioner. Hantera division med noll genom att returnera 0.0.

```python
def recall(tp: int, fn: int) -> float
def precision(tp: int, fp: int) -> float
def f1(tp: int, fp: int, fn: int) -> float
```

### Runner

```python
def run_evaluation(pipeline, dataset: list[LabeledText]) -> Report
```

Rapporten ska innehålla metriker totalt, per kategori, och per lager (gruppera findings på `source.split(".")[0]`).

### Enhetstester

Skriv i `tests/unit/`:
- `test_matcher.py` (viktigast)
- `test_metrics.py`
- `test_loader.py`

Kör med: `pytest tests/unit/ -v`

---

## Testdata: JSON-format

Fil: `tests/data/iteration_1/test_dataset.json`

```json
[
  {
    "text": "Mitt personnummer är 850101-1234.",
    "description": "Text med personnummer",
    "expected_findings": [
      {
        "category": "article4.personnummer",
        "start": 21,
        "end": 32,
        "text_span": "850101-1234"
      }
    ]
  },
  {
    "text": "Mötet är klockan 14 i rum B.",
    "description": "Okänslig text",
    "expected_findings": []
  }
]
```

Tillgängliga category-värden:
- `article4.personnummer`
- `article4.email`
- `article4.telefonnummer`
- `article4.iban`

Krav på testdata:
- `start` och `end` är teckenpositioner (0-indexerat)
- `text_span` ska vara exakt den sträng som finns på den positionen
- Använd realistiska men syntetiska uppgifter (inga riktiga personnummer)
- Variera kontexten: formella mail, chattmeddelanden, löpande text
- Inkludera edge cases: personnummer utan bindestreck, telefonnummer med mellanslag
- Minst 3 texter med blandad data (flera typer i samma text)

---

## Beroendekarta

```
            ┌──────────────────────┐
            │  #1-4 Core (shared)  │
            └──────────┬───────────┘
                ┌──────┴──────┐
                ▼             ▼
        Abdulla path    Johanna path
                │             │
        #9  Protocol    #14 Loader
                │             │
        #5-8 Recognizers #15 Matcher
                │             │
        #10 PatternLayer #16 Metrics
                │             │
        #11 Stubs        #17 Runner
                │             │
        #12 Pipeline     #18-20 Test data
                │             │
        #13 Aggregator        │
                │             │
                └──────┬──────┘
                       ▼
               Integration test
                       ▼
              Evaluation report
                       ▼
            Demo + intervju (v17)
```

Spåren är helt oberoende efter core/. Johanna testar sin kod med fejkade findings. Synkpunkten är "Integration test" där runner kör pipeline mot testdata.

---

## Synkpunkt: Integration

När båda spåren är klara:

```python
from evaluation.dataset.loader import load_dataset
from evaluation.runner import run_evaluation, print_report
from gdpr_classifier.pipeline import Pipeline
# ... setup pipeline with layers

dataset = load_dataset("tests/data/iteration_1/test_dataset.json")
report = run_evaluation(pipeline, dataset)
print_report(report)
```

Om något inte matchar beror det på att Finding-formatet skiljer sig, men det ska inte hända eftersom båda importerar från samma `core/`.

---

## Iteration 1: Förväntade resultat

- Hög recall för personnummer (Luhn-validering) och e-post (regex)
- Låg precision (förväntat, regex ger falska positiva - bekräftat av Mishra et al.)
- Inga fynd för Artikel 9 (lager 2 och 3 är stubs)
- Det låga precision-resultatet motiverar lager 2 (NER) i iteration 2

---

## Loggbok

Dokumentera löpande i loggboken, i formatet: beslut, alternativ som övervägdes, motivering, koppling till GDPR-krav eller empiriskt stöd.

Saker att dokumentera:
- Varför lageruppdelning valdes framför monolitisk klassificering
- Varför alla lager får samma input (parallell) istället för sekventiell kedja
- Varför överlappande fynd bevaras istället för att filtreras
- Val av recognizer-gränssnitt och dess påverkan på utbytbarhet
- Val av matchningsnivå i utvärderingen (span vs dokument)
- Teknikval inom varje lager och motivering

---

## Agent-sessionslogg

### Regel

**Varje agent (AI eller människa) som arbetar i en session ska logga sin session här efter avslutad iteration.** Loggen är komplement till Loggboken ovan: Loggboken dokumenterar *beslut och motiveringar*, medan sessionsloggen dokumenterar *vad som faktiskt gjordes, i vilken ordning, och av vem*. Syftet är spårbarhet och att nästa agent (eller granskare) snabbt ska kunna förstå repots historik utan att läsa hela git-loggen.

### Format

Lägg till en ny post längst ner. Använd följande mall:

```markdown
### Session YYYY-MM-DD - [Agent/Person]

**Iteration:** [t.ex. 1 / v0.1.0]
**Mål:** [en mening om vad sessionen skulle åstadkomma]

**Ändrade filer:**
- `path/till/fil.py` - [kort beskrivning]

**Gjort:**
- [punkt per konkret åtgärd]

**Beslut fattade:** [kort; länka till Loggboken om längre motivering behövs]
**Öppet/Nästa steg:** [vad som återstår eller blockerar]
```

### Regler för loggning

1. Logga **efter varje iteration** (eller efter en sammanhållen arbetssession om iterationen sträcker sig över flera dagar).
2. En post per session, inte per commit.
3. Håll det kort: punktlistor, inga resonemang (de hör hemma i Loggboken).
4. Ändra aldrig tidigare poster. Lägg till en ny post om något behöver korrigeras.
5. Om sessionen genererade arkitekturbeslut ska dessa även föras in i Loggboken med full motivering.

### Poster

#### Session 2026-04-17 - Cursor agent (Opus 4.7)

**Iteration:** 1 (v0.1.0), dag 1
**Mål:** Implementera core-domänmodellen (Issues #1-#4) och synka arkitekturdokumentet.

**Ändrade filer:**
- `gdpr_classifier/core/category.py` - `Category(str, Enum)` med Artikel 4-värden, Artikel 9-platshållare och `KONTEXTUELLT_KANSLIG`.
- `gdpr_classifier/core/finding.py` - fryst `Finding`-dataclass enligt spec.
- `gdpr_classifier/core/classification.py` - `SensitivityLevel` (`NONE`/`LOW`/`MEDIUM`/`HIGH`) och fryst `Classification`-dataclass.
- `gdpr_classifier/core/layer.py` - `Layer` som `typing.Protocol` med `@runtime_checkable`.
- `gdpr_classifier/core/__init__.py` - publika re-exporter via `__all__`.
- `docs/arkitektur.md` - uppdaterad enum-definition i 3.3 och `_determine_sensitivity`-docstring i avsnitt 8 för att spegla `MEDIUM`.

**Gjort:**
- Ersatte fyra docstring-endast filer under `gdpr_classifier/core/` med faktiska implementationer, stdlib-only, `from __future__ import annotations` i varje fil.
- Lade till `SensitivityLevel.MEDIUM = "medium"` för indirekta identifierare / kombinationer (pusselbitseffekten).
- Synkade `docs/arkitektur.md` så dokument och kod stämmer överens.
- Inga tester skrivna (per instruktion - hör till senare issues).

**Beslut fattade:**
- `SensitivityLevel` ärver från `str, Enum` (matchar `Category`, ger JSON-serialiserbarhet utan extra kod).
- `Layer` implementerad som `@runtime_checkable Protocol` i stället för ABC (strukturell typning, låter externa klasser uppfylla kontraktet utan arv).
- Tillägget av `MEDIUM` motiveras i Loggboken (pusselbitseffekten: indirekta identifierare som i kombination ökar identifieringsrisken).

**Öppet/Nästa steg:**
- Abdulla: påbörja pipeline-spåret, steg 1 (Issue #9, `layers/pattern/recognizer.py`).
- Johanna: påbörja evaluation-spåret, steg 1 (Issue #14, dataset-moduler).
- Loggboken behöver en post som motiverar `MEDIUM`-nivån formellt (pusselbitseffekten, empiriskt stöd).

