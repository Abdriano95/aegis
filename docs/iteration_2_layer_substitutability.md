# Layer-protokollets utbytbarhet: empirisk evidens (Issue #79)

**Datum:** 2026-05-03  
**Issue:** #79 (I-12) - Layer-protokollets utbytbarhet med stub-Layer  
**Branch:** `79-layer-protokollets-utbytbarhet-med-stub-layer`

---

## 1. Git diff-sammanställning

Följande filer skapades under issue #79. Inga ändringar gjordes i
`gdpr_classifier/core/`, `gdpr_classifier/pipeline.py` eller
`gdpr_classifier/aggregator.py` - detta är en förutsättning för att
demonstrationen ska utgöra giltig empirisk evidens för Beslut 18.

### Skapade filer

| Fil | Beskrivning |
|-----|-------------|
| `tests/fixtures/__init__.py` | Gör `tests/fixtures/` till Python-paket |
| `tests/fixtures/stub_combination_layer.py` | StubCombinationLayer - testfixtur |
| `tests/unit/test_stub_combination_layer.py` | 8 enhetstester för stubben |
| `scripts/demonstrations/stub_substitution.py` | Demonstrationsskript (Run A / Run B) |
| `docs/iteration_2_layer_substitutability.md` | Denna fil |

### Ändrade filer

| Fil | Beskrivning |
|-----|-------------|
| `docs/iteration_2_implementation.md` | Issue #79 status uppdaterad |

### Bekräftelse: inga ändringar i skyddade filer

Kommandot `git diff --stat main..HEAD` visar inga ändringar i:

- `gdpr_classifier/core/` (Layer-protokollet, Finding, Category, Classification)
- `gdpr_classifier/pipeline.py` (Pipeline-orchestreringen)
- `gdpr_classifier/aggregator.py` (Aggregator med Mekanism 1, 3 och bypass)

Pipeline och Aggregator använder StubCombinationLayer identiskt med
CombinationLayer - utan en enda kodändring utanför stubben själv.

---

## 2. Jämförelsetabell: CombinationLayer (A) vs StubCombinationLayer (B)

| Text (<=80 tecken) | Sens A | Mek A | Fynd A | Sens B | Mek B | Fynd B |
|---|---|---|---|---|---|---|
| Förslagsgruppen bestod av VD för Hvitfeldtska gymnasiets musiklinje och professo... | medium | bypass | 5 | medium | bypass | 5 |
| Rektor på Hvitfeldtska gymnasiets musiklinje har bett mig att kontakta läkare i ... | high | article9 | 6 | high | article9 | 6 |
| Professor Lars Eriksson, rektor på Hvitfeldtska gymnasiets musiklinje, meddelade... | medium | bypass | 6 | low | low | 2 |
| En legitimerad tandläkare vid Västra Götalandsregionens tandvårdscenter i Borås ... | medium | bypass | 6 | low | low | 2 |
| Sjuksköterskan på intensivvården vid Sahlgrenska Universitetssjukhuset i Götebor... | medium | bypass | 7 | medium | bypass | 7 |
| Förläggaren för den nya elbilen, Volvo Cars, har etablerat ett produktionscenter... | low | low | 3 | low | low | 1 |
| Avdelningschefen på vårdcentralen i Karlskoga diskuterade med den nya sjuksköter... | medium | bypass | 4 | low | low | 1 |
| Den nya enhetschefen som tillträdde i januari efter omorganisationen vid Sahlgre... | medium | bypass | 4 | none | none | 1 |
| Den första kvinnliga produktionschefen på Volvo Cars Skövde, som rekryterades fr... | medium | bypass | 3 | none | none | 0 |
| Det nya lagret på industrivägen öppnar i morgon och de första anställda börjar s... | low | low | 2 | low | low | 1 |
| Under mötesdagen diskuterade projektledaren och den ekonomiska experten från huv... | low | low | 5 | low | low | 1 |
| Han jobbade som projektledare på den kommunala vårdcentralen i Karlskrona under ... | medium | bypass | 4 | low | low | 1 |
| På mötet diskuterade vi med den nya ekonomichefen hur projektet skulle drivas fr... | medium | bypass | 4 | low | low | 1 |
| Det var en anställd på receptionen som berättade att de nya systemen för bokning... | none | none | 2 | none | none | 0 |
| Den automatiserade processen aktiverades klockan 14.37. En loggsändning registre... | none | none | 0 | none | none | 0 |
| Systemet registrerar automatiskt alla förändringar i databasen. Varje uppdaterin... | none | none | 0 | none | none | 0 |
| Protokollen för uppdatering av databasen kommer att ske vid två tillfällen per d... | none | none | 0 | none | none | 0 |
| En ny regel för hantering av digitala filer implementeras den 15 november. Det i... | none | none | 0 | none | none | 0 |
| Automatiserad processen genomfördes enligt schema. Dataanalysen visade en ökning... | none | none | 0 | none | none | 0 |
| Enligt protokoll från den senaste iterationen ska den optimerade modellen gå ige... | none | none | 0 | none | none | 0 |
| Lagledningen på konferensen diskuterade vikten av att anställa fler medarbetare ... | none | none | 1 | none | none | 0 |
| Att jobba som försäljningskonsult i Malmö kan vara utmanande, men också väldigt ... | low | low | 2 | low | low | 1 |
| På mötet diskuterade vi behovet av fler lärare inom den digitala utbildningen i ... | low | low | 3 | medium | bypass | 4 |
| Förra veckan deltog många lärare från Stockholm i konferensen om digitalisering ... | low | low | 3 | medium | bypass | 4 |
| På mötet diskuterade vi hur många anställda som arbetade på kontoret i Stockholm... | low | low | 2 | low | low | 1 |
| Det är alltid roligt att träffa nya kollegor på konferenser. I år var många från... | low | low | 3 | low | low | 1 |
| Vi har fått många ansökningar om tjänster som ekonomichef i Malmö, men det var s... | low | low | 3 | low | low | 1 |

*Fylls i av `scripts/demonstrations/stub_substitution.py` efter manuell körning
mot Ollama med modell `qwen2.5:7b-instruct`.*

*Körning B (StubCombinationLayer) kräver fortfarande Ollama för Article9Layer (Lager 3).*

---

## 3. Reflexion

### Vad evidensen styrker

Layer-protokollets schema-identitetskontrakt - `@property name: str` och
`detect(text: str) -> list[Finding]` - är tillräckligt som kontraktsyta för att
byta ut CombinationLayer mot StubCombinationLayer utan att röra Pipeline,
Aggregator eller någon core-modul. Pipeline itererar över `self.layers` och anropar
`layer.detect(text)` för varje element; det spelar ingen roll vilket konkret lager
som ligger i listan så länge det uppfyller protokollet. Aggregatorn behandlar
StubCombinationLayerens fynd identiskt med CombinationLayerens: `context.kombination`-fynd
med konfidens >= 0.90 triggar hög-konfidens-bypass och returnerar MEDIUM-klassificering
med mechanism_used="bypass".

Det empiriska resultatet av Run A och Run B bekräftar vad Beslut 18 (Loggbok
iteration 2) formulerar teoretiskt: Pipes and Filters-mönstrets utbytbarhet
(Buschmann et al., 1996) är realiserad i denna pipeline utan att konsumerande
komponenter behöver ändras.

### Vad evidensen inte styrker

Evidensen visar inte att StubCombinationLayer och CombinationLayer är funktionellt
ekvivalenta. Stubben matchar deterministiskt mot en hårdkodad ordlista - den
producerar exempelvis kombinationer för texter där CombinationLayer korrekt
bedömt att lågsignaler som "lärare" och "Stockholm" ensamma inte uppfyller
identifierbarhetskravet. Jämförelsetabellen visar tydliga skillnader i sensitivity
och findings_count för flera texter i Cell 4 (signaler utan identifierbarhet).

Evidensen styrker inte heller utbytbarhet av lager med ett annat output-schema.
Ett hypotetiskt lager som bara returnerar aggregat (utan individuella signalsignaler)
eller som använder andra source-taggar än `context.{yrke|plats|organisation}` och
`context.kombination` skulle behandlas annorlunda av Aggregatorn och delvis av
konsumerande utvärderingslogik. Schema-identitet är en förutsättning för friktionsfri
utbytbarhet - protokollets namnkontrakt är nödvändig men inte tillräcklig för
semantisk ekvivalens.

Evidensen styrker inte utbytbarhet för lager med annan aritet, exempelvis ett lager
som producerar bara aggregat utan individuella signaler. Aggregatorns Mekanism 3
räknar på Lager 1/2-fynd (source startar på "pattern." eller "entity.") för att
validera kombinationsfynd - det är ett kontraktsansvar för konsumenter av Layer-protokollet
att förstå vilka source-taggar som används.

### Föranledda frågor för iteration 3

Skillnaden mellan Run A och Run B i jämförelsetabellen - särskilt för Cell 4-texter
där stubben producerar MEDIUM men CombinationLayer returnerar NONE - belyser att
protokollets utbytbarhet är ett arkitekturellt egenskapspåstående, inte ett funktionellt
ekvivalenspåstående. I iteration 3:s Generalized Outcomes-fas bör Designprincip 2
formuleras med denna distinktion: Layer-protokollet garanterar kompositionell
utbytbarhet (Pipeline behöver inte ändras), men den semantiska innebörden av
utbytet beror på den utbytande komponentens detektionslogik. Denna empiri kan
användas som underlag för att precisera vad "utbytbarhet" innebär i kontexten
av GDPR-klassificering där recall > precision.
