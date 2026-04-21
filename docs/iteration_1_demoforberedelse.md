# Iteration 1: Demoförberedelse

**Projekt:** gdpr-classifier  
**Version:** 0.1.1  
**Period:** v17 (18-22 april)  
**Metodik:** Scrumban (kanban-board i GitHub Projects)  
**Syfte:** Förbereda artefakten för den första naturalistiska utvärderingen (demo + intervju) genom att implementera lager 2 (NER), åtgärda kända edge cases, och bygga ett demo-gränssnitt.

---

## Status (uppdaterad 2026-04-20)

Sammanställning av iteration 1:s demoförberedelse-issues per 2026-04-20. Detaljerade sessionsposter för varje issue finns under Agent-sessionslogg längre ner i dokumentet.

| # | Issue | Ansvarig | Status | Sessionspost |
|---|-------|----------|--------|--------------|
| 37 | Email IDN-fix | Abdulla | Klar | 2026-04-18 |
| 38 | Telefon parentes-stöd | Abdulla | Klar | 2026-04-18 |
| 39 | IBAN-telefon-FP dokumenterad | Abdulla | Klar | 2026-04-18 |
| 40 | EntityLayer med SpaCy NER (inkl. #41) | Abdulla | Klar | 2026-04-18 |
| 42 | Dash-app: rapport-vy | Johanna | Klar | 2026-04-18 |
| 43 | Dash-app: fritext-vy med markeringar | Johanna | Klar | - |
| 44 | Dash-app: spårbarhet per markering | Johanna | Pågår | - |
| 45 | NER-testdata: personnamn | Johanna | Klar | - |
| 46 | NER-testdata: platser + organisationer | Johanna | Klar | - |
| 47 | NER-testdata: blandade texter | Johanna | Klar | - |
| 48 | Demomanus + intervjufrågor | Gemensamt | Ej påbörjad | - |
| 54 | SSOT-drift (POSTORT/POSTNUMMER + diakriter) | Abdulla | Klar | 2026-04-20 |
| 55 | Beslut N i Loggboken (context.*-prefix) | Backlog | Ej påbörjad | - |
| 60 | PRS-fix (SpaCy SUC3-taggset) | Abdulla | Klar | 2026-04-20 |
| 62 | Avsnitt 14: NER-FPs + grundorsaks-struktur | Abdulla | Klar | 2026-04-20 |
| - | Testdata-fix 820415-3421 → 820415-3426 | Abdulla | Klar | 2026-04-20 |
| - | SSOT docs-sync extra (D1-D7 exkl D5: filstruktur, fem recognizers, frontmatter, finding-exempel) | Abdulla | Klar | 2026-04-20 |

Total evaluation efter alla dagens fixar: TP=78, FP=13, FN=3, precision 85.71%, recall 96.30%, F1 90.70%. Kvarvarande FP och FN dokumenterade som kända begränsningar i SSOT avsnitt 14.

Anmärkningar:
- "Klar" = implementation + sessionspost + commit (där sessionspost finns) eller verifierad som klar i testdatat/UI:t (där sessionspost saknas).
- Issues utan sessionspost (#43, #45, #46, #47) är verifierade klara via senaste evaluation-körningen (18 namn detekteras, 7 platser, 7 org-exempel i testdatan) och Dash-appens fritext-vy.
- "-" i Sessionspost-kolumnen betyder att ingen separat post finns; spårbarhet via git-historik.
- Issue #41 är sammanslagen i #40 och har ingen egen rad.

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

- [x] Email-recognizer hanterar svenska tecken i domännamn.
- [x] Telefon-recognizer hanterar parenteser runt landskod.
- [x] IBAN-telefon-FP dokumenterad som känd begränsning.
- [x] EntityLayer implementerad med SpaCy NER och source-taggar `entity.spacy_PRS/LOC/ORG`; ORG mappad till `context.organisation`.
- [x] `gdpr_classifier/core/category.py` utökad med `Category.ORGANISATION = "context.organisation"`.
- [x] Nya testdata med namn, platser, organisationer.
- [x] Demo-gränssnitt med två vyer (rapport + fritext).
- [ ] Fritext-vyn visar markeringar med spårbarhet.
- [ ] Demomanus och intervjufrågor förberedda.
- [x] Evaluation körd med NER aktivt, metriker rapporterade.
- [x] Arkitektur.md uppdaterad (avsnitt 5).
- [x] Sessionslogg uppdaterad.
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

#### Session 2026-04-19 – Claude Sonnet 4.6 (claude-code) (issue #45)

**Iteration:** 1 / v0.1.1
**Mål:** Utöka testdatasetet med 10 nya texter för NER-detektion av personnamn (`article4.namn`), isolerade från övriga GDPR-mönster.

**Ändrade filer:**
- `tests/data/iteration_1/test_dataset.json` - 10 nya testfall med enbart `article4.namn`-fynd tillagda (totalt 55 entries).
- `scripts/build_namn_testdata.py` - nytt temporärt valideringsskript som beräknar och assert-verifierar alla `(start, end, text_span)`-index programmatiskt.
- `docs/iteration_1_demoforberedelse.md` - denna sessionspost.

**Gjort:**
- Skrivit `scripts/build_namn_testdata.py`: definierar varje testfall som `(text, [namn-spans])`, beräknar index via `text.find()`, assertar `text[start:end] == span` för varje fynd innan serialisering. Noll AssertionErrors vid körning.
- Lagt till 10 nya JSON-objekt i `test_dataset.json`: hälsningsfras, mötesanteckning, kundtjänstnotat, affärskorrespondens, verksamhetstext, projektbeskrivning, chattmeddelande, HR-dokument, intyg och formellt protokoll. Totalt 14 namnfynd (6 texter med ett namn, 4 texter med två namn). Bindestreck i förnamn (`Lars-Göran Berg`, `Per-Olof Lindberg`) ingår.
- Verifierat att `load_dataset()` laddar alla 55 entries utan ValueError.
- Kört `pytest tests/` (23 passed, inga regressioner).

**Beslut fattade:** Index beräknas maskinellt (inte hand-räknade) via `find()`-strategi med `search_from`-offset för att hantera upprepade namn - samma metod som användes i issue #18-20.
**Öppet/Nästa steg:** Commit efter granskning. EntityLayer-recall mot dessa 10 texter utvärderas när `run_evaluation.py` körs i demoläge.

#### Session 2026-04-19 – Claude Sonnet 4.6 (claude-code) (issues #46 & #47)

**Iteration:** 1 / v0.1.1
**Mål:** Utöka testdatasetet med platser (`article4.adress`), organisationer (`context.organisation`) och blandade cross-layer-texter (NER + regex).

**Ändrade filer:**
- `tests/data/iteration_1/test_dataset.json` - 15 nya testfall tillagda (totalt 70 entries).
- `scripts/build_locations_orgs_mixed_testdata.py` - nytt valideringsskript med generaliserad `build_findings(text, span_category_pairs)`.
- `docs/iteration_1_demoforberedelse.md` - denna sessionspost.

**Gjort:**
- Skrivit `scripts/build_locations_orgs_mixed_testdata.py` med tre RAW-listor: 5 platstexter, 5 organisationstexter, 5 blandade texter. Generaliserad `build_findings` tar `(span, category)`-par istället för en global konstant.
- Lagt till 5 `article4.adress`-testfall: Stockholm, Sveavägen 44, Göteborg, Malmö C, Örebro.
- Lagt till 5 `context.organisation`-testfall: Volvo AB, Skatteverket, Acme Corp, Nordea Bank, Region Skåne.
- Lagt till 5 blandade testfall (cross-layer): namn+email, namn+personnummer+plats, organisation+IBAN, namn+telefon+plats, organisation+namn+email.
- Verifierat noll AssertionErrors. Verifierat att `load_dataset()` laddar alla 70 entries utan ValueError. Kört `pytest tests/` utan regressioner.

**Beslut fattade:** Samma `find()`-strategi med `search_from`-offset för indexberäkning. Blandade entries ordnar span_category_pairs i textordning (vänster → höger) för att `search_from` ska fungera korrekt.
**Öppet/Nästa steg:** Commit efter granskning. `run_evaluation.py` bör nu visa recall > 0 för `article4.adress` och `context.organisation`.

#### Session 2026-04-20 - Cursor-agent (Opus) (issue #60)

**Iteration:** 1 / v0.1.1
**Mål:** Lösa issue #60 - byta SpaCy-label-nyckeln i `EntityLayer._label_map` från `PER` (CoNLL) till `PRS` (SUC3, vilket `sv_core_news_lg` faktiskt producerar) så att `article4.namn` detekteras.

**Ändrade filer:**
- `gdpr_classifier/layers/entity/entity_layer.py` - `_label_map`-nyckeln ändrad från `"PER"` till `"PRS"`; source-taggen från `"entity.spacy_PER"` till `"entity.spacy_PRS"`; modul-docstringens mappnings-exempel (`PER -> Category.NAMN`) uppdaterat till `PRS`. LOC/ORG, `confidence=0.8`, `metadata={"ner_label": ent.label_}` och övrig struktur oförändrade.
- `docs/arkitektur.md` - avsnitt 5: mappningsraden (`PRS` → `Category.NAMN`, `source="entity.spacy_PRS"`), källformat-exemplet (`PRS`/`LOC`/`ORG`), ny mening om SUC3 vs CoNLL, samt neutral omskrivning av ORG-motiveringen (`PER-prestanda` → `person-prestanda`). Avsnitt 12: ny bullet om upptäckten av SUC3 vs CoNLL-tagg-konvention.
- `docs/iteration_1_demoforberedelse.md` - denna sessionspost.

**Gjort:**
- **Diagnos (före fix):** `.venv\Scripts\python.exe run_evaluation.py` visade `article4.namn` recall 0/18, entity-lager TP=11, FP=4. Inga NAMN-findings alls från EntityLayer trots att testdatan innehöll 18 namnspan.
- **Verifiering av rotorsak:** `.venv\Scripts\python.exe test.py` gav `'Anna Svensson' → PRS`, vilket bekräftar att `sv_core_news_lg` använder SUC3:s `PRS` för person-entiteter - inte CoNLL:s `PER`. Det tidigare `_label_map` med `"PER"` som nyckel filtrerade därför bort alla namn i `if ent.label_ not in self._label_map: continue`.
- **Ändrat `_label_map` och source-tag** till `PRS` / `entity.spacy_PRS`. Docstring synkad.
- **Uppdaterat `arkitektur.md`** avsnitt 5 (mapping, källformat, SUC3-not, neutral ORG-prosa) och avsnitt 12 (SUC3/CoNLL-bullet).
- **Evaluation efter fix:** Total TP=77, FP=13, FN=4, Precision 85.56%, Recall 95.06%, F1 90.06%. `article4.namn` TP=18, FP=6, FN=0 → **recall 100% (18/18, upp från 0/18)**, precision 75.00%, F1 85.71%. `article4.personnummer` TP=13, FP=0, FN=1 (oförändrad, 92.86% recall; kvarvarande FN `820415-3421` är separat testdata-bugg utanför scope). Per-lager: entity TP=29, FP=10 (upp från TP=11, FP=4 - de nya TP är de 18 namnen, nya FP är bl.a. PRS-feldetektion av `2222`/`070`/`Anna` samt ORG-feldetektion av e-postadresser).
- **`.venv\Scripts\python.exe -m pytest tests/integration/test_end_to_end.py -s`:** 1 passed.
- **`ReadLints` på `entity_layer.py`:** rent.

**Beslut fattade:** Source-taggen följer SpaCys råetikett (`entity.spacy_PRS`), konsekvent med SSOT 5:s formatregel `entity.spacy_{LABEL}`. Historiska sessionsposter som refererar till `PER` lämnas orörda per mall-regel 4 ("Ändra aldrig tidigare poster"). Docstring-uppdatering och neutral omskrivning av ORG-motiveringen i avsnitt 5 beslutade i Plan Mode som följdändringar.
**Öppet/Nästa steg:** Kvarvarande FN på personnummer `820415-3421` är separat testdata-bugg (eget issue). Nya NER-FP från PRS (`2222`, `070`, `Anna` utan efternamn) och ORG (e-postadresser) är förväntad arkitektonisk kompromiss i iteration 1 - kan bli input till kända begränsningar (avsnitt 14) eller senare tuning. Commit sker efter granskning (ingen commit i denna session).

#### Session 2026-04-20 - Cursor-agent (Opus) (testdata-fix personnummer)

**Iteration:** 1 / v0.1.1
**Mål:** Fixa testdata-bugg i `tests/data/iteration_1/test_dataset.json` - personnummer `820415-3421` fallerar Luhn-checksumma och avvisas korrekt av `PersonnummerRecognizer`. Byt till giltig variant enligt Beslut 9 i Loggboken (testdata med strukturerad data måste ha giltiga kontrollsiffror).

**Ändrade filer:**
- `tests/data/iteration_1/test_dataset.json` - `820415-3421` → `820415-3426` i både `text`-fältet och motsvarande `expected_findings[].text_span` för entryn "Erik Johansson, 820415-3421, är bosatt i Göteborg." Positionerna (`start=16, end=27`) oförändrade eftersom längden är densamma.
- `docs/iteration_1_demoforberedelse.md` - denna sessionspost.

**Gjort:**
- Manuellt räknat Luhn-kontrollsiffra för `820415-342X`: positionerna 0,2,4,6,8 dubblas (8→16→7, 0, 1→2, 3→6, 2→4), positionerna 1,3,5,7 (2, 4, 5, 4), summa utan kontrollsiffra = 34, kontrollsiffra = (10 - 34 mod 10) mod 10 = **6**.
- Bytt båda förekomsterna via en enda textersättning (`replace_all`). Verifierat med `git status` att exakt en fil ändrades.
- **Evaluation efter fix:** `article4.personnummer` TP=14, FP=0, FN=0 → **recall 100% (upp från 13/14 = 92.86%)**, F1 100%. Total: TP=78, FP=13, FN=3, Precision 85.71%, Recall 96.30%, F1 90.70% (total FN minskar med 1; övriga tre kvarvarande FN är `context.organisation`: `Volvo AB`, `Skatteverket` ×2).
- `.venv\Scripts\python.exe -m pytest tests/integration/test_end_to_end.py -s`: 1 passed.

**Beslut fattade:** Ingen kodändring, ingen SSOT-synk - rent testdata-fix enligt Beslut 9. Samma typ av korrigering som de 13 som gjordes tidigare i iteration 1.
**Öppet/Nästa steg:** Kvarvarande tre `context.organisation`-FN (Skatteverket, Volvo AB) beror på SpaCy-modellens taggning - separata issues. Commit sker efter granskning (ingen commit i denna session).

#### Session 2026-04-20 - Cursor-agent (Opus) (issue #62)

**Iteration:** 1 / v0.1.1
**Mål:** Lösa issue #62 - utöka SSOT avsnitt 14 (Kända begränsningar) med ingress och omstrukturering till två grundorsaksblock (14.1 Cross-recognizer-överlapp, 14.2 NER modell-feldetekteringar) inför demon.

**Ändrade filer:**
- `docs/arkitektur.md` - avsnitt 14: ny ingress efter rubriken som signalerar per-grundorsak-gruppering; ny underrubrik `### 14.1 Cross-recognizer-överlapp` före befintlig IBAN-telefon-prosa; första meningen i 14.1 uppdaterad till cross-recognizer-formulering ("Två falska positiva i iteration 1:s utvärdering härrör från cross-recognizer-överlapp."); resten av 14.1:s prosa (konkret exempel, grundorsak på aggregator-nivå, motivering till att inte åtgärda) ordagrant oförändrad; avslutnings-meningarna "Åtgärden planeras för iteration 2:s Build-fas. Denna issue (#39) dokumenterar enbart begränsningen som underlag för framtida arbete." togs bort (stale self-referens till issue när avsnittet nu växer med fler grundorsaker - git-historiken bevarar spårbarheten till #39) och ersattes av hänvisnings-mening till 14.2 som avslutar 14.1; nytt block `### 14.2 NER modell-feldetekteringar` med tre stycken (fenomenet + litteraturförankring till Mishra et al. 2025 och Karras et al. 2025, tre konkreta underkategorier av feldetekteringar med exempel `"2222"`/`"070"`/`"Anna"`/`foretag.se`/`privat.se`/`"9001010009"`, rotorsak på lager-interaktion och planerad åtgärd).
- `docs/iteration_1_demoforberedelse.md` - denna sessionspost.

**Gjort:**
- Verifierat att sektionsnumrering inte förändrats: `## 14. Kända begränsningar (iteration 1)` kvar som 14, `## 15. Referenser` kvar som 15. `### 14.1` och `### 14.2` införda som nya nivåer (`###`), inte toppsektioner.
- Verifierat via `Grep` i repot att inga andra ställen refererar till `14.1`/`14.2` på ett sätt som kolliderar med de nya underrubrikerna (tidigare sessionsposter refererar till "avsnitt 14" som helhet, vilket förblir korrekt).
- Befintlig IBAN-telefon-prosa (konkret exempel med `"0555 5555 55"`/`"05 1234 5678"`, grundorsak på aggregator-nivå, motivering till att inte åtgärda i iteration 1, containment-regel som planerad åtgärd) flyttad ordagrant in under 14.1 - endast första meningen och avslutnings-meningarna i sista paragrafen ändrade.
- `git status` visar exakt två ändrade filer: `docs/arkitektur.md`, `docs/iteration_1_demoforberedelse.md`. Ingen kodfil rörd, inga tester ändrade.

**Beslut fattade:** Struktur: ingress + två grundorsaksblock (14.1/14.2) valdes framför att lägga till NER-FPs som ytterligare en flödande paragraf - per-grundorsak-gruppering matchar behovet att särskilja cross-recognizer-överlapp från modell-feldetekteringar inför demon. Alternativ B i Plan Mode-granskningen: "Åtgärden planeras för iteration 2:s Build-fas. Denna issue (#39) dokumenterar enbart begränsningen som underlag för framtida arbete." togs bort ur 14.1 - self-referensen till #39 var giltig när avsnittet enbart täckte IBAN-telefon men blir missvisande när avsnittet växer till strukturerat begränsningsregister och skulle annars bli stale när iteration 2 adresserar begränsningen; spårbarheten till #39 bevaras i git-historiken. "Åtta falska positiva" i 14.2:s första stycke speglar antalet NER-FPs efter PRS-fixen (#60) och testdata-fixen.
**Öppet/Nästa steg:** Commit sker efter granskning (ingen commit i denna session). Iteration 2 fattar beslut om primär mekanism (containment vs pre-filtrering vs kombination) utifrån intressentfeedback under demon.

#### Session 2026-04-20 - Cursor-agent (Opus) (docs-synk)

**Iteration:** 1 / v0.1.1
**Mål:** Lägga till statustabell och uppdatera DoD-checklistan i demoforberedelse.md så dokumentet speglar nuvarande läge efter dagens implementation.

**Ändrade filer:**
- `docs/iteration_1_demoforberedelse.md` - ny `## Status (uppdaterad 2026-04-20)`-sektion efter frontmatter med tabell över alla 16 issues + testdata-fix; DoD-checklistan uppdaterad med rätt `[x]` för uppfyllda punkter och PRS istället för PER; denna sessionspost.

**Gjort:**
- Statustabellen placerad före `## Kontext och ADR-motivering` så den är högt synlig.
- Tabellen listar `#`, `Issue`, `Ansvarig`, `Status`, `Sessionspost` för 16 poster (15 issues + testdata-fix).
- DoD-raden om EntityLayer uppdaterad från `spacy_PER/LOC/ORG` till `spacy_PRS/LOC/ORG` (synk med faktiska source-taggar efter #60).
- Verifierat via git status att endast `docs/iteration_1_demoforberedelse.md` är ändrad.

**Beslut fattade:** Tabellen placerad tidigt i dokumentet (efter frontmatter) snarare än som eget avsnitt längre ner - inför demon är dagsfärsk översikt det första intressenter/granskare vill se. Sessionspost-kolumnen refererar till datum (2026-04-18/2026-04-20) istället för issue-nummer för att undvika dubbel spårbarhet.
**Öppet/Nästa steg:** Återstående issues: #44 (spårbarhet per markering), #48 (demomanus + intervjufrågor), #54 (SSOT-drift), #55 (Beslut N i Loggboken). Commit sker efter granskning.

#### Session 2026-04-20 - Cursor-agent (Opus) (issue #54)

**Iteration:** 1 / v0.1.1
**Mål:** Lösa issue #54 - synka Category-enumen i SSOT avsnitt 3.3 mot gdpr_classifier/core/category.py. Tre driftspunkter: POSTORT/POSTNUMMER saknas i SSOT, RELIGIÖS_ÖVERTYGELSE har diakriter i SSOT men inte i koden, KONTEXTUELLT_KÄNSLIG skiljer sig på både nyckel (diakrit) och värde (kontextuellt_kanslig vs context.identifierbar).

**Ändrade filer:**
- `docs/arkitektur.md` - avsnitt 3.3 Category-enum: lagt till POSTORT/POSTNUMMER under Artikel 4-gruppen efter ADRESS och före BETALKORT; bytt nyckelnamnet RELIGIÖS_ÖVERTYGELSE till RELIGIOS_OVERTYGELSE (värdet redan matchande); bytt både nyckel KONTEXTUELLT_KÄNSLIG till KONTEXTUELLT_KANSLIG och värde "kontextuellt_kanslig" till "context.identifierbar" så båda matchar koden; prosa-paragrafen om prefix-konventionen verifierad och oförändrad.
- `docs/iteration_1_demoforberedelse.md` - denna sessionspost; statustabellens rad för #54 uppdaterad från "Ej påbörjad" till "Klar" med sessionspost-datum 2026-04-20.

**Gjort:**
- Verifierat att `gdpr_classifier/core/category.py` har POSTORT, POSTNUMMER, RELIGIOS_OVERTYGELSE utan diakriter, och KONTEXTUELLT_KANSLIG = "context.identifierbar".
- Tre exakta diff-punkter implementerade i avsnitt 3.3. Ingen kodfil rörd.
- `git status` visar exakt två modifierade filer.

**Beslut fattade:** SSOT anpassas till koden (dokumentation-only fix), inte tvärtom. Kommentaren "Kontextuellt känslig (identifierbar indirekt, iteration 3)" över KONTEXTUELLT_KANSLIG-raden behåller diakriterna eftersom den är prosa, inte Python-identifierare.
**Öppet/Nästa steg:** #55 (Beslut N i Loggboken) och #48 (demomanus + intervjufrågor) återstår av iteration 1:s backlog. Commit sker efter granskning.

#### Session 2026-04-20 - Cursor-agent (Opus) (SSOT docs-sync extra)

**Iteration:** 1 / v0.1.1
**Mål:** Efter implementation av #54 genomfördes en bredare docs-sync-scan av `docs/arkitektur.md` mot faktisk kodbas för att fånga driftpunkter utöver Category-enumen. Sex driftpunkter (D1-D4, D6-D7) åtgärdades; en sjunde (D5) flaggades som substansdrift som kräver designbeslut och lämnades orörd.

**Ändrade filer:**
- `docs/arkitektur.md` - frontmatter uppdaterad till v0.1.1 och datum 2026-04-20 (D6); Finding-exemplets source-kommentar bytt från `entity.spacy_person` till `entity.spacy_PRS` (D7, synkar mot SUC3-taggset som används av `sv_core_news_lg`); avsnitt 10 filstruktur-blocket synkat: `betalkort.py` tillagd under recognizers/ (D1), "stub iteration 1"-kommentaren på `entity_layer.py` bytt till "SpaCy sv_core_news_lg, aktiv från v0.1.1" (D4), tests/-blocket synkat mot faktiska testfiler (D3) - listade tester som inte finns borttagna (`test_personnummer.py`, `test_email.py`, `test_pattern_layer.py`, `test_aggregator.py`, `test_pipeline.py`), faktiska tester tillagda (`test_betalkort.py`, `test_evaluation_flow.py`, `test_loader.py`), samt `tests/dataset/test_dataset_offsets.py` inlagd som egen underkatalog; avsnitt 11 Iteration 1 "alla fyra recognizers" uppdaterat till "alla fem recognizers" (D2).
- `docs/iteration_1_demoforberedelse.md` - statustabell: ny `-`-rad för SSOT docs-sync extra; denna sessionspost.

**Gjort:**
- Systematisk korsreferens mellan SSOT avsnitt 3-11 och faktiska filer i `gdpr_classifier/`, `evaluation/`, `tests/`.
- Sex drift-punkter åtgärdade i docs; ingen kodfil rörd.
- D5 (aggregatorn elevear `context.*` till HIGH, vilket motsäger SSOT avsnitt 8 rad 360) dokumenterad separat och lämnad orörd: är substansdrift som kräver beslut om nuvarande kodbeteende är tänkt eller ska justeras. Hör sannolikt ihop med #55 (Beslut N: `context.*`-prefix och ORG-kategorisering). Inte en ren docs-fix.
- `git status` visar exakt två modifierade filer (samma två som #54-posten ovan).

**Beslut fattade:** Docs-sync följer samma SSOT-följer-kod-princip som #54. D5 separeras ut och hanteras som designbeslut, inte som tyst docs-sync, för att undvika att cementera ett potentiellt kod-bug (ORG-fynd från NER triggar HIGH) i dokumentationen utan granskning.
**Öppet/Nästa steg:** D5 behöver adresseras, antingen som del av #55 eller i ny issue ("aggregatorns hantering av `context.*`-fynd: kod-fix vs SSOT-uppdatering"). #48 (demomanus) återstår av iteration 1:s backlog.
