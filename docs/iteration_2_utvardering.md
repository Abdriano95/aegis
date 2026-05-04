# Iteration 2: Utvärdering

**Projekt:** gdpr-classifier  
**Iteration:** 2 (BIE-cykel 2, naturalistisk formativ utvärdering)  
**Version under demo:** v0.2.0 (preliminärt — justeras vid demotillfället)  
**Datum:** [fylls i per session]  
**Deltagare (organisation):** Verksamhet 1,2,4
**Deltagare (namn, roll):** [fylls i per session]  
**Intervjuare:** Abdulla Mehdi och Johanna Gull

---

> **[UNDER UPPBYGGNAD]** Specifika demo-texter och intervjufrågornas exakta innehåll fylls i när iteration 2:s artefakt är implementerad och demonstrationsfokus är fastställt. Frågornas klassificering (återkommande / ny) fastställs efter analys av iteration 1:s utvärderingsresultat. Nuvarande innehåll är ett metodologiskt ramverk att fylla i.

---

## Metodologisk förankring

Utvärderingen genomförs som en naturalistisk formativ utvärdering i BIE-cykel 2, i enlighet med Venable, Pries-Heje & Baskerville (2016). Deltagarna möter artefakten i eller nära sin verkliga kontext (Authentic and Concurrent Evaluation). Syftet är formativt: resultaten styr iteration 3:s inriktning och bidrar till formalisering av Generalized Outcomes.

Utvärderingen är strukturerad kring tre FEDS-kriterier: **utility** (är systemet användbart för intressentens behov?), **efficacy** (fungerar systemet som avsett?), och **fit with organization** (passar systemet in i intressentens verksamhet?). Samma tre kriterier tillämpas som i iteration 1, i enlighet med ADR:s princip om Authentic and Concurrent Evaluation.

Intervjuerna är semistrukturerade och följer Kvale & Brinkmanns (2009) taxonomi med fyra frågetyper: *introducing* (öppnar ett tema och bjuder in spontana beskrivningar), *specifying* (konkretiserar och preciserar), *direct* (riktar uppmärksamhet mot en specifik aspekt), och *probing* (fördjupar och följer upp svar).

Iteration 2:s utvärdering fokuserar särskilt på Lager 3:s kontextuella analys och pusselbitseffekten (GDPR skäl 26): hur kombinationer av `context.*`-fynd i aggregatorn höjer känslighetsnivån till `MEDIUM`, och hur intressenterna upplever systemets förmåga att hantera indirekt identifierbarhet.

Intervjuguiden förfinas mellan iterationer i enlighet med ADR:s princip Reflection and Learning (Sein et al., 2011, s. 44). Frågor från iteration 1 återanvänds oförändrade eller revideras baserat på vad som redan besvarats och vad som kvarstår att undersöka. Frågor som besvarats tillfredsställande utelämnas. Nya frågor introduceras för att adressera det som är specifikt nytt i den aktuella iterationen — i iteration 2 gäller det framför allt kontextuell analys och kombinationslogik.

---

## Del 1: Demomanus

### Minut 0-3: Introduktion och kontext

Talepunkter (generiska):
- Presentera er själva och projektets syfte (GDPR-klassificering av fritext)
- Förklara artefaktens roll i projektet: iteration 2 utökar systemet med Lager 3 (kontextuell analys) utöver Lager 1 (mönsterigenkänning) och Lager 2 (NER)
- Beskriv sessionens upplägg: kort demo följt av semistrukturerad intervju
- Påminn om inspelning och konfidentialitet

> **[Platshållare]** Specifika talepunkter fastställs när demonstrationsfokus är fastställt.

### Minut 3-8: Fritext-demo live

Talepunkter (generiska):
- Visa demo-gränssnittet (fritext-vyn)
- Kör demo-text(er) live och låt resultaten visas
- Lyft fram Lager 3-fynd och `MEDIUM`-känslighetsnivå
- Förklara kombinationslogiken kort: enskilda `context.*`-fynd är inte personuppgifter i sig, men i kombination triggar de en höjd känslighetsnivå — pusselbitseffekten (GDPR skäl 26)
- Visa spårbarhet: vilket lager och vilken regel som producerade varje fynd

> **[Platshållare]** Demo-texter och specifika talepunkter fastställs när iteration 2:s artefakt är implementerad. Texterna ska demonstrera Lager 3:s kontextuella analys och pusselbitseffekten.

### Minut 8-10: Överbrygga till intervju

Talepunkter (generiska):
- Avrunda demon och tacka för uppmärksamheten
- Förklara att ni nu vill ställa några frågor om upplevelsen
- Påminn om att det inte finns rätt eller fel svar — det är er verksamhetskunskap och era reaktioner som är värdefulla

> **[Platshållare]** Specifika talepunkter fastställs när demonstrationsfokus är fastställt.

---

## Del 2: Intervjuguide

### Tema 1: Utility (ca 5 min)

Syfte: Bedöm om systemet upplevs leverera värde för intressentens kärnbehov att identifiera och hantera personuppgifter. Utforska om systemets funktioner matchar vad intressenten faktiskt behöver.

**F1.** [FEDS: utility | Kvale: typ fastställs senare]

> **[Platshållare]** Återkommande från iteration 1 [revideras] / Återkommande från iteration 1 [oförändrad] / Ny för iteration 2. Klassificering och innehåll fastställs efter analys av iteration 1:s utvärderingsresultat och i samband med arkitekturplanering för Lager 3.

**F2.** [FEDS: utility | Kvale: typ fastställs senare]

> **[Platshållare]** Återkommande från iteration 1 [revideras] / Återkommande från iteration 1 [oförändrad] / Ny för iteration 2. Klassificering och innehåll fastställs efter analys av iteration 1:s utvärderingsresultat och i samband med arkitekturplanering för Lager 3.

**F3.** [FEDS: utility | Kvale: typ fastställs senare]

> **[Platshållare]** Återkommande från iteration 1 [revideras] / Återkommande från iteration 1 [oförändrad] / Ny för iteration 2. Klassificering och innehåll fastställs efter analys av iteration 1:s utvärderingsresultat och i samband med arkitekturplanering för Lager 3.

---

### Tema 2: Efficacy (ca 5 min)

Syfte: Bedöm om systemet faktiskt lyckas identifiera det som är avsett att identifiera, inklusive kontextuellt känsliga texter där ingen enskild uppgift är en personuppgift men kombinationen är det.

**F4.** [FEDS: efficacy | Kvale: typ fastställs senare]

> **[Platshållare]** Återkommande från iteration 1 [revideras] / Återkommande från iteration 1 [oförändrad] / Ny för iteration 2. Klassificering och innehåll fastställs efter analys av iteration 1:s utvärderingsresultat och i samband med arkitekturplanering för Lager 3.

**F5.** [FEDS: efficacy | Kvale: typ fastställs senare]

> **[Platshållare]** Återkommande från iteration 1 [revideras] / Återkommande från iteration 1 [oförändrad] / Ny för iteration 2. Klassificering och innehåll fastställs efter analys av iteration 1:s utvärderingsresultat och i samband med arkitekturplanering för Lager 3.

**F6.** [FEDS: efficacy | Kvale: typ fastställs senare]

> **[Platshållare]** Återkommande från iteration 1 [revideras] / Återkommande från iteration 1 [oförändrad] / Ny för iteration 2. Klassificering och innehåll fastställs efter analys av iteration 1:s utvärderingsresultat och i samband med arkitekturplanering för Lager 3.

---

### Tema 3: Fit with organization (ca 5 min)

Syfte: Bedöm om systemet och dess utdata passar in i intressentens befintliga arbetsflöde och kravbild för GDPR-efterlevnad. Utforska praktiska förutsättningar för adoption.

**F7.** [FEDS: fit with organization | Kvale: typ fastställs senare]

> **[Platshållare]** Återkommande från iteration 1 [revideras] / Återkommande från iteration 1 [oförändrad] / Ny för iteration 2. Klassificering och innehåll fastställs efter analys av iteration 1:s utvärderingsresultat och i samband med arkitekturplanering för Lager 3.

**F8.** [FEDS: fit with organization | Kvale: typ fastställs senare]

> **[Platshållare]** Återkommande från iteration 1 [revideras] / Återkommande från iteration 1 [oförändrad] / Ny för iteration 2. Klassificering och innehåll fastställs efter analys av iteration 1:s utvärderingsresultat och i samband med arkitekturplanering för Lager 3.

**F9.** [FEDS: fit with organization | Kvale: typ fastställs senare]

> **[Platshållare]** Återkommande från iteration 1 [revideras] / Återkommande från iteration 1 [oförändrad] / Ny för iteration 2. Klassificering och innehåll fastställs efter analys av iteration 1:s utvärderingsresultat och i samband med arkitekturplanering för Lager 3.

---

### Iteration 2-specifika kompletteringsfrågor

> **[Platshållare]** Kompletteringsfrågor om Lager 3:s kontextuella analys och kombinationslogik fastställs efter att artefakten är implementerad och iteration 1:s utvärderingsresultat har analyserats.

---

### Intressent-specifika frågor

| Intressent | Fråga |
|-----------|-------|
| V1 | [Fylls i baserat på iteration 1-feedback och iteration 2:s scope] |
| V2 | [Fylls i baserat på iteration 1-feedback och iteration 2:s scope] |
| V4 | [Fylls i baserat på iteration 1-feedback och iteration 2:s scope] |

---

## Del 3: Antecknings-mall

### Session-metadata

- **Datum:**
- **Plats:**
- **Deltagare (namn, roll):**
- **Organisation:**
- **Inspelning:** J / N — filnamn:
- **Längd:**

### Demo-observationer

- **Spontana reaktioner under demo:**
- **Hantering av kända begränsningar:**
- **Tekniska problem:**

### Svar per tema

#### Tema 1: Utility – svar per fråga

*(F-nummer fylls i när intervjuguiden är fastställd)*

- **Sammanfattning:**
- **Citat:**

#### Tema 2: Efficacy – svar per fråga

*(F-nummer fylls i när intervjuguiden är fastställd)*

- **Sammanfattning:**
- **Citat:**

#### Tema 3: Fit with organization – svar per fråga

*(F-nummer fylls i när intervjuguiden är fastställd)*

- **Sammanfattning:**
- **Citat:**

### Intressent-specifika svar

- **Sammanfattning:**
- **Citat:**

### Tematiska koder (preliminärt — fyll på direkt efter intervjun)

Initiala koder hämtas från iteration 1:s tematiska analys. Nya koder — exempelvis kring kontextuell analys, kombinationslogik och pusselbitseffekten — läggs till löpande baserat på faktiska intervjusvar.

- [koder från iteration 1:s analys läggs in här när de är kända]
- [nya iteration 2-koder läggs till efter varje session]

### Övrigt som dök upp

---

## Del 4: Post-session checklist

- [ ] Säkerhetskopiera inspelningen
- [ ] Skriv initial reflektion (senast 24h efter sessionen)
- [ ] Transkribera
- [ ] Tematisk kodning v1
- [ ] Uppdatera Loggboken ("Loggbok - iteration 2"-fliken) och sessionslogg-post i `docs/iteration_2_implementation.md`
- [ ] Kommunicera 

---

## Del 5: Tolkning och analys över alla sessioner

### Cross-case-jämförelse per tematisk kod

Jämförelse av mönster och avvikelser över deltagare och organisationer. Vilka koder är konsistenta? Var skiljer sig intressentperspektiven åt?

### Identifiering av designinsikter

Vilka insikter från sessionsanalysen styr iteration 3:s inriktning? Koppla till FEDS-kriterierna: vad fungerar (utility, efficacy), vad behöver förändras (fit with organization)?

### Förankring i Loggboken

Alla designinsikter med full motivering dokumenteras i Loggboken ("Loggbok - iteration 2"-fliken, Google Docs). Formuleringen av Generalized Outcomes sker i iteration 3 baserat på det samlade underlaget från iteration 1 och 2.

---

## Del 6: Kvantitativa mätvärden — Pipeline-precisionsförbättring (#96)

Utöver den naturalistiska formativa utvärderingen med intressenter genomfördes inom #96 en kvantitativ mätning av pipelinens precision mot det automatiserade testdataset som etablerades i iteration 2. Mätningen är inte en FEDS-utvärdering utan ett komplement som ger iterationens artefakt en reproducerbar slutpunkt.

### Bakgrund och omgångar

Fyra omgångar av precisionsförbättring genomfördes inom #96. Utgångspunkten var baslinjen etablerad av #75 (Precision 55.35%, Recall 88.41%, F1 68.18%, FP=272). Förbättringsarbetet bedrevs med täta mät–analysera–justera-cykler:

- **Omgång 0 (baslinje, #75):** TP=209, FP=272, FN=27 — Precision 43.46%, Recall 88.56%, F1 58.27%
- **Omgång 1:** EntityLayer-filter för PRS-FPs (enkla förnamn, Beslut 30) — FP-reduktion mot omgång 0
- **Omgång 2:** Prompt-optimering för article9-kategorierna — fortsatt FP-reduktion
- **Omgång 3 (slutpunkt):** Aggregator-containment för article9-context-dubbeltaggning (Beslut 32) — se nedan

Slutpunkten fastställdes vid omgång 3 per Beslut 33: ytterligare optimering bedömdes ge avtagande avkastning och riskerade att sänka Recall, vilket strider mot designprincipen Recall > precision.

### Slutresultat — omgång 3

| Mätvärde | Värde |
|---|---|
| TP | 208 |
| FP | 123 |
| FN | 25 |
| Precision | 62.84% |
| Recall | 89.27% |
| F1 | 73.76% |

**Förändring mot baslinje (#75):** FP 272 → 123 (−149 falska positiva eliminerade). Recall bibehölls i praktiken: 88.41% → 89.27%.

### Reproduktionskörning (2026-05-03, #80)

En reproduktionskörning av samma pipeline-konfiguration (qwen2.5:7b-instruct, article9 v5, combination v4, aggregator med article9-containment-filter) genomfördes 2026-05-03 inom ramen för issue #80 (demo-snapshot). Resultatet:

| Mätvärde | Värde |
|---|---|
| TP | 208 |
| FP | 117 |
| FN | 25 |
| Precision | 64.00% |
| Recall | 89.27% |
| F1 | 74.55% |

Recall och FN är identiska med #96:s slutpunkt. FP-räkningen skiljer med 6 fynd (123 → 117) och precision/F1 marginellt högre. Variationen ligger inom förväntad marginal för LLM-baserade pipelines, eftersom LLM-output inte är deterministisk även med temperatur 0. Reproduktionen bekräftar #96:s slutpunkt som stabil och utgör underlag för den demonstrationsversion som används i naturalistisk utvärdering med V1, V2 och V4.

Reproduktionen är versionskontrollerad i `demo/snapshots/iteration_2_report.json` med commit-hash `49e00ce70985fa884cfa7f0287bae0f53a437c11` inbäddat i snapshot-metadatan, vilket möjliggör spårning till exakt pipeline-tillstånd vid körning.

### Per-kategori-noteringar

- **`article4.namn`:** Störst enskild FP-reduktion. SpaCy PRS-fynd för enkla förnamn utan efternamn (t.ex. "Anna", "Lars") filtrerades via EntityLayer-filtret (Beslut 30).
- **`context.organisation` och `context.yrke`:** FP-reduktion via promptjusteringar i omgång 2; kategorier som tidigare triggar på generella organisationsnamn och yrkestitel-liknande fraser.
- **`article9.halsodata` och `article9.etniskt_ursprung`:** Kvarstående FP-källorna i omgång 3 — se `arkitektur.md` sektion 14.3 för detaljer och iteration 3-planering.

### Kvarstående förbättringsområden

Identifierade begränsningar som inte åtgärdades inom #96 förs vidare till iteration 3. Se `docs/arkitektur.md` sektion 14.3 (Kvarstående begränsningar) för fullständig förteckning med grundorsaker.

---

## Del 7: FP-rotorsaksanalys — post-iteration 2 (2026-05-04)

En explorativ rotorsaksanalys av de kvarstående 117 FP:arna genomfördes efter iteration 2:s avslut, baserad på `demo/snapshots/iteration_2_report.json`. Analysen undersökte varje FP i förhållande till datasettens `expected_findings` för att särskilja äkta detektionsfel från strukturella orsaker i evaluering och dataset-design.

### Metod

För varje FP kontrollerades om ett expected-fynd med (a) samma kategori och (b) överlappande textspan existerade i datasetet. Tre scenarion identifierades:

- **Dubbeldetektion**: Expected finns och overlapperar — en annan prediktion har redan krävt expected-fyndet som TP (matcharen är en-till-en), och den aktuella prediktionen lämnas utan expected att matcha.
- **Kategori-kroch**: Expected finns och overlapperar i text, men med annan kategori — matcharen kräver exakt kategorimatch, vilket ger FP trots korrekt detekterad entitet.
- **Äkta FP**: Inget overlappande expected — prediktionen har ingen grund i datasetet.

### Resultat per kategori

| Kategori | Totalt FP | Dubbeldetektion | Kategori-krock | Äkta FP |
|---|---|---|---|---|
| `context.organisation` | 41 | 11 | 0 | 30 |
| `context.yrke` | 23 | 0 | 0 | 23 |
| `article4.adress` | 22 | 0 | 17 | 5 |
| `context.plats` | 15 | 0 | 10 | 5 |
| `article4.namn` | 3 | 0 | 0 | 3 |
| `article9.halsodata` | 4 | 0 | 0 | 4 |
| Övriga artikel 9 | 3 | 0 | 0 | 3 |
| `context.kombination` | 6 | 0 | 0 | 6 |

### Tre identifierade rotorsaker

**Rotorsak 1 — Kategori-kroch `article4.adress` / `context.plats` (17 FP:ar)**

Kombinationsdatasetet (`combination_dataset.json`) labelar ortsnamn som `context.plats`. EntityLayer mappar spaCy LOC → `article4.adress`. Matcharen kräver exakt kategorimatch, vilket skapar systematiska FP+FN-par för varje ort i kombinationsdatasetets texter:

```
Expected:     context.plats   "Malmö"   [combination_dataset]
EntityLayer:  article4.adress "Malmö"   → FP  (fel kategori)
Expected:     context.plats   "Malmö"   → FN  (ingen prediktion med rätt kategori)
```

Berörda samplar: 135–138, 141–144, 153–158. Alla orts- och platsreferenser i kombinationsdatasetet drabbas. Orsaken är att kombinationsdatasetet designades specifikt för att testa pusselbitseffekten (Lager 4) och labels-satte enbart `context.*`-kategorier — inte de grundläggande `article4.*`-kategorier som Lager 1+2 också producerar.

**Rotorsak 2 — Saknade grundlabels i kombinationsdatasetet (3+ FP:ar)**

Utöver ortskrocken saknar kombinationsdatasetet `article4.namn`-expected för namn som texterna faktiskt innehåller. EntityLayer (spaCy PRS → `article4.namn`) detekterar dessa korrekt men hittar inget expected att matcha:

```
Sample 134: "Professor Lars Eriksson, rektor på Hvitfeldtska..."
  Expected:     [context.yrke, context.organisation, context.kombination]
  EntityLayer:  article4.namn "Lars Eriksson"   → FP (saknar expected i datasetet)
```

**Rotorsak 3 — CombinationLayer övergenerering av `context.yrke`-signaler (23 FP:ar)**

CombinationLayerens LLM producerar `context.yrke`-fynd i texter från alla tre dataset. Felen delas in i tre undertyper:

- *Hallucineringar*: verb och fraser klassificeras som yrke — "leddes av", "protokollfördes av", "eskaleras till bedrägerienheten".
- *Felaktig entitetstyp*: namn klassificeras som yrke — "Erik Johansson", "Lars Berg" (borde vara `article4.namn`).
- *Korrekt men olabeled*: verkliga yrkestitlar som inte finns i expected — "systemutvecklare", "Projektledare" (iter1-datasetet labels-satte inte yrken för dessa texter).

**Tilläggsnotering — Dubbeldetektion `context.organisation` (11 FP:ar)**

EntityLayer och CombinationLayer detekterar oberoende samma organisationsnamn. Matcharen är en-till-en; CombinationLayerens signal (typiskt högre konfidens) kräver expected → TP; EntityLayerens fynd lämnas utan expected → FP. Dessa 11 FP:ar är inte fel i datasetet — de är ett strukturellt problem i hur matcharen hanterar redundanta detektioner från flera lager.

### Slutsatser för iteration 3

1. Kombinationsdatasetet behöver kompletteras med `article4.adress`- och `article4.namn`-expected för de texter som innehåller sådana entiteter. Alternativt: matcharen utökas till att acceptera kategori-alias (t.ex. `article4.adress` ≡ `context.plats` vid span-overlap).
2. CombinationLayerens prompt behöver skärpas för `yrke`-signaler: tydligare negativa exempelpar som exkluderar verb, namnfraser och alltför generiska rollbeskrivningar.
3. Dubbeldetektionsproblemet för `context.organisation` löses lämpligast via deduplicering av overlappande same-category-prediktioner i matcharen eller aggregatorn, inte i datasetet.
