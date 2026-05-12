# Iteration 3: Implementationsplanering

**Projekt:** gdpr-classifier  
**Iteration:** 3 (v0.3.0-dev)  
**Period:** V19–V21  
**Metodik:** Scrumban (kanban-board i GitHub Projects)

> **[UNDER UPPBYGGNAD]** Denna fil är under aktiv uppbyggnad. Iterationsförberedelse pågår och specifik teknisk planering — inklusive issue-specifikationer, beroendekarta och förväntade resultat — fylls i löpande i takt med att planeringen för iteration 3 genomförs tillsammans med arkitekt-agenten. En framtida läsare (handledare, examinator eller annan agent) bör beakta att innehållet reflekterar ett pågående arbete och att tomma sektioner är avsiktliga platshållare.

**Startdatum:** 2026-05-07  
**Slutdatum (planerat):** 2026-05-20  
**Status:** Pågår

---

## Mål och scope

Iteration 3 är ADR:s Formalization of Learning-fas (Sein et al., 2011, princip 7). Iterationen är formaliseringsfokuserad: huvudbidraget är designkunskap formaliserad som designprinciper och arkitekturbeskrivning, inte ny funktionalitet. Iteration 3 är sista iterationen; det finns ingen iteration 4 som backup.

Iteration 3 har tre primära mål:

1. **Tvådimensionsoperationalisering.** Operationalisera tvådimensionsobservationen från iteration 2:s naturalistiska utvärdering — att identifierbarhet och dataskyddsklass är separata dimensioner med `SensitivityLevel` som derivat — enligt Beslut 37 i Loggboken. Reservplan per Beslut 39 om scope-tryck uppstår.

2. **FP-baslinjereduktion.** Reducera FP-baslinjen från iteration 2:s 117 falska positiva genom riktade åtgärder baserade på FP-rotorsaksanalysen 2026-05-04:
   - CombinationLayer prompt-skärpning för `context.yrke` och `context.organisation` (53 äkta FP)
   - matcher-aliasing för `article4.adress` kontra `context.plats` (17 FP plus motsvarande FN)
   - aggregator-deduplicering för same-category overlap över lager (11 FP)
   - promptförbättringar för svaga artikel 9-kategorier (`halsodata`, `etniskt_ursprung`, `religios_overtygelse`) per Beslut 33 från iteration 2

3. **Empirisk tröskelkalibrering.** Kalibrera aggregatorns trösklar (`medium_threshold`, `high_confidence_bypass`, `min_evidence_count`) enligt Beslut 20 från iteration 2 mot V1:s riktmärke om cirka 80 procents precision som tak, utan att kompromissa med recall under iteration 2:s baslinje på 89,27 procent. Per Beslut 41 schemaläggs kalibreringen som iterationens sista konstruktionssteg efter att alla övriga ändringar är committade.

**Sekundära mål:**
- Revidering av DP1-DP5 i AEGIS-rapportens kapitel 5.5 med stärkt Rationale-komponent per princip enligt Gregor, Chandra Kruse och Seidel (2020)
- Villkorad formulering av DP6 (kopplad till Beslut 38)
- Spårbarhetsmatris mellan designprinciper och iteration 1-2-empiri
- Färdigställande av arkitekturkapitel 5.3 med UML-klassdiagram
- Designcykel 3-avsnitten i kapitel 4.5
- Slutgiltig utvärderingssyntes i kapitel 5.4 efter iteration 3:s naturalistiska utvärdering med V1, V2 och V4

**Lågprioriterade utforskningar i mån av tid:**
- Modellskalningsprob via större molnmodell (V4:s rekommendation från iteration 2)
- Narrativ specificitet som strukturerad output i CombinationLayers JSON (med revideringsklausul: omprövas efter att övriga issues är committade)

**Out of scope för iteration 3** — dokumenteras som framtida arbete i rapportens kapitel 6.10:
- Schemautvidgning av CombinationLayers `allowed_signals` (Beslut 43)
- Implementation av artikel 10-lager för CRIMINAL-kategorin (Beslut 40)
- Guide-parser-duplikering mellan genereringsskripten (ren kodskuld utan vetenskaplig vikt)
- Strukturella mätfrågor som Cell 2-tröskelkalibreringens cirkularitet (redan dokumenterad i `data_statement.md`)

---

## Beroendekarta

Beroendekartan visar vilka issues som beror på varandra och i vilken ordning de bör implementeras, inklusive parallella spår och konvergenspunkter.

Iteration 3 organiseras i två konstruktionsspår som körs parallellt under första halvan av iterationen, en gemensam tung period i mitten med tvådimensionsoperationaliseringen, och en differentierad slutfas med tröskelkalibrering och intervjuförberedelse parallellt med rapport-finalisering.

**Spårtillhörighet:**
- Spår A1 (prompt-arbete): Abdulla
- Spår A2 (matcher- och aggregator-arbete): Johanna
- Spår A3 (tvådimensionsoperationalisering): Gemensamt med ansvarsdelning — Abdulla driver core-modell och aggregator, Johanna driver demogränssnitt och utvärderingsmodul
- Spår A4 (tröskelkalibrering): Johanna, granskas av Abdulla
- Spår B (formalisering och rapport): Delat enligt arbetsföljd
- Spår C (utvärdering): Gemensamt

```
              V19                              V20–V21

   Abdulla            Gemensam            Johanna
   ────────          ──────────          ─────────
   I-1  ──┐                             ┌── I-2
   I-19   │                             │   I-3
   I-4    │                             │
          └────────┐         ┌──────────┘
                   ▼         ▼
                    I-5 (tvådimension, efter I-3)
                          │
                          ▼
                    I-6 (tröskelkalibrering,
                         efter I-1…I-5)
                          │
   I-10 (DP6,             │
    villkorad             │
    på I-5)               ▼
                    I-18 (naturalistisk
                          utvärdering, efter I-6)
```

**Konkreta beroenden:**
- Issues I-1, I-2, I-3, I-4 har inga inbördes beroenden och körs parallellt i V19.
- Issue I-5 (tvådimensionsoperationalisering) ska komma efter I-3 (deduplicering) för att undvika merge-konflikter i aggregator-koden.
- Issue I-6 (tröskelkalibrering) körs när I-1 till I-5 är committade och ny baslinje är etablerad. Detta är iterationens sista konstruktionssteg.
- Issue I-18 (naturalistisk utvärdering) körs efter I-6 eftersom intressenterna ska se den slutkalibrerade artefakten.
- Issue I-19 (intervjuguide-revidering) ska vara klar tidigt i V19 för att intervjusessioner ska kunna bokas.
- Issue I-10 (DP6-formulering) är villkorat på I-5:s utfall per Beslut 38.

---

## Förväntade resultat

**Kvantitativa mål:**
- Recall bibehålls på eller över iteration 2:s baslinje (89,27 procent)
- Precision höjs mot V1:s riktmärke (cirka 80 procent) efter samtliga pipeline-ändringar och tröskelkalibrering
- FP-reduktion från iteration 2:s 117 till en nivå som motsvarar V1:s riktmärke; specifika delsiffror för Rotorsak 1, Rotorsak 3 och Tilläggsorsak från FP-rotorsaksanalysen
- Per-mekanism-statistik visar att Mekanism 3 aktiveras för åtminstone en del av kombinationsfynden efter tröskelkalibrering

**Kvalitativa mål:**
- DP1-DP5 har stärkt Rationale-komponent per princip enligt Gregor, Chandra Kruse och Seidel (2020)
- DP6 är antingen formaliserad eller dokumenterad som empirisk lärdom enligt Beslut 38
- Spårbarhetsmatrisen mappar varje designprincip mot iteration 1- och 2-empiri med uttryckliga referenser
- Arkitekturkapitel 5.3 är komplett med UML-klassdiagram och Composite-prosa
- Iteration 3:s naturalistiska utvärdering med V1, V2 och V4 är genomförd, transkriberad och tematiskt kodad; DC3-platshållarna i rapportens kapitel 5 är ifyllda

---

## Issue-specifikationer

Status-legenda: ✅ Klar | 🔄 Pågår | ⏸️ Blockerad | ⬜ Ej startad

> GitHub-issue-nummer börjar från första lediga nummer efter iteration 2:s sista issue (#96). Numren tilldelas vid skapande via `gh` CLI och tabellraderna uppdateras därefter. Iterationsinterna ID:n I-1 till I-20 reserveras nedan; titlar, spårtillhörighet, ansvarig, beroenden och formaliseringskonsekvens fylls i när respektive issue skapas.

| Issue | Titel | Spår | Ansvarig | Status | Beroenden | Formaliseringskonsekvens |
|---|---|---|---|---|---|---|
| [#101](https://github.com/Abdriano95/aegis/issues/101) (I-1) | Promptskärpning för CombinationLayer context.yrke och context.organisation | A1 | Abdulla | ⬜ Ej startad | Inga | Stärker DP1 Rationale; 4.5.2 ska uppdateras. |
| [#102](https://github.com/Abdriano95/aegis/issues/102) (I-2) | Matcher-aliasing för article4.adress och context.plats | A2 | Johanna | ✅ Klar (2026-05-12) | Inga | 5.3 (arkitekturbeskrivning) uppdateras med aliasing-mekanism. |
| [#103](https://github.com/Abdriano95/aegis/issues/103) (I-3) | Aggregator-deduplicering för same-category overlap över lager | A2 | Johanna | ⬜ Ej startad | Inga (I-5 berör samma kod) | 5.3 uppdateras med dedupliceringsregel. |
| [#104](https://github.com/Abdriano95/aegis/issues/104) (I-4) | Promptförbättringar för svaga artikel 9-kategorier | A1 | Abdulla | ⬜ Ej startad | Inga | Empiriskt material för DP1; 4.5.2 och 6.5/6.7 uppdateras. |
| [#105](https://github.com/Abdriano95/aegis/issues/105) (I-5) | Tvådimensionsoperationalisering enligt Variant 2 | A3 | Gemensamt | ⬜ Ej startad | I-3 | Villkorad DP6 (5.5); 5.3 klassdiagram och 4.4.3 uppdateras. |
| [#106](https://github.com/Abdriano95/aegis/issues/106) (I-6) | Empirisk tröskelkalibrering | A4 | Johanna | ⬜ Ej startad | I-1, I-2, I-3, I-4, I-5 | Stärker DP1 Rationale; 4.5.2 och 5.2 uppdateras. |
| [#107](https://github.com/Abdriano95/aegis/issues/107) (I-7) | Modellskalningsprob via större molnmodell | A1 | Johanna | ⬜ Ej startad | Inga (efter I-1–I-5) | Diskussionsmaterial för kapitel 6 (6.5/6.7). |
| [#108](https://github.com/Abdriano95/aegis/issues/108) (I-8) | Narrativ specificitet som strukturerad output | A1 | Abdulla | ⬜ Ej startad | Inga (revideras efter I-1) | Villkorad — 5.3 eller 6 beroende på utfall. |
| [#109](https://github.com/Abdriano95/aegis/issues/109) (I-9) | Revidering av DP1-DP5 med stärkt Rationale-komponent | B | Abdulla | ⬜ Ej startad | Påverkas av I-1–I-6 | Detta ÄR formaliseringsarbetet (5.5.1–5.5.5 revideras). |
| [#110](https://github.com/Abdriano95/aegis/issues/110) (I-10) | Villkorad formulering av DP6 | B | Abdulla | ⬜ Ej startad | I-5, I-18 | Detta ÄR formaliseringsarbetet (DP6 i 5.5 eller observation i 4.4.3/6). |
| [#111](https://github.com/Abdriano95/aegis/issues/111) (I-11) | Spårbarhetsmatris DP × iteration 1-2-empiri | B | Johanna | ⬜ Ej startad | I-9 | 5.4.4 eller bilaga får spårbarhetsmatris. |
| [#112](https://github.com/Abdriano95/aegis/issues/112) (I-12) | Färdigställande av arkitekturkapitel 5.3 | B | Abdulla | ⬜ Ej startad | I-5 | Detta ÄR formaliseringsarbetet (5.3 slutförs). |
| [#113](https://github.com/Abdriano95/aegis/issues/113) (I-13) | Reflektionsinslag i kapitel 4.4.3 och 6 | B | Gemensamt | ⬜ Ej startad | I-5, I-10, I-4, I-8 | Detta ÄR formaliseringsarbetet (4.4.3 och 6 reflektioner). |
| [#114](https://github.com/Abdriano95/aegis/issues/114) (I-14) | Designcykel 3-avsnitten i kapitel 4.5 | B | Gemensamt | ⬜ Ej startad | I-1–I-6, I-18 | Detta ÄR formaliseringsarbetet (4.5 slutförs). |
| [#115](https://github.com/Abdriano95/aegis/issues/115) (I-15) | Slutgiltig utvärderingssyntes i kapitel 5.4 | B | Johanna | ⬜ Ej startad | I-18 | Detta ÄR formaliseringsarbetet (5.4 slutförs). |
| [#116](https://github.com/Abdriano95/aegis/issues/116) (I-16) | Kapitel 6 (Diskussion) inklusive 6.10 framtida arbete | B | Gemensamt | ⬜ Ej startad | I-1–I-15 | Detta ÄR formaliseringsarbetet (kapitel 6 slutförs). |
| [#117](https://github.com/Abdriano95/aegis/issues/117) (I-17) | DC3-platshållarna genomgående i rapporten | B | Gemensamt | ⬜ Ej startad | I-18, I-5, I-6 | Detta ÄR formaliseringsarbetet (DC3-platshållare ifylls). |
| [#118](https://github.com/Abdriano95/aegis/issues/118) (I-18) | Iteration 3:s naturalistiska utvärdering med V1, V2 och V4 | C | Gemensamt | ⬜ Ej startad | I-6, I-19 | Genererar input till I-15, I-17, I-10. |
| [#119](https://github.com/Abdriano95/aegis/issues/119) (I-19) | Intervjuguide-revidering för iteration 3 | C | Gemensamt | ⬜ Ej startad | Inga | Styr I-18; ingen direkt rapportsektion. |
| [#120](https://github.com/Abdriano95/aegis/issues/120) (I-20) | SSOT-uppdateringar för docs/arkitektur.md | B | Abdulla | ⬜ Ej startad | I-1–I-6 | SSOT (`docs/arkitektur.md`) synkas mot slutartefakten. |

### Separat buggfix (utanför iterationsplanen)

Issue nedan bär `iteration-3`-labeln men ingår inte i de tjugo planerade arbetena (I-1 till I-20) och är inte kopplad till milestonen "iteration 3 / v0.3.0". Den dokumenteras separat för spårbarhet och hanteras sidoordnat under iterationen utan att räknas mot iterationens scope.

| Issue | Titel | Ansvarig | Status | Anmärkning |
|---|---|---|---|---|
| [#99](https://github.com/Abdriano95/aegis/issues/99) | test_schema_error_invalid_signal fallerar på main: CombinationLayerError kastas inte vid okänt signal-värde | Gemensamt | ⬜ Ej startad | Pre-existing buggrapport från 2026-05-03; `CombinationLayer`:s schema-validering kastar inte `CombinationLayerError` vid okänt signal-värde utanför `{"yrke", "plats", "organisation"}`. Beslut om åtgärdsväg (validator-fix kontra test-justering) tas i Loggboken. |

---

## Loggbok

Designbeslut för iteration 3 dokumenteras i Loggboken (Google Docs) under fliken **"Loggbok - iteration 3"**. Format: beslut, alternativ som övervägdes, motivering, koppling till GDPR-krav eller empiriskt stöd.

Denna fil listar inga beslut. Alla arkitektoniska och metodologiska avgöranden under iteration 3 förs in direkt i Loggboken med full motivering. Om ett beslut genereras under en agent-session ska det även noteras i sessionens post under "Beslut fattade" nedan, med hänvisning till Loggboken för längre motivering.

---

## Arbetsflöde

Iteration 3 följer samma nio-stegs-loop som iteration 1 och 2, beskriven i [`arbetsflode.md`](arbetsflode.md). Skillnaden mot iteration 1 är att Claude Code används som implementations-agent istället för Cursor: Claude Code tar emot issue-specifikationer, genererar plan i Plan Mode, och implementerar i Agent Mode efter användarens godkännande.

> Iteration 3 utökar issue-mallen med fältet **Formaliseringskonsekvens** per Beslut 42 (Loggbok – iteration 3). Fältet beskriver hur issue-utfallet matas tillbaka in i designprinciperna, arkitekturkapitlet eller spårbarhetsmatrisen.

---

## Agent-sessionslogg

### Regel

**Varje agent (AI eller människa) som arbetar i en session ska logga sin session här efter avslutad iteration.** Loggen är komplement till Loggboken ovan: Loggboken dokumenterar *beslut och motiveringar*, medan sessionsloggen dokumenterar *vad som faktiskt gjordes, i vilken ordning, och av vem*. Syftet är spårbarhet och att nästa agent (eller granskare) snabbt ska kunna förstå repots historik utan att läsa hela git-loggen.

### Format

Lägg till en ny post längst ner. Använd följande mall:

```markdown
### Session YYYY-MM-DD - [Agent/Person]

**Iteration:** [t.ex. 3 / v0.3.0]
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

<!-- Kommande sessionsposter läggs till här i kronologisk ordning. -->

### Session 2026-05-11 - Claude Code (Opus 4.7)

**Iteration:** 3 / v0.3.0-dev
**Mål:** Synkronisera stegantalet i arbetsflöde-loopen så att `CLAUDE.md`, `docs/arbetsflode.md` och `docs/iteration_3_implementation.md` är konsistenta, samt uppdatera arbetsflode.md:s terminologi till iteration 3:s praktik.

**Ändrade filer:**
- `docs/arbetsflode.md` - nytt steg 9 tillagt (sessionspost + statusuppdatering + Loggbok-inmatning) så loopen omfattar nio numrerade steg som matchar `CLAUDE.md` sektion 4; alla Cursor-referenser ersatta med Claude Code
- `docs/iteration_3_implementation.md` - Arbetsflöde-sektionen: "åtta-stegs-loop" → "nio-stegs-loop"; denna sessionspost tillagd

**Gjort:**
- Jämfört CLAUDE.md sektion 4 (rad 74-82, 9 numrerade steg) mot arbetsflode.md (rad 5-25, 8 numrerade steg) och identifierat att det saknade steget motsvarar CLAUDE.md:s steg 9 (sessionspost + statusuppdatering + Loggbok)
- Lagt till nytt steg 9 i arbetsflode.md i samma stil och detaljnivå som befintliga steg
- Cursor-referenserna i arbetsflode.md uppdaterade till Claude Code (fem instanser: "Cursor-prompt", "Cursor (Plan Mode)", "Cursor genererar", "Cursor (Agent Mode)", "Cursor gör implementationen"), så filen är aktuell mot iteration 3:s praktik
- Ändrat referenstexten i iteration_3_implementation.md från "åtta-stegs-loop" till "nio-stegs-loop"

**Rättelse av tidigare slutsats:** En tidigare plan-iteration utgick från att `docs/arbetsflode.md` var den auktoritativa referensen och att CLAUDE.md sektion 4 hade fel siffra. Den slutsatsen var omvänd. CLAUDE.md är korrekt; arbetsflode.md var ofullständig (saknade steg 9) och föråldrad i terminologi (Cursor-referenser). Ingen ändring gjordes i CLAUDE.md.

**Beslut fattade:** Inga arkitektoniska beslut. Stilval för det nya steget i arbetsflode.md följer befintliga steg.
**Öppet/Nästa steg:** Inga.

### Session 2026-05-11 - Claude Code (Opus 4.7) — issue-skapande

**Iteration:** 3 / v0.3.0-dev
**Mål:** Skapa 20 GitHub-issues för iteration 3 (I-1 till I-20) enligt specifikation från arkitekt-agenten, med korrekt body, labels, assignees och milestone-koppling, och uppdatera tabellen i denna fil med faktiska GitHub-nummer.

**Ändrade filer:**
- `docs/iteration_3_implementation.md` — tabellrader 122–143 ifyllda med #101–#120, titlar, spår, ansvariga, beroenden och formaliseringskonsekvens; denna sessionspost tillagd

**Gjort:**
- Skapat 10 nya labels i `Abdriano95/aegis`: `iteration-3`, `spar-A1`, `spar-A2`, `spar-A3`, `spar-A4`, `spar-B`, `spar-C`, `prio-hog`, `prio-medel`, `prio-lag`
- Skapat milestone "iteration 3 / v0.3.0" (number=1)
- Skapat 20 GitHub-issues #101 till #120 motsvarande I-1 till I-20, med fullständiga bodies (Beskrivning, Spår, Beroenden, Acceptanskriterier, Formaliseringskonsekvens, Förankring, Out of scope), labels, assignees och milestone-koppling enligt promptens spec
- Uppdaterat tabellen rad 122–143 med faktiska issue-nummer (länkade till GitHub-URL), titlar, spår, ansvariga, beroenden i I-N-format och formaliseringskonsekvens i kort form
- Issue-numren tilldelades monotont från #101 till #120 (I-N motsvarar #(100+N))

**Mappning I-N → GitHub-issue:**
- I-1 → #101, I-2 → #102, I-3 → #103, I-4 → #104, I-5 → #105
- I-6 → #106, I-7 → #107, I-8 → #108, I-9 → #109, I-10 → #110
- I-11 → #111, I-12 → #112, I-13 → #113, I-14 → #114, I-15 → #115
- I-16 → #116, I-17 → #117, I-18 → #118, I-19 → #119, I-20 → #120

**Beslut fattade:** Inga arkitektoniska beslut. Tre operativa antaganden bekräftades med användaren via AskUserQuestion innan implementationen:
- Issues med "Gemensamt" som ansvarig (I-5, I-13, I-14, I-16, I-17, I-18, I-19) fick båda användarna (`Abdriano95` och `Jozelle`) som GitHub-assignees
- Status-kolumnen behållen i tabellen och initierad med `⬜ Ej startad` för alla 20 rader
- I-6 fick endast `Jozelle` som assignee (Abdullas granskningsansvar hanteras via PR-review, inte assignee-fältet)

**Observerad avvikelse vid slutverifiering:** Sökning på `--label iteration-3` returnerade 21 issues istället för 20 — pre-existing issue #99 (`test_schema_error_invalid_signal fallerar på main`) bär också `iteration-3`-labeln men är inte kopplad till milestone "iteration 3 / v0.3.0". Detta är inte ett fel i denna sessions arbete (våra 20 issues #101–#120 har alla korrekt milestone, labels och assignees).

**Uppföljning samma session:** På användarens begäran adderades en separat sektion "Separat buggfix (utanför iterationsplanen)" direkt efter huvudtabellen, som dokumenterar #99 i en mini-tabell med Anmärkning-kolumn. #99:s GitHub-milestone lämnades oförändrad — buggen hanteras sidoordnat under iteration 3 utan att räknas mot de tjugo planerade arbetena.

**Öppet/Nästa steg:** Iteration 3-arbetet kan starta. Per beroendekartan (rad 66–95) körs I-1, I-2, I-3, I-4 parallellt i V19, och I-19 påbörjas tidigt för att möjliggöra bokning av V20:s intervjusessioner. I-6 är iterationens sista konstruktionssteg per Beslut 41 och körs först när I-1 till I-5 är committade. Inga andra filer ändrade i denna session.

### Session 2026-05-12 - Claude Code (Opus 4.7) — Issue #99

**Iteration:** 3 / v0.3.0-dev
**Mål:** Issue #99 — Åtgärda fallande test `test_schema_error_invalid_signal` genom att lägga till strikt enum-validering av `signal`-värdet i CombinationLayer.

**Ändrade filer:**
- `gdpr_classifier/layers/combination/combination_layer.py` — Ersatte log-and-skip vid okänt signal-värde med `raise CombinationLayerError`. Schemafel hanteras strikt; hallucinationer kvarstår med tolerant hantering enligt Beslut 29.
- `docs/iteration_3_implementation.md` — Statusuppdatering #99 (⬜ Ej startad → 🔄 Pågår vid sessionsstart → ✅ Klar 2026-05-12 vid sessionsslut) samt denna sessionspost.

**Gjort:**
- Identifierade att aktuell implementation (rad 106–112 i `combination_layer.py`) behandlade okänt enum-värde som hallucination (log-and-skip), vilket är fel kategorisering enligt Beslut 22 och Beslut 29:s avgränsning. Okänt enum-värde är schemafel, inte hallucination.
- Lade till `raise CombinationLayerError` med deskriptivt felmeddelande som följer befintlig konvention för schemafel i samma fil (jämför rad 118 `Invalid confidence value: ...` och rad 122 `Confidence must be a finite float ...`).
- Verifierade att riktade testet `test_schema_error_invalid_signal` nu passerar.
- Verifierade att samtliga 10 tester i CombinationLayer-suiten passerar, inklusive Beslut 29:s fyra hallucinationstester (`test_differentiated_validation_hallucinated_individual`, `test_differentiated_validation_reconstructed_combination`, `test_differentiated_validation_dropped_combination`, `test_differentiated_validation_normalized_whitespace`).
- Verifierade full test-suite: 164/165 tester passerar. Det enda failet (`tests/integration/test_end_to_end.py::test_end_to_end_pipeline_evaluation`) är `OSError: [E050] Can't find model 'sv_core_news_lg'` — en pre-existing miljöfråga (saknad spaCy svenska NER-modell i lokal venv), inte en regression från denna ändring. Felet ligger i NER-lagrets modell­laddning och är orelaterat till `CombinationLayer.detect()`.

**Beslut fattade:** Implementation enligt åtgärdsväg 1 i issue #99 (validator-fix, ej test-justering). Beslutsdokumentation i Loggboken (Google Docs, fliken "Loggbok – iteration 3"). Distinktion mot Beslut 29: schemafel (ogiltigt enum, saknad nyckel, fel typ på fält) → strikt validering; hallucination (text_span hittas inte) och ofullständig per-signal-output (saknade fält i enskild post) → tolerant skip enligt Beslut 29.

**Öppet/Nästa steg:** Inga. Issue #99 stängs efter användarens manuella git-commit och push enligt CLAUDE.md sektion 4 steg 8. Pre-existing miljöfråga med `sv_core_news_lg` ligger utanför denna sessions scope och kvarstår.

### Session 2026-05-12 - Manuell - README.md spaCy-modell-dokumentation

**Iteration:** 3 / v0.3.0-dev (utanför iterationsplanens 20 planerade arbeten)
**Mål:** Komplettera README.md:s Miljösetup-sektion med nedladdning av spaCy-modellen `sv_core_news_lg`.

**Ändrade filer:**
- `README.md` - Lade till `python -m spacy download sv_core_news_lg` i Miljösetup-kodblocket och ett textstycke som förklarar modellberoendet för EntityLayer.

**Gjort:**
- Identifierade luckan i README:s setup-instruktioner som orsakade `OSError: [E050]` under issue #99-sessionen 2026-05-12.
- Lade till nedladdningssteget mellan `pip install` och `pytest --co -q`.
- Lade till textförklaring av modellberoendet med referens till EntityLayer (Lager 2).

**Beslut fattade:** Inga arkitektoniska beslut. Ren dokumentationsfix.

**Öppet/Nästa steg:** Inga.

### Session 2026-05-12 - Claude Code (Opus 4.7) — Issue #102 (I-2)

**Iteration:** 3 / v0.3.0-dev
**Mål:** Issue #102 — Implementera matcher-aliasing mellan `article4.adress` och `context.plats` i evaluation/matcher.py för att lösa Rotorsak 1 från FP-rotorsaksanalysen 2026-05-04.

**Ändrade filer:**
- `evaluation/matcher.py` — Modul-konstant `CATEGORY_ALIASES` (frozenset av frozensets), hjälpfunktion `_are_aliased`, tvåpass-loop i `match()` (Pass 1 exakt → Pass 2 alias), uppdaterad docstring med ny regel 1b.
- `tests/unit/test_matcher.py` — 6 nya enhetstester: 4 obligatoriska (alias båda riktningar, exakt-företräde med båda orderingar, ej alias för obesläktade) + 2 robusthet (symmetri, alias-stjäl-inte-från-exakt).
- `docs/arkitektur.md` — Ny underrubrik 9.2.1 "Matcher-aliasing för kategorikrock" inom sektion 9.2 (efter Aggregering, före 9.3).
- `docs/iteration_3_implementation.md` — Statusuppdatering #102 (⬜ Ej startad → 🔄 Pågår vid sessionsstart → ✅ Klar 2026-05-12 vid sessionsslut) samt denna sessionspost.

**Gjort:**
- Statusuppdatering till 🔄 Pågår som första edit före kodändringar.
- Implementerade `CATEGORY_ALIASES = frozenset({frozenset({Category.ADRESS, Category.PLATS})})` på modulnivå för triviall framtida utökning.
- Implementerade `_are_aliased(a, b)` med self-aliasing → False (exakt-fall fångas redan av Pass 1) och robusthet mot okända kategorier via frozenset-membership.
- Restrukturerade `match()`:s inner-loop till tvåpass per prediktion: Pass 1 exakt-match (oförändrat beteende), Pass 2 alias-match endast om Pass 1 inte fann något. Confidence-sortering, `id(e)`-tracking och en-till-en-claiming oförändrade.
- 6 nya tester gröna; alla 6 befintliga matcher-tester orörda och gröna (12/12 i `test_matcher.py`).
- Hela testsviten grön: 171 passed, 0 failed (`pytest tests/`).
- SSOT-uppdatering 9.2.1 dokumenterar aliasstrukturen, tvåpass-logiken, motiveringen (Rotorsak 1) och hänvisning till Loggboken iteration 3.

**Avvikelse från issue-spec:** Issue-specen refererade till `Category.KONTEXTUELLT_PLATS`. Det faktiska enum-namnet i `gdpr_classifier/core/category.py` är `Category.PLATS` (string-värde `"context.plats"`). Implementationen använder det faktiska namnet enligt spec-instruktionen ("Om enum-värdet för `context.plats` har annat namn, använd det faktiska namnet och notera det i sessionsloggen").

**Designval (utöver spec):**
- `aliased_matches`-fält i `MatchResult` skippades. Information härledbar post-hoc via `p.category == e.category` på `true_positives`. Undviker mutable-list-default på `frozen=True` dataclass.
- SSOT-placering: ny underrubrik 9.2.1 inom sektion 9.2 (samlat med övrig matcher-dokumentation) snarare än egen sektion 9.6.
- `_are_aliased` returnerar False vid self-aliasing — exakt-fallet hanteras redan av Pass 1.

**Beslut fattade:** Aliasing på evaluation-sidan istället för dataset-fix eller EntityLayer-mapping-fix (lösning på Rotorsak 1). Beslut 11 om LOC → ADRESS-mappning står kvar. Designbeslut för aliasing-mekanismen förs in i Loggboken iteration 3 av Johanna utanför agent-flödet.

**Formaliseringskonsekvens (per Beslut 42):** AEGIS-rapportens kapitel 5.3 (arkitekturbeskrivning) behöver uppdateras med aliasing-mekanismen i utvärderingsramverket. Hanteras av Abdulla och Johanna utanför agent-flödet.

**Öppet/Nästa steg:** Baslinjekörning via `python run_evaluation.py` blockerad av separat runtime-bugg i CombinationLayer: LLM (qwen2.5:7b-instruct) returnerar signal-värdet `'person'` som ej finns i tillåten mängd `{organisation, plats, yrke}`, och den nya strikta validatorn från issue #99 kastar `CombinationLayerError`. Felet är frikopplat från matcher-ändringarna (vår diff rör endast `evaluation/matcher.py` och tillhörande tester). Ny baslinjemätning kan inte antecknas i denna session — väntar på antingen utökning av tillåtna signal-värden eller LLM-prompttuning för CombinationLayer (separat issue). Förväntad effekt enligt analys: FP ↓ ≈17 från 117, motsvarande FN ↓, recall ↑ marginellt, precision ↑ märkbart.
