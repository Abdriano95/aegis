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

#### Session 2026-04-17 - Antigravity agent (Gemini 3.1 Pro (High))

**Iteration:** 1 (v0.1.0), dag 1
**Mål:** Implementera evaluation dataset-modeller och loader samt tester (Issue #14).

**Ändrade filer:**
- `evaluation/dataset/labeled_finding.py` - Skapade `LabeledFinding` dataclass.
- `evaluation/dataset/labeled_text.py` - Skapade `LabeledText` dataclass.
- `evaluation/dataset/loader.py` - Implementerade `load_dataset` för JSON-inläsning.
- `evaluation/dataset/__init__.py` - Lade till publika re-exporter.
- `tests/unit/test_loader.py` - Implementerade enhetstester för inläsningen av testdata.
- `docs/iteration_1_planering.md` - Lade till denna sessionslogg.

**Gjort:**
- Skapat frysta dataklasser för utvärderingsfasit så att de kan användas med matchningslogik senare.
- Loadern validerar korrekt json och höjer `ValueError` vid inmatning av felaktiga kategorier baserat på `Category` enum från godkänd core struktur.
- Enhetstest skrivna och verifierade via pytest. Inga konstigheter eller omdesigningar behövdes. 

**Beslut fattade:**
- Inga större nya konventionella eller arkitekturella byten. Gjorde rakt enligt arkitektur.md och specifikationen (inga avvikelser från SSOT).

**Öppet/Nästa steg:**
- Johanna: fortsätt med evaluation-spåret, steg 2 (Issue #15, `evaluation/matcher.py`).

#### Session 2026-04-17 - Cursor agent (Opus 4.7)

**Iteration:** 1 (v0.1.0), pipeline-spåret steg 1
**Mål:** Implementera Recognizer-protokollet (Issue #9) som kontrakt för lager 1:s mönsterigenkännare.

**Ändrade filer:**
- `gdpr_classifier/layers/pattern/recognizer.py` - `Recognizer` som `typing.Protocol` med `@runtime_checkable`, properties `category` och `source_name`, metod `recognize(text) -> list[Finding]`.
- `gdpr_classifier/layers/pattern/__init__.py` - re-exporterar `Recognizer` via `__all__`.

**Gjort:**
- Implementerade protokollet enligt `docs/arkitektur.md` avsnitt 4.1, samma mönster som `core/layer.py` (stdlib only, `from __future__ import annotations`, korta member-docstrings).
- Importerade `Category` och `Finding` från `gdpr_classifier.core` - inga duplicerade typer.
- Verifierade `from gdpr_classifier.layers.pattern import Recognizer` (OK) och `ReadLints` (rena).
- Inga ändringar i `core/` eller `docs/arkitektur.md` - dokumentet matchade redan koden.
- Inga tester skrivna (egna issues).

**Beslut fattade:**
- `source`-strängen på `Finding` byggs av recognizern själv (alternativ 2 i issue-specen), t.ex. `"pattern.luhn_personnummer"`. `source_name` förblir den lager-lokala identifieraren för spårbarhet/registerlogik. Motivering: protokollets kontrakt är `recognize(text) -> list[Finding]`, så recognizern konstruerar redan `Finding`-objekten - alternativ 1 hade krävt post-processing i `PatternLayer`. Valet är dokumenterat i module-docstringen i `recognizer.py` så att Issues #5-#8 och #10 har ett tydligt kontrakt.

**Öppet/Nästa steg:**
- Issue #5: `recognizers/personnummer.py` (regex + Luhn-validering, `source="pattern.luhn_personnummer"`).
- Issues #6-#8: e-post, telefon, IBAN-recognizers.
- Issue #10: `PatternLayer` som itererar registrerade recognizers och konkatenerar findings.

#### Session 2026-04-17 - Antigravity agent (Gemini 3.1 Pro (High))

**Iteration:** 1 (v0.1.0), dag 1
**Mål:** Implementera matchningslogik och enhetstester (Issue #15).

**Ändrade filer:**
- `evaluation/matcher.py` - Definierade `MatchResult` och implementerade `match`-funktionen.
- `evaluation/__init__.py` - Re-exporterade publikt `MatchResult` och `match`.
- `tests/unit/test_matcher.py` - Omfattande enhetstester för alla matchningsregler.
- `docs/iteration_1_planering.md` - Lade till denna sessionslogg.

**Gjort:**
- Skapat logik för att utvärdera modellens funna data mot förväntad LabeledFinding på spann-nivå.
- Hanterat greedy match med avseende på överlappande spann för konfidensvärden (högst vinner, lägst blir False Positive).
- Enhetstest verifierar hantering av exakt överlapp, partiell överlapp, misstapade kategorier, helt felplacerade detektioner samt dubblett-problematiken med konfidens.
- Tester och lints ok.

**Beslut fattade:**
- Vald en girig heuristik för matchning där `predicted` sorteras på konfidens nedåtgående och den förväntade listan itereras för check med `id()` – ett säkrare och effektivare alternativ än komplexa dubbelriktade map-strukturer.
- `MatchResult` representeras som en `frozendataclass` precis i linje med projektets övriga output-strukturer.

**Öppet/Nästa steg:**
- Johanna: fortsätt med evaluation-spåret, steg 3 (Issue #16, `evaluation/metrics.py`).

#### Session 2026-04-17 - Antigravity agent (Gemini 3.1 Pro (High))

**Iteration:** 1 (v0.1.0), dag 1
**Mål:** Implementera metriker för utvärdering (Issue #16).

**Ändrade filer:**
- `evaluation/metrics.py` - Implementerade funktionerna `recall`, `precision` och `f1`.
- `evaluation/__init__.py` - Re-exporterade de nya funktionerna i `__all__`.
- `tests/unit/test_metrics.py` - Skapade enhetstester för alla funktioner, med täckning för 0-division.
- `docs/iteration_1_planering.md` - Lade till denna sessionslogg.

**Gjort:**
- Skapat funktioner för Recall, Precision och F1.
- Inkluderat hantering av ZeroDivisionError via exakta `denominator == 0` kontroller, enligt specifikationen.
- Samtliga testfall implementerade och verifierade via `pytest`.

**Beslut fattade:**
- Följer exakt den angivna specifikationen för division med noll utan undantag (returnerar `0.0`).

**Öppet/Nästa steg:**
- Johanna: fortsätt med evaluation-spåret, steg 4 (Issue #17, `evaluation/runner.py`).

#### Session 2026-04-17 - Cursor agent (Opus 4.7)

**Iteration:** 1 (v0.1.0), pipeline-spåret steg 2
**Mål:** Implementera `PersonnummerRecognizer` (Issue #5) med regex-matchning, datumvalidering och Luhn-kontroll.

**Ändrade filer:**
- `gdpr_classifier/layers/pattern/recognizers/personnummer.py` - `PersonnummerRecognizer` (stdlib `re` + Luhn + datumvalidering, emitterar `Finding` med `source="pattern.luhn_personnummer"` och `confidence=1.0`).
- `gdpr_classifier/layers/pattern/recognizers/__init__.py` - re-exporterar `PersonnummerRecognizer` via `__all__`.
- `docs/arkitektur.md` - avsnitt 4.2 uppdaterat: personnummer-recognizern emitterar endast Luhn-validerade träffar (0.7-konfidensvägen för formatmatch utan validering är borttagen i iteration 1).

**Gjort:**
- En kompilerad regex med ordnad alternation (längst först: 12-siffror, 8+sep, 10-siffror, 6+sep) och `(?<!\d)`/`(?!\d)`-vakter för att undvika matchning mitt i längre siffersekvenser (t.ex. kreditkort).
- Separator `-` och `+` stöds. Århundradeprefixet (2 eller 4 inledande siffror) normaliseras bort; datum- och Luhn-kontroll körs på de sista 10 siffrorna.
- Datumvalidering: månad 1-12, dag 1-31 eller 61-91 (samordningsnummer). Ingen per-månads-dagsräkning (rimlighetskontroll enligt spec).
- Luhn: dubblar varannan siffra från vänster, -9 om resultatet > 9, giltig vid sum % 10 == 0.
- `Finding` byggs med `start`/`end` från `match.start(1)`/`match.end(1)` och `text_span` som den exakta råsträngen.
- Inga tester skrivna (egna issues).

**Beslut fattade:**
- Avvikelse från tidigare formulering i `arkitektur.md` avsnitt 4.2: issue #5 kräver att endast Luhn-validerade träffar emitteras, så 0.7-vägen är borttagen för iteration 1. Motivering: en format-bara-match utan checksum är i praktiken en falsk positiv; iteration 1 prioriterar recall på validerade nummer utan att späda ut precisionen med osäkra kandidater.
- Issue-beskrivningens påstående att `850101-1234` är ett giltigt personnummer är felaktigt (Luhn-summa = 28). Det korrekta giltiga exemplet för samma datum/serienummer är `850101-1236` (Luhn-summa = 30). Implementationen följer algoritmen, inte det felaktiga exemplet.

**Öppet/Nästa steg:**
- Issue #6: `recognizers/email.py` (regex för e-post).
- Issue #7: `recognizers/telefon.py` (regex för svenska telefonnummer).
- Issue #8: `recognizers/iban.py` (regex + mod97).
- Issue #10: `PatternLayer` som itererar registrerade recognizers.


#### Session 2026-04-17 - Antigravity agent (Gemini 3.1 Pro (High))

**Iteration:** 1 (v0.1.0), dag 1
**Mål:** Implementera rapportgenerator, confusion matrix och utvärderingsrunner (Issue #17).

**Ändrade filer:**
- `evaluation/confusion_matrix.py` - Implementerade `ConfusionMatrix` för ackumulering av TP/FP/FN.
- `evaluation/report.py` - Skapade dataklasserna `RunMetrics` och `Report`, samt `print_report`.
- `evaluation/runner.py` - Implementerade `run_evaluation` som orkestrerar klassificering, matchning och resultatsammanställning.
- `evaluation/__init__.py` - Uppdaterade re-exporterna.
- `tests/unit/test_evaluation_flow.py` - Lade till enhetstester för aggregering och runnern.
- `docs/arkitektur.md` - Uppdaterade dokumentet för att notera att True Negatives (TN) utelämnas från ConfusionMatrix.

**Gjort:**
- Alla tre angivna dimensioner implementerades (totalt, kategori, lager).
- Rapporten formatkodades i enkla f-strängar enligt feedback.
- Pytest körda framgångsrikt (100% pass för validering).

**Beslut fattade:**
- Lagerspecifika falska negativa (FN) avsänds inte aktivt / ignoreras då individuella lager inte utvidgas till hela taxonomin. Detta resonemang bekräftades av uppdragsgivaren och stäms av som konvention.
- True Negatives (TN) ströks från arkitekturen kring spann-klassificeringen.

**Öppet/Nästa steg:**
- Johanna: Skapa testdata (Issue #18 - #20).

#### Session 2026-04-17 - Cursor agent (Opus 4.7)

**Iteration:** 1 (v0.1.0), pipeline-spåret steg 3
**Mål:** Implementera `EmailRecognizer` (Issue #6) som regex-baserad recognizer för e-postadresser.

**Ändrade filer:**
- `gdpr_classifier/layers/pattern/recognizers/email.py` - `EmailRecognizer` (stdlib `re`, case-insensitive regex, emitterar `Finding` med `source="pattern.regex_email"` och `confidence=1.0`).
- `gdpr_classifier/layers/pattern/recognizers/__init__.py` - re-exporterar `EmailRecognizer` via `__all__` (alfabetisk ordning).

**Gjort:**
- Kompilerad regex `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` med `re.IGNORECASE` - täcker punkt, bindestreck, understreck och plus i local part, domän med minst en punkt och TLD på minst 2 bokstäver.
- `Finding` byggs med `match.start()`/`match.end()`/`match.group()` i en loop över `finditer`, analogt med `personnummer.py`-mönstret.
- Avslutande interpunktion (t.ex. `"anna@test.se."`) hamnar inte i spanet eftersom TLD-delen `[a-zA-Z]{2,}` bara accepterar bokstäver; regex-motorns backtracking stannar på sista bokstavsgruppen.
- `ReadLints` rena på båda filerna. Inga tester skrivna (egna issues).
- Inga ändringar i `core/` eller `docs/arkitektur.md` - avsnitt 4.2 matchade redan koden (`source="pattern.regex_email"`, `confidence=1.0`).

**Beslut fattade:**
- Inga avvikelser från SSOT. Följde exakt samma filstruktur, import-ordning och klassmönster som `PersonnummerRecognizer` för konsistens inom `recognizers/`-paketet.
- `re.IGNORECASE` adderad trots att regex-teckenklasser redan täcker båda casen - defensiv mot framtida förenklingar av mönstret.

**Öppet/Nästa steg:**
- Issue #7: `recognizers/telefon.py` (regex för svenska telefonnummer, `source="pattern.regex_telefon"`, `confidence=0.9`).
- Issue #8: `recognizers/iban.py` (regex + mod97, `source="pattern.checksum_iban"`).
- Issue #10: `PatternLayer` som itererar registrerade recognizers.

#### Session 2026-04-17 - Antigravity agent (Gemini 3.1 Pro (High))

**Iteration:** 1 (v0.1.0), dag 1
**Mål:** Skapa slutgiltigt testdataset (JSON) för Iteration 1 (Issue #18, #19, #20).

**Ändrade filer:**
- `tests/data/iteration_1/test_dataset.json` - Skapade 40 st testfall med 0-baserade exakta index för testning av mönsterigenkänning.

**Gjort:**
- Skapade ett temporärt Python-skript för att bygga datan, beräkna teckenindex och validera strängar med `assert` för att undvika "off-by-one"-fel.
- Genererade testfall med fördelning: 10 personnummer, 5 e-post, 5 telefonnummer, 5 IBAN, 4 blandad känslig data, samt 11 okänsliga texter.
- Inkluderade edge-cases (olika mönster, landsnummer, okänslig kontext och parenteser) enligt specifikation.
- Utförde ingen commit, enligt instruktioner.

**Beslut fattade:**
- Valde systemgenererad JSON (via scratch-skript) i stället för manuell strängräkning för att garantera att de 0-baserade teckenindexen (för tecken som åäö) blev hundraprocentigt korrekta in i det sista.

**Öppet/Nästa steg:**
- Synkpunkten: När pipeline-spåret (Issue #10, #12) är klart kan det första integrationstestet köras med detta testdataset!

#### Session 2026-04-17 - Cursor agent (Opus 4.7)

**Iteration:** 1 (v0.1.0), pipeline-spåret steg 4
**Mål:** Implementera `TelefonRecognizer` (Issue #7) som regex-baserad recognizer för svenska telefonnummer.

**Ändrade filer:**
- `gdpr_classifier/layers/pattern/recognizers/telefon.py` - `TelefonRecognizer` (stdlib `re`, emitterar `Finding` med `source="pattern.regex_telefon"` och `confidence=0.9`).
- `gdpr_classifier/layers/pattern/recognizers/__init__.py` - re-exporterar `TelefonRecognizer` via `__all__` (alfabetisk ordning: Email, Personnummer, Telefon).
- `docs/iteration_1_planering.md` - denna sessionslogg.

**Gjort:**
- Kompilerad regex `(?<![\d+])(?:\+46|0046|0)[-\s]?[1-9](?:[-\s]?\d){6,8}(?!\d)` - täcker domestikt format (`0XX...`), internationellt (`+46...`) och dubbelnolla (`0046...`), med valfria bindestreck/mellanslag som separatorer mellan siffergrupper.
- Prefix-alternation ordnad längst först (`\+46 | 0046 | 0`) så att `0046`-prefix inte felaktigt konsumeras av domestik-branchen.
- Första siffran efter prefix begränsad till `[1-9]` (inga extra inledande nollor), resterande 6-8 siffror ger totalt 7-9 abonnentsiffror efter prefix - motsvarar svenska nummers totala längd på 8-10 siffror.
- `(?<![\d+])`/`(?!\d)`-vakter hindrar matchning mitt i längre siffersekvenser, samma idé som `personnummer.py`.
- `Finding` byggs med `match.start()`/`match.end()`/`match.group()` analogt med `email.py`-mönstret.
- Manuell verifiering mot DoD-fallen: `070-123 45 67`, `0701234567`, `+46701234567`, `+46 70 123 45 67`, `08-123 456 78`, `0046 70 123 45 67`, `+46-70-123-45-67` → alla matchar som förväntat. `rum 307 pa klockan 0800` och tom sträng → inga träffar. Text med två nummer → två separata findings.
- `ReadLints` rena på båda ändrade filerna. Inga tester skrivna (egna issues).
- Inga ändringar i `core/` eller `docs/arkitektur.md` - avsnitt 4.2 matchade redan koden (`source="pattern.regex_telefon"`, `confidence=0.9`).

**Beslut fattade:**
- Inga avvikelser från SSOT. Följde exakt samma filstruktur, import-ordning och klassmönster som `EmailRecognizer`/`PersonnummerRecognizer` för konsistens inom `recognizers/`-paketet.
- Valde en enhetlig regex med prefix-alternation i stället för flera separata mönster i alternation - ger kortare/tydligare kod och samma täckning. Accepterar vissa falska positiver (t.ex. `01234567` i fritext) vilket motiverar `confidence=0.9` i stället för 1.0.
- Telefon-recognizern filtrerar inte bort personnummer-liknande spann; enligt issue-beskrivningen är det aggregatorns ansvar att hantera överlapp.

**Öppet/Nästa steg:**
- Issue #8: `recognizers/iban.py` (regex + mod97, `source="pattern.checksum_iban"`).
- Issue #10: `PatternLayer` som itererar registrerade recognizers.

#### Session 2026-04-17 - Cursor agent (Opus 4.7)

**Iteration:** 1 (v0.1.0), pipeline-spåret steg 5
**Mål:** Implementera `IbanRecognizer` (Issue #8) som regex + ISO 7064 mod97-baserad recognizer för IBAN-nummer.

**Ändrade filer:**
- `gdpr_classifier/layers/pattern/recognizers/iban.py` - `IbanRecognizer` (stdlib `re` + mod97, emitterar `Finding` med `source="pattern.checksum_iban"` och `confidence=1.0`).
- `gdpr_classifier/layers/pattern/recognizers/__init__.py` - re-exporterar `IbanRecognizer` via `__all__` (alfabetisk ordning: Email, Iban, Personnummer, Telefon).
- `docs/iteration_1_planering.md` - denna sessionslogg.

**Gjort:**
- Kompilerad regex `(?<![A-Za-z0-9])[A-Za-z]{2}\d{2}(?:[ ]?[A-Za-z0-9]){10,30}(?![A-Za-z0-9])` - matchar landskod (2 bokstäver) + 2 kontrollsiffror + 10-30 alfanumeriska BBAN-tecken med valfritt enskilt mellanslag mellan varje BBAN-tecken. Täcker både kompakt form (`SE3550000000054910000003`) och 4-grupperad form (`SE35 5000 0000 0549 1000 0003`).
- Teckenklasser hanterar case direkt (ingen `re.IGNORECASE`); validering görs på en separat uppercasad och space-strippad kopia så `text_span` bevaras exakt som skrivet.
- Boundary-vakter `(?<![A-Za-z0-9])`/`(?![A-Za-z0-9])` hindrar matchning inuti längre alfanumeriska tokens, samma idé som `(?<!\d)`/`(?!\d)` i `personnummer.py`.
- Litteralt mellanslag `[ ]?` (ej `\s`) så matchningen inte korsar nyradstecken.
- Privat `_mod97_valid(iban: str) -> bool`: flyttar första 4 tecken till slutet, ersätter bokstäver med numeriskt värde (A=10..Z=35 via `ord(c) - 55`), konverterar till `int` och returnerar `% 97 == 1`. Defensiv fallback `return False` om ett oväntat tecken skulle slinka igenom.
- Längdkontroll `15 <= len(normalized) <= 34` innan mod97 - defensiv mot regex-quirks, bevarar korrekt IBAN-intervall enligt specifikation.
- `Finding` byggs med `match.start()`/`match.end()`/`match.group()` analogt med `email.py`/`telefon.py`-mönstret; `text_span` är råsträngen med originalmellanslag.
- Manuell verifiering mot DoD: `SE3550000000054910000003` (mod97=1), `SE35 5000 0000 0549 1000 0003` (spaced, samma IBAN, mod97=1), `DE89370400440532013000` (mod97=1) matchar. `SE0000000000000000000000` matchar regex men mod97=3 → filtreras bort. IBAN mitt i mening ("Betala till SE35... senast fredag") plockas upp via boundary-vakter. Tom text eller text utan IBAN → tom lista.
- `ReadLints` rena på båda ändrade filerna. Inga tester skrivna (egna issues).
- Inga ändringar i `core/` eller `docs/arkitektur.md` - avsnitt 4.2 matchade redan koden (`source="pattern.checksum_iban"`, `confidence=1.0`).

**Beslut fattade:**
- Inga avvikelser från SSOT. Följde exakt samma filstruktur, import-ordning och klassmönster som `PersonnummerRecognizer`/`EmailRecognizer`/`TelefonRecognizer` för konsistens inom `recognizers/`-paketet.
- Valde `(?:[ ]?[A-Za-z0-9]){10,30}` i stället för explicit 4-char-gruppering - enklare mönster som accepterar både standardformateringen (mellanslag var 4:e tecken) och godtycklig formatering, och förlitar sig på mod97 för slutgiltig validering. Greedy-backtracking hittar korrekt slut via `(?![A-Za-z0-9])`-vakten.
- Konvertering A-Z via `ord(c) - 55` direkt i mod97-hjälparen (operates on pre-normalized uppercase input) i stället för en separat tabell - kortare, lika läsbart, matchar algoritmens matematiska definition.

**Öppet/Nästa steg:**
- Issue #10: `PatternLayer` som itererar registrerade recognizers och konkatenerar findings.

#### Session 2026-04-17 - Cursor agent (Opus 4.7)

**Iteration:** 1 (v0.1.0), pipeline-spåret steg 6
**Mål:** Implementera `PatternLayer` (Issue #10) som uppfyller `Layer`-protokollet och delegerar till de fyra registrerade recognizers.

**Ändrade filer:**
- `gdpr_classifier/layers/pattern/pattern_layer.py` - `PatternLayer` (stdlib only, default-recognizers via `__init__(recognizers=None)`, `name="pattern"`, `detect(text)` konkatenerar findings).
- `gdpr_classifier/layers/pattern/__init__.py` - re-exporterar `PatternLayer` via `__all__` (alfabetisk ordning: `PatternLayer`, `Recognizer`).
- `docs/iteration_1_planering.md` - denna sessionslogg.

**Gjort:**
- Implementerade `PatternLayer` enligt `docs/arkitektur.md` avsnitt 3.2 och 4.1: layern äger ingen detektionslogik själv, utan itererar över registrerade recognizers och slår ihop deras `list[Finding]` till en enda lista.
- Default-konstruktion `PatternLayer()` instansierar alla fyra recognizers i ordningen Personnummer, Email, Telefon, IBAN - deterministisk men semantiskt irrelevant (aggregatorn sorterar).
- Konstruktorn accepterar `list[Recognizer] | None` så att tester och konfigurationer kan injicera en delmängd, t.ex. `PatternLayer([PersonnummerRecognizer()])`.
- Recognizer-listan kopieras med `list(recognizers)` för att undvika aliasing med uppringarens lista.
- `detect` bygger en lokal `findings: list[Finding]`, kör `extend` per recognizer och returnerar. Ingen sortering, filtrering eller dedup - det är aggregatorns ansvar (avsnitt 3.4).
- Uppfyller `Layer`-protokollets runtime-checkable kontrakt (property `name`, metod `detect(text) -> list[Finding]`).
- `ReadLints` rena på båda ändrade filerna. Inga tester skrivna (egna issues).
- Inga ändringar i `core/` eller `docs/arkitektur.md` - avsnitt 3.2 och 4.1 matchade redan koden.

**Beslut fattade:**
- Inga avvikelser från SSOT. Default-recognizers motsvarar iteration 1:s fyra Artikel 4-kategorier exakt.
- Valde att importera recognizer-klasserna på modulnivå (inte lazy) - de är redan laddade via `recognizers/__init__.py` och eager-import ger tydligare fel om någon klass saknas.

**Öppet/Nästa steg:**
- Issue #11: `layers/entity/entity_layer.py` och `layers/context/context_layer.py` som stubs (returnerar tom lista).
- Issue #12: `pipeline.py` som kör aktiva lager.
- Issue #13: `aggregator.py`.

#### Session 2026-04-17 - Cursor agent (Opus 4.7)

**Iteration:** 1 (v0.1.0), pipeline-spåret steg 7
**Mål:** Implementera `EntityLayer` och `ContextLayer` (Issue #11) som stubs som uppfyller `Layer`-protokollet och returnerar tom lista, så pipelinen kan instansiera alla tre lager utan fel i iteration 1.

**Ändrade filer:**
- `gdpr_classifier/layers/entity/entity_layer.py` - `EntityLayer` (stdlib only, `name="entity"`, `detect(text)` returnerar `[]`).
- `gdpr_classifier/layers/entity/__init__.py` - re-exporterar `EntityLayer` via `__all__`.
- `gdpr_classifier/layers/context/context_layer.py` - `ContextLayer` (stdlib only, `name="context"`, `detect(text)` returnerar `[]`).
- `gdpr_classifier/layers/context/__init__.py` - re-exporterar `ContextLayer` via `__all__`.
- `docs/iteration_1_planering.md` - denna sessionslogg.

**Gjort:**
- Skapade minimala stubs enligt `docs/arkitektur.md` avsnitt 5 (NER, iteration 2) och avsnitt 6 (kontextuell analys, iteration 3), båda redan dokumenterade som "Stub i iteration 1. Returnerar tom lista."
- Båda klasserna följer samma mönster som `PatternLayer`: `@property name` + `detect(text) -> list[Finding]`. Inga konstruktorargument behövs för stubs.
- `Finding` importeras från `gdpr_classifier.core` (samma import-stil som `pattern_layer.py`).
- Module-docstrings innehåller frasen "Stub for iteration 1" enligt spec, och pekar ut vad den framtida implementationen ska göra samt tillhörande avsnitt i arkitektur.md.
- Verifierat med en liten runtime-check: `isinstance(EntityLayer(), Layer)` och `isinstance(ContextLayer(), Layer)` returnerar `True`; båda `detect("x")` returnerar `[]`; `name`-property:erna returnerar `"entity"` respektive `"context"`.
- `ReadLints` rena på alla fyra ändrade filerna. Inga tester skrivna (egna issues).
- Inga ändringar i `core/` eller `docs/arkitektur.md` - avsnitt 5 och 6 matchade redan koden.

**Beslut fattade:**
- Inga avvikelser från SSOT. Strikt minimal stub-implementation enligt issue-specen; ingen spekulativ NER-/zero-shot-struktur i förväg.
- Stubs implementeras som vanliga klasser (inte ABC eller Protocol) eftersom de ska *uppfylla* `Layer`-protokollet, inte definiera ett nytt kontrakt.

**Öppet/Nästa steg:**
- Issue #12: `pipeline.py` som kör aktiva lager.
- Issue #13: `aggregator.py`.

#### Session 2026-04-17 - Cursor agent (Opus 4.7)

**Iteration:** 1 (v0.1.0), pipeline-spåret steg 8
**Mål:** Implementera `Pipeline` (Issue #12) som ren orkestrerare: kör alla aktiva lager mot indatan, samlar findings och delegerar till aggregatorn.

**Ändrade filer:**
- `gdpr_classifier/pipeline.py` - `Pipeline` (stdlib only, `classify(text) -> Classification`, duck-typad `Aggregator` via `TYPE_CHECKING`-guard).
- `gdpr_classifier/__init__.py` - re-exporterar `Pipeline` via `__all__` så `from gdpr_classifier import Pipeline` fungerar.
- `docs/iteration_1_planering.md` - denna sessionslogg.

**Gjort:**
- Implementerade `Pipeline` exakt enligt `docs/arkitektur.md` avsnitt 7: `__init__(layers, aggregator)` sparar båda attributen; `classify(text)` itererar `self.layers`, `extend`ar findings och returnerar `self.aggregator.aggregate(findings=..., active_layers=[l.name for l in self.layers])`.
- Ingen klassificeringslogik i Pipeline - ingen sortering, dedup, sensitivity-bedömning eller överlappshantering. Allt sådant är aggregatorns ansvar (avsnitt 8).
- `Aggregator`-beroendet löst via duck typing + `TYPE_CHECKING`-guard så Pipeline kan skrivas innan Issue #13 är klar utan runtime-import av den ännu obefintliga `gdpr_classifier.aggregator`. Annotationen `aggregator: Aggregator` är giltig tack vare `from __future__ import annotations` (PEP 563: annotationer utvärderas aldrig vid runtime).
- Defensiv kopia `self.layers = list(layers)` så att uppringarens lista inte kan muteras av Pipeline - samma mönster som `PatternLayer.__init__` använder för recognizers.
- `ReadLints` rena på båda ändrade filerna. Inga tester skrivna (egna issues).
- Inga ändringar i `core/` eller `docs/arkitektur.md` - avsnitt 7 innehåller redan exakt den klasskropp som implementerades (rad 278-293), inget att synka.

**Beslut fattade:**
- Duck typing för `Aggregator` (inte en ny `Protocol`) enligt issuens "Välj det enklare alternativet". `TYPE_CHECKING`-importen bevarar läsbarhet och IDE-stöd utan att tvinga fram ett kontrakt innan aggregatorn finns.
- `Pipeline` re-exporteras från pakettoppen eftersom det är systemets publika entry point (arkitektur.md avsnitt 7), konsistent med hur `core/__init__.py` exponerar domän-primitiverna.

**Öppet/Nästa steg:**
- Issue #13: `aggregator.py` - `aggregate(findings, active_layers) -> Classification`, `_find_overlaps`, `_determine_sensitivity` enligt arkitektur.md avsnitt 8.

#### Session 2026-04-17 - Cursor agent (Opus 4.7)

**Iteration:** 1 (v0.1.0), pipeline-spåret steg 9
**Mål:** Implementera `Aggregator` (Issue #13) så `Pipeline` kan köra end-to-end: hitta överlappande fynd, avgöra känslighetsnivå och returnera en `Classification`.

**Ändrade filer:**
- `gdpr_classifier/aggregator.py` - `Aggregator` (stdlib only, `aggregate`, `_find_overlaps` via `itertools.combinations`, `_determine_sensitivity` via `article9.`/`context.`-prefix på `Category.value`).
- `gdpr_classifier/__init__.py` - re-exporterar `Aggregator` i `__all__` bredvid `Pipeline` (alfabetisk ordning).
- `docs/arkitektur.md` - avsnitt 8 utökat med iteration 1-not: `MEDIUM` är definierad i `SensitivityLevel` men tilldelas inte förrän `ContextLayer` finns i iteration 3.
- `docs/iteration_1_planering.md` - denna sessionslogg.

**Gjort:**
- Implementerade `Aggregator.aggregate` exakt enligt arkitektur.md avsnitt 8: kallar `_find_overlaps`, `_determine_sensitivity` och bygger en fryst `Classification`. Ingen sortering, dedup eller filtrering - findings förs vidare i den ordning de producerades av lagren, i linje med avsnitt 3.4 ("båda fynden bevaras").
- `_find_overlaps` använder `itertools.combinations(findings, 2)` för att garantera unika par (ingen `(a, b)` + `(b, a)`, ingen `(a, a)`). Överlappsvillkoret `a.start < b.end and b.start < a.end` matchar exakt formuleringen i issuen och i arkitektur.md avsnitt 3.4.
- `_determine_sensitivity`: tom lista `-> NONE`; minst ett fynd med kategori vars `value` börjar med `"article9."` eller `"context."` `-> HIGH`; annars `-> LOW`. Kontrollen görs via `Category.value.startswith((...))` eftersom `Category` är en `str, Enum` (`gdpr_classifier/core/category.py`), vilket gör prefix-strategin explicit knuten till enum-namngivningskonventionen.
- `MEDIUM` tilldelas aldrig i iteration 1 - dokumenterat i metodens docstring och synkat i `docs/arkitektur.md` avsnitt 8.
- `ReadLints` rena på `gdpr_classifier/aggregator.py` och `gdpr_classifier/__init__.py`.
- Smoke-check: `Pipeline([PatternLayer()], Aggregator()).classify("test")` returnerar `Classification(findings=[], sensitivity=SensitivityLevel.NONE, active_layers=["pattern"], overlapping_findings=[])`. Pipelinen kör nu end-to-end utan fel.
- Inga tester skrivna (egna issues), inga ändringar i `core/`.

**Beslut fattade:**
- `MEDIUM` tilldelas inte i iteration 1. Den är definierad i enumen (arkitektur.md avsnitt 3.3) men aktiveras först tillsammans med `ContextLayer` (iteration 3), där pusselbitseffekten kan detekteras. Iteration 1 har inga kontextuella indirekt-identifierare, så ingen input skulle kunna producera `MEDIUM` meningsfullt - att tilldela den vore att hitta på en gräns. Avvikelsen är dokumenterad direkt i arkitektur.md avsnitt 8 i samma stil som 0.7-vägs-noten i avsnitt 4.2.
- Prefix-detektion på `Category.value` (`startswith("article9.", "context.")`) i stället för en separat mappningstabell. Enum-värdena *är* kontraktet (`article4.*`, `article9.*`, `context.*`); en parallell tabell skulle dubblera samma information och riskera att driva isär när nya kategorier läggs till. Byt strategi när/om prefixnamnen ändras.
- Ingen sortering eller dedup av findings i aggregatorn. Spårbarhet (arkitektur.md avsnitt 3.4) vinner över kompakthet: båda överlappande fynden bevaras i `findings`, och `overlapping_findings` pekar ut deras relation för analys.

**Öppet/Nästa steg:**
- Pipeline-spåret steg 1-9 är nu klara i iteration 1. Kvar i iterationen: evaluation-spåret (Issue #14+), tester per komponent (egna issues) samt formell loggboksmotivering av `MEDIUM` inför iteration 3.

#### Session 2026-04-17 - Antigravity agent (Gemini 3.1 Pro (High))

**Iteration:** 1 (v0.1.0), Issue #21
**Mål:** Implementera betalkorts-detektion (PCI-data) i PatternLager.

**Ändrade filer:**
- `gdpr_classifier/core/category.py` - Ersatte `KORTNUMMER` med `BETALKORT`.
- `gdpr_classifier/layers/pattern/recognizers/betalkort.py` - Ny recognizer med Regex och Luhn.
- `gdpr_classifier/layers/pattern/recognizers/__init__.py` - Exporterade `BetalkortRecognizer`.
- `gdpr_classifier/layers/pattern/pattern_layer.py` - Registrerade `BetalkortRecognizer`.
- `docs/arkitektur.md` - Uppdaterade teknisk dokumentation för betalkort.
- `tests/data/iteration_1/test_dataset.json` - Lade till 5 st testfall.
- `tests/unit/test_betalkort.py` - Skapade enhetstester.

**Gjort:**
- Refaktorerade `KORTNUMMER` till `BETALKORT="article4.betalkort"`.
- Logiska implementationen för Luhn från höger till vänster för 13-16 siffror är gjord. Stödjer vanliga kort (Visa, Mastercard, Amex).
- Nya enhetstester och integrationstester (testdatan) slår igenom till 100%.

**Beslut fattade:**
- Utvecklade en standardiserad Luhn-funktion som jobbar från höger till vänster istället för att återanvända den i `personnummer.py` då kort varibel längd gör originalet otillräckligt. Sträng-ersättning för existerande kategori tillgodosåg renare domänmodell.

**Öppet/Nästa steg:**
- Klar med Issue #21!

