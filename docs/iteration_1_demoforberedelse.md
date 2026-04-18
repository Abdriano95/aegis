# Iteration 1: Demoförberedelse

**Projekt:** gdpr-classifier  
**Version:** 0.1.1  
**Period:** v17 (18-22 april)  
**Metodik:** Scrumban (kanban-board i GitHub Projects)  
**Syfte:** Förbereda artefakten för den första naturalistiska utvärderingen (demo + intervju) genom att implementera lager 2 (NER), åtgärda kända edge cases, och bygga ett demo-gränssnitt.

---

## Kontext och ADR-motivering

Iteration 1:s pipeline och evaluation är integrerade och körda.
Kvantitativa resultat: 95.45% recall, 95.45% precision totalt.
Identifierade begränsningar: 2 FP (telefon-regex matchar delar av IBAN),
2 FN (IDN-epost, telefonnummer med parenteser).

Det höga recall-värdet speglar att testdatan består av "enkla" fall
med explicita mönster. Litteraturen (Mishra et al., 2025; Zhou et al.,
2025; Karras et al., 2025) visar konsekvent att regex utan semantisk
komplettering misslyckas med obekanta format och kontextuell data.
Att presentera enbart regex-systemet för intressenterna vore att
utvärdera en artefakt vi redan vet är otillräcklig.

Detta är fortfarande BIE-cykel 1 (Build, Intervene, Evaluate).
Build-fasen utökas med lager 2 (NER) innan Intervene-steget (demo).
Beslutet att inkludera NER motiveras av justificatory knowledge
från litteraturen, inte av stakeholder-feedback (som ännu inte skett):

- Mishra et al. (2025): "Rule-based and regex systems fail in
  unfamiliar formats and produce many false positives."
- Zhou et al. (2025): mönstermatchning som första steg kräver
  semantisk analys som komplement.
- Karras et al. (2025): rekommenderar hybridpipelines där regler
  förfiltrerar och ML hanterar residualen.

Feedbacken från demon styr sedan iteration 2, där kontextlagret
(lager 3) implementeras.

**Iterationsstruktur efter omplanering:**
- Iteration 1 (BIE-cykel 1): Lager 1 (regex) + Lager 2 (NER) + demo + utvärdering
- Iteration 2 (BIE-cykel 2): Lager 3 (kontext) + förbättringar baserat på feedback
- Iteration 3 (BIE-cykel 3): Förfining + slutgiltig utvärdering

---

## Repo och miljö

- **Repo:** https://github.com/Abdriano95/gdpr-classifier
- **Branch-strategi:** Jobba direkt på `main`. Committa ofta, korta meddelanden.
- **Stäng issues:** Använd `fixes #N` i commit-meddelanden.
- **WIP-gräns:** Max 2 kort i "In progress" per person.

### Nya beroenden

```toml
[project.optional-dependencies]
dev = ["pytest>=8.0"]
demo = ["dash>=2.0"]
nlp = ["spacy>=3.7"]
all = ["dash>=2.0", "spacy>=3.7"]
```

Installera NER-modell: `python -m spacy download sv_core_news_lg`

Installera allt: `pip install -e ".[all,dev]"`

---

## User stories

### Edge case-fixar

| # | Story |
|---|-------|
| 37 | *As a system I want to identify email addresses with Swedish characters in the domain (å, ä, ö) so that IDN addresses like info@företaget.se are flagged as Article 4.* |
| 38 | *As a system I want to identify phone numbers with parentheses around the country code so that formats like (+46)70 999 88 77 are flagged as Article 4.* |
| 39 | *As a developer I want the IBAN-phone overlap false positive documented as a known limitation so that it can be addressed in iteration 2.* |

### Lager 2: NER

| # | Story |
|---|-------|
| 40 | *As a developer I want EntityLayer to use SpaCy sv_core_news_lg for Swedish NER so that person names, locations and organizations are detected with source tags `entity.spacy_PER/LOC/ORG` and organizations mapped to the new `context.organisation` category.* |

*Issue #41 är sammanslagen i #40: source-fältets format är en specifikation inom #40:s implementation, inte en separat kodförändring.*

### Demo-gränssnitt

| # | Story |
|---|-------|
| 42 | *As an evaluator I want a Dash web interface with an evaluation report view so that I can show stakeholders the quantitative results in a readable format with verbose toggle.* |
| 43 | *As an evaluator I want a free-text input view where stakeholders can type or paste text and see detected findings highlighted in the original text with category, source and confidence so that traceability is visible and testable live.* |
| 44 | *As an evaluator I want each highlighted finding to show which layer and rule produced it so that stakeholders can assess the system's traceability (design principle 3).* |

### Testdata

| # | Story |
|---|-------|
| 45 | *As an evaluator I want at least 10 texts containing person names without other patterns so that the NER layer can be evaluated independently.* |
| 46 | *As an evaluator I want at least 5 texts each with location names and organization names so that all NER entity types have test coverage.* |
| 47 | *As an evaluator I want mixed texts combining NER entities with regex patterns so that cross-layer interaction is tested.* |

### Demo och utvärdering

| # | Story |
|---|-------|
| 48 | *As an evaluator I want a demo script with prepared texts and interview questions so that the naturalistic evaluation session is structured and reproducible.* |

---

## Arbetsfördelning

### Abdulla: Edge cases + NER

Bygg i den här ordningen:

| Steg | Issue | Fil | Vad |
|------|-------|-----|-----|
| 1 | #37 | `layers/pattern/recognizers/email.py` | Utöka regex för IDN-domäner |
| 2 | #38 | `layers/pattern/recognizers/telefon.py` | Valfria parenteser i prefix |
| 3 | #39 | `docs/arkitektur.md` | Dokumentera IBAN-telefon-FP |
| 4 | #40 | `layers/entity/entity_layer.py`, `gdpr_classifier/core/category.py` | SpaCy NER-implementation med source-taggar och ORG-mappning till `context.organisation` |

### Johanna: Demo + testdata

Bygg parallellt med Abdulla:

| Steg | Issue | Fil | Vad |
|------|-------|-----|-----|
| 1 | #42 | `demo/app.py`, `demo/layout.py`, `demo/callbacks.py` | Dash-app med rapport-vy |
| 2 | #43 | `demo/callbacks.py`, `demo/layout.py` | Fritext-vy med markeringar |
| 3 | #44 | `demo/callbacks.py` | Spårbarhetsinformation per markering |
| 4 | #45 | `tests/data/iteration_1/test_dataset.json` | NER-testdata: personnamn |
| 5 | #46 | `tests/data/iteration_1/test_dataset.json` | NER-testdata: platser, organisationer |
| 6 | #47 | `tests/data/iteration_1/test_dataset.json` | Blandade texter |

### Tillsammans

| Steg | Issue | Vad |
|------|-------|-----|
| Synk | - | Integrera NER + demo, kör evaluation |
| Sist | #48 | Demomanus och intervjufrågor |

---

## Beroendekarta

```
       Abdulla                          Johanna
          │                                │
  #37 Email IDN-fix (0.5h)       #42 Rapport-vy (0.5 dag)
          │                                │
  #38 Telefon parentes-fix (0.5h)  #43 Fritext-vy (0.5 dag)
          │                                │
  #39 Dokumentera FP (0.5h)       #44 Spårbarhet i UI (2h)
          │                                │
  #40-41 NER EntityLayer (1-2 dag)  #45-47 NER-testdata (0.5 dag)
          │                                │
          └────────────┬───────────────────┘
                       ▼
            Integrera NER + demo (tillsammans, 1h)
                       ▼
            Kör evaluation med NER-data
                       ▼
            #48 Demomanus + intervjufrågor (tillsammans, 1-2h)
                       ▼
            Demo + intervju med intressenter
                       ▼
            Sammanställ feedback -> styr iteration 2
```

---

## Detaljerade instruktioner

### Abdulla: NER-implementation (#40-41)

Ersätt stubben i `layers/entity/entity_layer.py` med:

```python
class EntityLayer:
    def __init__(self, model_name: str = "sv_core_news_lg"):
        self._nlp = spacy.load(model_name)
        self._label_map = {
            "PER": (Category.NAMN, "entity.spacy_PER"),
            "LOC": (Category.ADRESS, "entity.spacy_LOC"),
            "ORG": (Category.ORGANISATION, "entity.spacy_ORG"),
        }

    @property
    def name(self) -> str:
        return "entity"

    def detect(self, text: str) -> list[Finding]:
        findings = []
        doc = self._nlp(text)
        for ent in doc.ents:
            if ent.label_ not in self._label_map:
                continue
            category, source = self._label_map[ent.label_]
            findings.append(Finding(
                category=category,
                start=ent.start_char,
                end=ent.end_char,
                text_span=ent.text,
                confidence=0.8,
                source=source,
                metadata={"ner_label": ent.label_},
            ))
        return findings
```

`confidence` är fast 0.8 i iteration 1; SpaCys `sv_core_news_lg` exponerar inte per-entitets-konfidens via ett enkelt API. Motiveringen och planen att revidera i iteration 2 är dokumenterad i SSOT avsnitt 5.

`Category.ORGANISATION = "context.organisation"` läggs till i `gdpr_classifier/core/category.py` som del av #40. Motiveringen (kontextsignal, inte art 4-data) är dokumenterad i SSOT avsnitt 3.3 och som bullet i avsnitt 12. Full beslutsprosa förs in i repots Loggbok i separat session.

### Johanna: Demo-gränssnitt (#42-44)

**Filstruktur:**
```
demo/
    app.py              # Dash-applikation, entry point
    callbacks.py        # Pipeline-anrop och resultatformatering
    layout.py           # UI-layout (två tabs)
```

**Vy 2 - Textmarkeringar:**
Bygg markeringarna genom att iterera `classification.findings`
sorterade på `start`-position och infoga HTML-spans med bakgrundsfärg:

```python
def build_highlighted_text(text: str, findings: list[Finding]):
    # Sortera findings på start-position
    sorted_findings = sorted(findings, key=lambda f: f.start)
    # Bygg HTML med spans runt varje finding
    # Färgkoda per lager: pattern=orange, entity=blå
    ...
```

Varje markering ska ha en tooltip eller inline-info med:
- Kategori (t.ex. "article4.personnummer")
- Källa (t.ex. "pattern.luhn_personnummer")
- Konfidens (t.ex. "1.0")

Under texten: sammanfattningspanel med känslighetsnivå,
antal fynd per kategori och per lager.

Pipeline-instansiering i callback:
```python
from gdpr_classifier import Pipeline, Aggregator
from gdpr_classifier.layers.pattern import PatternLayer
from gdpr_classifier.layers.entity import EntityLayer
from gdpr_classifier.layers.context import ContextLayer

pipeline = Pipeline(
    layers=[PatternLayer(), EntityLayer(), ContextLayer()],
    aggregator=Aggregator(),
)
```

### Johanna: NER-testdata (#45-47)

Utöka `tests/data/iteration_1/test_dataset.json` med:

Nya kategorivärden:
- `article4.namn`
- `article4.adress`

Exempelformat:
```json
{
  "text": "Hej Anna Svensson, tack för ditt mejl.",
  "description": "Text med personnamn",
  "expected_findings": [
    {
      "category": "article4.namn",
      "start": 4,
      "end": 18,
      "text_span": "Anna Svensson"
    }
  ]
}
```

Tänk på: SpaCy:s NER kan ge andra span-gränser än vad ni
förväntar er. Kör `EntityLayer().detect(text)` på varje
testtext och justera expected_findings efter faktisk output
innan ni committar. Lär av personnummer-buggen.

---

## Testdata: JSON-format (uppdaterat)

Tillgängliga category-värden:
- `article4.personnummer`
- `article4.email`
- `article4.telefonnummer`
- `article4.iban`
- `article4.betalkort`
- `article4.namn` (ny, NER)
- `article4.adress` (ny, NER)
- `context.organisation` (ny, NER - kontextsignal, inte art 4)

---

## Intervjufrågor (utkast)

Semistrukturerade frågor för den naturalistiska utvärderingen:

1. Hur bedömer ni systemets förmåga att identifiera personuppgifter i de texter vi visade?
2. Vilka typer av känslig data ser ni som mest kritiska att fånga i er verksamhet?
3. Finns det texttyper eller format som ni hanterar dagligen som ni tror att systemet skulle missa?
4. Hur värderar ni balansen mellan falska positiva och falska negativa?
5. Om systemet hade funnits i er verksamhet idag, var i arbetsflödet skulle det passa in?
6. Vad skulle behöva förbättras för att ni skulle överväga att använda ett sådant system?
7. Ser ni ett värde i att systemet visar vilket lager och vilken regel som gjorde detektionen (spårbarhet)?

---

## Definition of done

- [ ] Email-recognizer hanterar svenska tecken i domännamn.
- [ ] Telefon-recognizer hanterar parenteser runt landskod.
- [ ] IBAN-telefon-FP dokumenterad som känd begränsning.
- [ ] EntityLayer implementerad med SpaCy NER och source-taggar `entity.spacy_PER/LOC/ORG`; ORG mappad till `context.organisation`.
- [ ] `gdpr_classifier/core/category.py` utökad med `Category.ORGANISATION = "context.organisation"`.
- [ ] Nya testdata med namn, platser, organisationer.
- [ ] Demo-gränssnitt med två vyer (rapport + fritext).
- [ ] Fritext-vyn visar markeringar med spårbarhet.
- [ ] Demomanus och intervjufrågor förberedda.
- [ ] Evaluation körd med NER aktivt, metriker rapporterade.
- [ ] Arkitektur.md uppdaterad (avsnitt 5).
- [ ] Sessionslogg uppdaterad.
- [ ] `git tag v0.1.1`

---

## Loggbok

Dokumentera löpande, i formatet: beslut, alternativ som övervägdes,
motivering, koppling till GDPR-krav eller empiriskt stöd.

Saker att dokumentera i denna fas:
- Teknikval NER: SpaCy vs KB-BERT, motivering
- Mappning av NER-entitetstyper till GDPR-kategorier
- SpaCy-modellval (sv_core_news_lg vs alternativ)
- Hur konfidens hanteras för NER-findings
- Designval i demo-gränssnittet som stöder spårbarhet
- Varför NER inkluderas före första utvärderingen (litteraturmotivering)
- Beslut om `context.*`-prefix och ORG-kategorisering (kommer att föras in som numrerat beslut i Loggboken i separat session)

---

## Agent-sessionslogg

### Regel

**Varje agent (AI eller människa) som arbetar i en session ska logga sin session här efter avslutat arbete.** Loggen är komplement till Loggboken ovan: Loggboken dokumenterar *beslut och motiveringar*, medan sessionsloggen dokumenterar *vad som faktiskt gjordes, i vilken ordning, och av vem*. Syftet är spårbarhet och att nästa agent (eller granskare) snabbt ska kunna förstå repots historik utan att läsa hela git-loggen.

### Format

Lägg till en ny post längst ner. Använd följande mall:

```markdown
#### Session YYYY-MM-DD - [Agent/Person]

**Iteration:** [t.ex. 1 / v0.1.1]
**Mål:** [en mening om vad sessionen skulle åstadkomma]

**Ändrade filer:**
- `path/till/fil.py` - [kort beskrivning]

**Gjort:**
- [punkt per konkret åtgärd]

**Beslut fattade:** [kort; länka till Loggboken om längre motivering behövs]
**Öppet/Nästa steg:** [vad som återstår eller blockerar]
```

### Regler för loggning

1. Logga **efter varje sammanhållen arbetssession**.
2. En post per session, inte per commit.
3. Håll det kort: punktlistor, inga resonemang (de hör hemma i Loggboken).
4. Ändra aldrig tidigare poster. Lägg till en ny post om något behöver korrigeras.
5. Om sessionen genererade arkitekturbeslut ska dessa även föras in i Loggboken med full motivering.

### Poster

#### Session 2026-04-18 - Cursor-agent (Opus) (issue #37)

**Iteration:** 1 / v0.1.1
**Mål:** Lösa issue #37 - utöka email-regex för IDN-domäner med svenska tecken (å, ä, ö).

**Ändrade filer:**
- `gdpr_classifier/layers/pattern/recognizers/email.py` - teckenklasser i lokal- och domändel utökade med `åäöÅÄÖ`; `-` explicit escapad (`\-`).
- `docs/arkitektur.md` - avsnitt 4.2, E-post-bullet: rad om IDN-stöd för svenska tecken tillagd.
- `docs/iteration_1_demoforberedelse.md` - denna sessionspost.

**Gjort:**
- Bytt `_PATTERN` i `email.py` enligt issue-spec; struktur, `source`, `confidence` och `IGNORECASE` oförändrade.
- Kört `.venv\Scripts\python.exe run_evaluation.py`: `article4.email` TP=10, FP=0, FN=0 → recall 100% (upp från 9/10). Total: TP=43, FP=2, FN=1, precision 95.56%, recall 97.73%, F1 96.63%. `info@företaget.se` ej längre i FN-sektionen.
- Kört `.venv\Scripts\python.exe -m pytest tests/integration/test_end_to_end.py -s`: 1 passed.
- `ReadLints` på `email.py`: rent.

**Beslut fattade:** Behåller `[a-zA-Z]{2,}` i TLD-delen; punycode/xn-- och IDN-TLD ligger utanför iteration 1:s scope (SSOT 4.2).
**Öppet/Nästa steg:** Kvarvarande FN/FP ligger i `article4.telefonnummer` (recall 90%, precision 81.82%) - hör till andra issues. Unit-tester för email-edge cases vid behov i senare issue. Commit sker efter granskning (ingen commit i denna session).

#### Session 2026-04-18 - Cursor-agent (Opus) (issue #38)

**Iteration:** 1 / v0.1.1
**Mål:** Lösa issue #38 - utöka telefon-regex så att `+46`/`0046` får omges av balanserade parenteser (t.ex. `(+46)70 999 88 77`).

**Ändrade filer:**
- `gdpr_classifier/layers/pattern/recognizers/telefon.py` - prefix-alternationen utökad med `\((?:\+46|0046)\)` som första gren; `source`, `confidence`, lookbehind `(?<![\d+])`, separators och boundaries oförändrade.
- `docs/arkitektur.md` - avsnitt 4.2, Telefonnummer-bullet: rad om stöd för valfria balanserade parenteser runt landskoden tillagd.
- `docs/iteration_1_demoforberedelse.md` - denna sessionspost.

**Gjort:**
- Bytt `_PATTERN` i `telefon.py` enligt issue-spec; parens-grenen placerad först i alternationen så motorn försöker den före bar-varianten.
- Kört `.venv\Scripts\python.exe run_evaluation.py`: `article4.telefonnummer` TP=10, FP=2, FN=0 → recall 100% (upp från 90%), precision 83.33%. Total: TP=44, FP=2, FN=0, precision 95.65%, recall 100%, F1 97.78%. `(+46)70 999 88 77` ej längre i FN-sektionen; inga nya FP utöver de 2 befintliga IBAN-överlapps-FP:erna (#39).
- Kört `.venv\Scripts\python.exe -m pytest tests/integration/test_end_to_end.py -s`: 1 passed.
- `ReadLints` på `telefon.py`: rent.

**Beslut fattade:** Parens-varianten omfattar endast `+46`/`0046`, inte domestikt `0` (FP-risk + inte i verkligt bruk). SSOT 4.2 uppdaterad i samma session.
**Öppet/Nästa steg:** Kvarvarande 2 FP på telefon (IBAN-fragment som matchar telefon-regex) hör till issue #39. Commit sker efter granskning (ingen commit i denna session).

#### Session 2026-04-18 - Cursor-agent (Opus) (issue #39)

**Iteration:** 1 / v0.1.1
**Mål:** Lösa issue #39 - dokumentera IBAN-telefon-FP som känd begränsning i SSOT.

**Ändrade filer:**
- `docs/arkitektur.md` - nytt avsnitt 14 "Kända begränsningar (iteration 1)" infört före Referenser; "Referenser" renumrerad från 14 till 15.
- `docs/iteration_1_demoforberedelse.md` - denna sessionspost.

**Gjort:**
- Lagt in ~24 raders prosa som beskriver fenomenet (telefon-regex matchar siffersekvenser inom IBAN-fynd), de två konkreta FP-exemplen verbatim (`"0555 5555 55"` inom `SE96 5000 0000 0555 5555 55` och `"05 1234 5678"` inom `SE05 1234 5678 9012 3456 78`), grundorsak på aggregator-nivå, motivering till att inte åtgärda i iteration 1 (koppling till designprincip 3 och intressentdiskussion), samt planerad containment-regel för iteration 2.
- Renumrerat "Referenser" från 14 till 15.
- Ingen kodfil rörd; verifierat med `git status` att endast `docs/arkitektur.md` och `docs/iteration_1_demoforberedelse.md` är ändrade.

**Beslut fattade:** Placering som nytt avsnitt 14 före Referenser valdes framför renumrering av sektion 12-13 eller underrubrik under Iterationsplan, efter granskning i Plan Mode. Terminologi "tar bort"/"bortfiltrerat" valdes framför anglicismen "droppa" för att matcha SSOT-prosans ton ("reducera fyndmängden", "aktiv reduktionsregel").
**Öppet/Nästa steg:** Issue #39 klar för commit efter granskning. Nästa: issue #40 (SpaCy EntityLayer i `layers/entity/entity_layer.py`). Commit sker efter granskning (ingen commit i denna session).

#### Session 2026-04-18 – Agent (Antigravity)

**Iteration:** 1 / v0.1.1
**Mål:** Implementera Issue #42 – Dash webbgränssnitt med rapportvy.

**Ändrade filer:**
- `pyproject.toml` – Lade till optional dependencies: `demo`, `nlp`, `all`.
- `demo/__init__.py` – Ny, standard init-fil.
- `demo/app.py` – Ny, Dash entry point med layout och callback-registrering.
- `demo/layout.py` – Ny, `get_layout()` med `dcc.Tabs` (tre flikar: "Utvärderingsrapport", "Fritext-analys", "Testdata").
- `demo/callbacks.py` – Ny, kör `run_evaluation()` vid modulstart, verbose-toggle callback.

**Gjort:**
- Uppdaterat `pyproject.toml` med `demo = ["dash>=2.0"]`, `nlp = ["spacy>=3.7"]`, `all = [...]` under `[project.optional-dependencies]`.
- Skapat `demo/`-paketet med fyra filer enligt planen.
- Flik 1 ("Utvärderingsrapport") visar totala mätvärden i en DataTable; verbose-toggle visar per-kategori- och per-lager-tabeller.
- Flik 2 ("Fritext-analys") är en stub/placeholder för Issue #43.
- Utvärderingen körs en gång globalt vid modulstart mot `tests/data/iteration_1/test_dataset.json`.
- Per-lager-tabellen visar "N/A" för Recall och F1 (arkitekturbeslut).
- Verifierat: appen startar utan fel, callbacks returnerar korrekt data, verbose-toggle döljer/visar detaljer.

**Beslut fattade:** Utvärderingen körs globalt en gång vid uppstart (inte per toggle-klick) för responsivt UI.
**Öppet/Nästa steg:** Issue #43 (fritext-analys med markeringar).

#### Session 2026-04-18 - Cursor-agent (Opus) (issue #40+#41 docs-merge)

**Iteration:** 1 / v0.1.1
**Mål:** Dokumentations-merge av issue #40+#41 och kategori-beslut C (ORG som `context.organisation`) i SSOT och demoforberedelse.md innan implementationsprompten.

**Ändrade filer:**
- `docs/arkitektur.md` - `Category`-enum utökad med `ORGANISATION = "context.organisation"`, prefix-konvention i prosa efter enum, avsnitt 5 omskrivet (rubrik utan "Iteration 2", entitetsmappning PER/LOC/ORG, ORG-motivering, konfidens-not, källformat), mening om `context.*` i avsnitt 8, ny bullet i avsnitt 12.
- `docs/iteration_1_demoforberedelse.md` - #40+#41 sammanslagna i user stories-tabellen, Abdulla-arbetsfördelning reducerad till 1-4 steg, `_label_map`-skissen uppdaterad med nya source-taggarna och `Category.ORGANISATION`, prosa under kodskissen omskriven, testdata-kategorilistan utökad med `context.organisation`, DoD-rader uppdaterade (NER + ny rad för `core/category.py`), Loggbok-bullet tillagd, denna sessionspost.

**Gjort:**
- Enum-ordning (BETALKORT sist) och `class Category(Enum)` (inte `str, Enum`) bevarade i SSOT efter granskning i Plan Mode; minsta möjliga diff.
- `KONTEXTUELLT_KÄNSLIG = "kontextuellt_kanslig"` bevarad verbatim - värdet har inte flyttats till `context.*`-paraplyet. Beslut från granskningen: `ORGANISATION` är en kontextsignal som kompletterar art 4-fynd, medan `KONTEXTUELLT_KÄNSLIG` är en iteration 3-signal med annan semantik; att ge dem samma prefix antyder likhet som inte finns.
- Rubriken på avsnitt 5 ändrad från "Lager 2: Entitetsigenkänning (NER) - Iteration 2" till "Lager 2: Entitetsigenkänning (NER)" eftersom lagret byggs i iteration 1.
- `context.*`-prefix-konventionen förklarad i prosa efter enum-blocket; ORG-motivering kopplad till pusselbitseffekten (avsnitt 3.3).
- Aggregator-not i avsnitt 8: `context.*`-fynd triggar inte ensamma någon sensitivity-höjning i iteration 1; kombinationslogik planerad iteration 2.
- Avsnitt 12 fick en bullet om `context.*`-beslutet; full Beslut N-prosa placeras i repots Loggbok i separat session (avsnitt 12 är ämneslista, inte beslutsregister).
- `git status` visar exakt två ändrade filer: `docs/arkitektur.md`, `docs/iteration_1_demoforberedelse.md`.

**Beslut fattade:** ORG mappas till `Category.ORGANISATION = "context.organisation"` (nytt `context.*`-prefix för kontextsignaler som inte i sig är art 4-data). Full motivering går till repots Loggbok i separat session; SSOT avsnitt 3.3, 5 och 12 och denna session räcker för implementationsprompten.
**Öppet/Nästa steg:** Pre-existerande drift mellan `core/category.py` (`POSTORT`, `POSTNUMMER`) och SSOT avsnitt 3.3 rörs inte här - egen issue. Implementationsprompt för sammanslagna #40 skrivs mot denna synkade SSOT.

#### Session 2026-04-18 - Cursor-agent (Opus) (issue #40 impl)

**Iteration:** 1 / v0.1.1
**Mål:** Implementera issue #40 (stänger #41) - SpaCy-baserad EntityLayer med PER/LOC/ORG-mappning och ny `Category.ORGANISATION = "context.organisation"`.

**Ändrade filer:**
- `gdpr_classifier/core/category.py` - ny grupp `# Kontextsignaler: inte art 4-data i sig, bidrar till klassificering i kombination` med `ORGANISATION = "context.organisation"` insatt mellan art 9-blocket och `KONTEXTUELLT_KANSLIG`. Ingen befintlig medlem flyttad.
- `gdpr_classifier/layers/entity/entity_layer.py` - stub ersatt med SpaCy-implementation: laddar `sv_core_news_lg` i `__init__`, `_label_map` mappar `PER→Category.NAMN/entity.spacy_PER`, `LOC→Category.ADRESS/entity.spacy_LOC`, `ORG→Category.ORGANISATION/entity.spacy_ORG`. `confidence=0.8` hårdkodad, `metadata={"ner_label": ent.label_}`. Okända labels hoppas över.
- `docs/iteration_1_demoforberedelse.md` - denna sessionspost.

**Gjort:**
- Installerat spaCy 3.8.14 i `.venv` via `pip install -e .[nlp]`. `sv_core_news_lg` 3.8.0 var redan installerad i miljön - verifierat med `spacy.load('sv_core_news_lg')`. Ingen modell-download behövdes.
- `pyproject.toml`-verifiering: `spacy>=3.7` fanns redan i `nlp` och `all` dependency-grupperna - ingen ändring behövdes.
- `evaluation/dataset/loader.py`-verifiering: loadern använder `Category(finding_data["category"])` dynamiskt (rad 36), så Del 1 räcker och ingen hardkodad allow-list finns - ingen ändring behövdes.
- Kört `.venv\Scripts\python.exe run_evaluation.py`.
  - Totalt före (iteration 1-baseline, enbart pattern-lagret): `TP=44, FP=2, FN=0`, precision 95.65%, recall 100%, F1 97.78%.
  - Totalt efter: `TP=44, FP=4, FN=0`, precision 91.67%, recall 100%, F1 95.65%. Recall oförändrad 100% för alla `article4.*`-kategorier.
  - Per lager: `pattern: TP=44, FP=2` (oförändrat), `entity: TP=0, FP=2` (nytt lager aktiverat).
  - Per kategori: `article4.adress` nu synlig med `TP=0, FP=2` (LOC-fynd mappade hit utan ground-truth); övriga art4-kategorier oförändrade.
  - Totalt **2 NER-fynd** producerade mot nuvarande testdata, båda LOC:
    - `[entity.spacy_LOC] "9001010009"` i `"Kunden (9001010009) ringde in."` - modellen flaggade personnummer-strängen som LOC (feldetektion som motiverar pattern-lagrets prioritet vid överlapp).
    - `[entity.spacy_LOC] "Stockholm"` i `"Namn: Anna Andersson\nPersonnummer: 19801010-0009\nOrt: Stockholm"` - korrekt LOC-detektion.
  - **0 PER-fynd** och **0 ORG-fynd** på nuvarande testdata trots att texterna innehåller namn (`Anna Andersson`, `Erik Eriksson`, `Maja Maj`, `Kalle`, `olof.olofsson`) och organisationen `Nordea`. Modellen plockade inte upp dem i de kontexter de förekommer (chattmeddelanden/mailfragment). Detta är utgångspunkten för Johannas #45-47 - testdata behöver entiteter i kontexter där modellen faktiskt triggar.
- Kört `.venv\Scripts\python.exe -m pytest tests/integration/test_end_to_end.py -s`: 1 passed.
- `ReadLints` på `core/category.py` och `layers/entity/entity_layer.py`: rent.
- `git status` visar exakt tre förväntade ändrade filer: `gdpr_classifier/core/category.py`, `gdpr_classifier/layers/entity/entity_layer.py`, `docs/iteration_1_demoforberedelse.md`.

**Beslut fattade:** DoD-raden "Total recall/precision ska inte regressera mot iteration 1-baseline" i originalprompten ersattes efter Plan Mode-granskning av två sanningsenliga krav: (a) recall för `article4.*`-kategorier ska inte regressera (uppfyllt, 100% per kategori), och (b) nya FP från NER-lagret rapporteras med antal och exempel (2 LOC-FP, se ovan). Totalprecision regresserade från 95.65% till 91.67% - förväntad arkitektonisk effekt av att NER-lagret aktiveras innan datasetet har NER-ground-truth. Effekten upphör när #45-47 levererar PER/LOC/ORG-labels. Kategoriplacering i `core/category.py` enligt Alternativ A: `ORGANISATION` och `KONTEXTUELLT_KANSLIG` behålls i två separata kommentargrupper (speglar SSOT och Plan Mode-beslutet att deras semantik är olika trots gemensamt `context.*`-prefix).
**Öppet/Nästa steg:** Johannas #45-47 (NER-testdata med ground-truth PER/LOC/ORG) är naturlig verifiering av EntityLayers recall. Eventuell evaluation-filtrering av `context.*`-fynd hör till separat issue. LOC-feldetektion av `9001010009` som plats-namn kan bli en not i avsnitt 14 (Kända begränsningar) om den kvarstår efter #45-47. Commit sker efter granskning (ingen commit i denna session).

#### Session 2026-04-18 – Claude Sonnet 4.6 (claude-code)

**Iteration:** 1 / v0.1.1
**Mål:** Implementera Issue #43 (Fritext-analys-flik) och Issue #44 (Spårbarhet via tooltips).

**Ändrade filer:**
- `demo/layout.py` – Ny hjälpfunktion `freetext_tab_layout()` med `dcc.Textarea`, "Analysera"-knapp, `freetext-result`-div och `freetext-summary`-div.
- `demo/callbacks.py` – Ny `_resolve_overlaps()` (klusteralgoritm för överlappande fynd), `build_highlighted_text()` (färgkodade `html.Span` med `title`-tooltip), `build_summary()` (sammanfattningspanel med känslighetsnivå + fynd per kategori/lager), samt `analyze_text`-callback. Stub-gren i `render_tab` ersatt med anrop till `freetext_tab_layout()`.

**Gjort:**
- Implementerat klusterbaserad överlappslösning: fynd grupperas i intervallkluster; per kluster väljs vinnaren med högst konfidens. Garanterar att ingen teckenposition dupliceras.
- Färgkodning via `style`-attribut: `pattern.*` → `orange`, `entity.*` → `#add8e6` (lightblue).
- Tooltip via `title`-attribut: `"Kategori: ..., Källa: ..., Konfidens: ..."`.
- Sammanfattningspanel visar känslighetsnivå (färgkodad badge), fynd per GDPR-kategori och fynd per lager i tabellformat.
- Återanvänder befintlig `build_pipeline()` (PatternLayer + EntityLayer + ContextLayer + Aggregator).
- Commit ej gjord (väntar på instruktion).

**Beslut fattade:** Överlappslösning via klustergruppa + max-confidence-vinnare (inte greedy cursor), eftersom det hanterar fall där ett sent fynd med hög konfidens ska vinna över ett tidigt fynd med låg konfidens inom samma kluster. Layoutkomponenter returnas från `layout.py` (separation of concerns); callbacks importerar `freetext_tab_layout` därifrån.
**Öppet/Nästa steg:** Manuell verifiering i webbläsaren. Commit efter granskning.
