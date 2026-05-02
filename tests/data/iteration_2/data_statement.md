# Data Statement: Artikel 9-texter

Detta dokument följer strukturen från Bender & Friedman (2018) "Data Statements for Natural Language Processing: Toward Mitigating System Bias and Enabling Better Science".

## 1. Curation Rationale

Detta dataset existerar för att möjliggöra systematisk utvärdering av gdpr-classifierns förmåga att direkt detektera särskilda kategorier av personuppgifter (artikel 9-data). Konstruktionen stödjer uppfyllandet av forskningsfråga RQ1.1 genom att förse systemets Article9Layer med representativa provfall för svenska språket. Metodiken följer en hybrid-ansats enligt Pilán et al. (2022) med LLM-genererade kandidater som sedan underkastas manuell oberoende granskning med konsensuskrav för att säkerställa högkvalitativ ground truth utan hantering av riktigt känsligt data (Privacy by Design).

## 2. Language Variety

- Språk: Svenska (sv-SE).
- Varietet: Företrädesvis formell och semiformell rikssvensk skriftspråklig text (även om simuleringar av slarvig chattkommunikation ingår). Regionala dialekter eller sociolekter är inte explicit eftersträvade men kan förekomma marginellt som artefakter av språkmodellens träningsdata.

## 3. Speaker Demographic

Ej tillämpligt. Texterna är uteslutande syntetiskt genererade av en språkmodell och representerar inga verkliga mänskliga författare.

## 4. Annotator Demographic

Granskningen av de syntetiska kandidaterna har utförts av två annoterare: Abdulla Mehdi och Johanna Gull. Båda är svensktalande studenter på kandidatprogrammet Systemarkitektur vid Malmö universitet. De har ämneskunskap inom datavetenskap och grundläggande utbildning i GDPR-lagstiftningens definitioner av personuppgifter.

## 5. Speech Situation

Texterna efterliknar skriftlig fritextkommunikation i en professionell men varierande arbetsmiljö. De syntetiska texterna representerar domäner såsom:
- E-postmeddelanden mellan kollegor eller till externa parter.
- Chattloggar från interna kommunikationssystem (t.ex. Slack, Teams).
- Interna anteckningar, ärendeloggar, mötesprotokoll och CRM-utdrag.
Målet är att simulera de kontexter där ostrukturerade personuppgifter vanligtvis sprids inom en organisation.

## 6. Text Characteristics

[Fylls i FAS B] (Detaljer kring textlängd, register och exakt ämnesfördelning per artikel 9-kategori efter granskning.)

## 7. Recording Quality

Ej tillämpligt. Datasetet innehåller enbart skriftlig text, ingen audio- eller videoinspelning har använts.

## 8. Other

**Kandidatgenerering:**
Den preliminära genereringen (FAS A) utfördes med språkteknologi. De syntetiska texterna togs fram med modellen `qwen2.5:7b-instruct` (via lokal Ollama-instans). Prompt-strategin instruerade modellen att generera realistiska, men helt fiktiva, arbetsplatstexter samt att ange förslag på korrekta annoteringar av artikel 9-fynd med tillhörande substring-positioner. Datumet för genereringen återfinns i filen `.candidates_metadata.json`.

**Känd begränsning (Cirkularitet):**
Utvärderings-LLM:n för Article9Layer-komponenten och LLM:n som genererat testkandidaterna är av samma typ (`qwen2.5:7b-instruct`). Denna potentiella metodologiska cirkularitet (modellen bedöms på texter som den själv har skrivit och förmodligen har lätt att "förstå") har adresserats genom manuell oberoende granskning i FAS B. Datasetet antas som godkänd testdata enbart i kraft av att granskarna har bekräftat att texterna och annoteringarna är logiskt och juridiskt korrekta ur ett mänskligt och rättsligt perspektiv, oberoende av vilken modell som skrev dem.

**Granskningsprotokoll:**
I FAS B granskade de två annoterarna genererade kandidattexter oberoende av varandra. Eventuella avvikelser i bedömningen löstes genom konsensusdiskussion. Endast kandidater där full konsensus nåddes inkluderades i den slutgiltiga datamängden.

## 9. FAS A2-revidering

Efter granskning av de ursprungliga kandidaterna (FAS A1) kasserades dessa på grund av frekventa missförstånd av kategorierna och icke-idiomatisk svenska från `qwen2.5:7b-instruct`. En ny genereringsomgång (FAS A2) utfördes med följande justeringar:

- **Annoteringsguide:** Genereringen integrerades med den nya, formella guiden (`docs/annotation_guidelines.md`). Modellen instruerades med kategorispecifika utdrag från denna guide vid varje genereringsanrop.
- **Genereringsstrategi:** Textgenereringen skedde iterativt och strikt per kategori, med explicita varningar inbäddade för att hindra vanliga kategoriförväxlingar (t.ex. att geografiskt ursprung felaktigt markeras som etnicitet).
- **Modellbyte:** Genereringen gjordes om med `gemma2:9b` via OllamaProvider. Den pragmatiska triggern var att Gemini-API:t konsekvent returnerade "resource exhausted"-fel. Den substantiella motiveringen vilar på tre ben:

  1. **Cirkularitetsreducering (Pilán et al., 2022).** FAS A1 använde `qwen2.5:7b-instruct` för både generering och utvärdering — samma modellfamilj (Alibaba). I FAS A2 används `gemma2:9b` (Google DeepMind) för generering och `qwen2.5:7b-instruct` (Alibaba) för utvärdering. Dessa modeller härstammar från skilda träningskorpusar, tokenizers och arkitekturella familjer, vilket reducerar risken att utvärderingsmodellen bedömer data som den "förstår bäst" av familjesläktskaps-skäl.

  2. **Konsekvent med Beslut 17.** Beslut 17 (Loggbok iteration 2) fastställer lokal LLM som primär exekveringsmiljö för hela systemets utvärderingslager. Att applicera samma princip på testdatagenerering är konsekvent med arkitekturens grundvärden — inte en avvikelse från dem.

  3. **Eliminerad tredjelandsöverföring.** Lokal körning innebär att ingen data skickas till extern part. Eftersom inga verkliga personuppgifter förekommer i syntetisk data är detta inte ett juridiskt krav, men för forskningsmetodologisk renlighet är lokal exekvering att föredra.

## 10. CombinationLayer-dataset (`combination_dataset.json`)

Detta avsnitt dokumenterar pusselbitseffekt-datasetet som annoteras enligt `docs/combination_annotation_guidelines.md`. Det skapades inom Issue #73 och kompletterar artikel 9-datasetet (`article9_dataset.json`).

### 10.1 Curation Rationale

Datasetet konstruerades för att möjliggöra utvärdering av CombinationLayer (Lager 4) samt empirisk grund för kalibrering av aggregatorns kombinationströsklar (Beslut 20). Identifierbarhetsbedömning enligt GDPR skäl 26 är till sin natur gradvis snarare än binär, vilket motiverade en mer komplex datastruktur än artikel 9-datasetet. Datasetet täcker fyra strukturella celler: tydligt identifierbara kombinationer (Cell 1), gränsfall (Cell 2), negativa kontroller utan signaler (Cell 3), och negativa kontroller med signaler men utan identifierbarhet (Cell 4). Cell 4 testar specifikt D5-korrigeringen i Beslut 19.

### 10.2 Language Variety

Svenska, samma som artikel 9-datasetet. Samtliga texter är skrivna på modern svensk standardprosa. Dialekter, regionala uttryck eller historiska språkformer förekommer inte.

### 10.3 Speaker Demographic

Inte tillämpligt. Texterna är syntetiskt genererade och representerar fiktiva avsändare.

### 10.4 Annotator Demographic

Annoteringen utfördes av samma två examensarbetstuderande som för artikel 9-datasetet (sektion 4). Modersmålstalare av svenska, båda i sista terminen av Systemarkitektur med inriktning mot programutveckling vid Högskolan i Borås. Granskningen genomfördes oberoende av varandra med konsensusupplösning via annoteringsguiden.

### 10.5 Speech Situation

Inte tillämpligt. Skriftliga texter, inga inspelningar.

### 10.6 Text Characteristics

Datasetet består av 27 syntetiskt genererade svenska texter, fördelade enligt:

- Cell 1 (tydligt identifierbara): 9 entries fördelade på Regel A (4), Regel B (3), Regel C (2)
- Cell 2 (gränsfall): 5 entries
- Cell 3 (inga signaler): 6 entries
- Cell 4 (signaler men inte identifierande): 7 entries

Texterna är 30-260 tecken långa och representerar arbetsplatskontexter (e-post, interna anteckningar, ärendeloggar). Totalt 46 individuella signaler (yrke 22, plats 14, organisation 10) plus 9 aggregat-fynd av typ `context.kombination`. Texternas innehåll är fiktivt; inga verkliga personer, händelser eller direkta personuppgifter förekommer.

### 10.7 Recording Quality

Inte tillämpligt. Datasetet innehåller enbart skriftlig text.

### 10.8 Other

**Kandidatgenerering (FAS A):**
Den preliminära genereringen utfördes med språkteknologi enligt FAS A-mönstret etablerat i Issue #71. Modellfamilje-asymmetri tillämpades: `gemma2:9b` (Google DeepMind) genererade kandidater medan `qwen2.5:7b-instruct` (Alibaba) används som utvärderingsmodell vid CombinationLayer-evaluering. Detta reducerar cirkularitetsrisken som beskrivs i Pilán et al. (2022). Genereringsskriptet (`scripts/generate_combination_candidates.py`) läste annoteringsguiden med git-hash-spårbarhet och injicerade kategorispecifika sektioner per cell-och-regel-kombination. Sex separata genereringskörningar utfördes: Cell 1 Regel A, B, C; Cell 2 gränsfall; Cell 3 utan signaler; Cell 4 med signaler men inte identifierande.

**Känd metodologisk begränsning (Cirkularitet i Cell 2):**
Cell 2 (gränsfall) är där tröskelkalibreringen sker enligt Beslut 20. Eftersom samtliga celler genererades automatiskt utan manuell konstruktion, och både genererings- och utvärderingsmodellen har sett guidens regler i sina respektive inferenskontexter, finns en cirkularitetsrisk att kalibreringen sker mot LLM-tolkning av guidens regler snarare än oberoende fakta. Denna begränsning accepterades pragmatiskt eftersom examensarbetets bidrag inte är testdatageneringsmetodologi. Manuell konstruktion av Cell 2-gränsfall noteras som potentiell förbättring för iteration 3.

**Schemaval och arkitektoniska begränsningar:**
Datasetet följer schemat `allowed_signals = {yrke, plats, organisation}` enligt CombinationLayer:s implementation (Issue #72). Ålder identifierades under guidens utformning som potentiellt stark identifierare men sköts till iteration 3 för att inte bryta koordinationsregeln för `gdpr_classifier/core/`. Artikel 9-kategorier exkluderas från schemat eftersom de redan triggar sensitivity via Lager 3.

**Aggregat-spans och narrativ specificitet:**
Aggregat-fynd (`context.kombination`) följer mekanisk min/max-regel: `text[min(starts):max(ends)]` av individuella signaler. Detta innebär att Regel C-bedömningar vars identifierbarhet drivs av narrativ specificitet (tidsmarkörer, händelsereferenser, demografiska detaljer) får aggregat-spans avgränsade till individuella signal-positioner, även när den narrativa kontexten ligger utanför dessa positioner. Detta är ett medvetet val för att ground-truth ska matcha vad CombinationLayer faktiskt producerar. Den narrativa kontexten dokumenteras i varje entrys `description`-fält.

**Granskningsprotokoll (FAS B):**
60 ursprungliga kandidater togs ej fram — FAS A producerade 29 kandidater (1 droppad i Cell 1 Regel A på grund av text_span under 5 tecken). Annotörerna granskade alla 29 kandidater oberoende av varandra. Inter-rater agreement: 22/29 = 75,9% strikt enighet på beslutsnivå (Behåll/Justera/Stryk). Konsensusupplösning skedde via annoteringsguiden enligt sektion 8 i `docs/combination_annotation_guidelines.md`. Resultat: 25 entries behållna (varav 21 justerade), 4 strukna. Två manuellt kompletterande Regel C-entries genererades efter konsensus för att täcka cellens krav om narrativ specificitet — dessa konstruerades med direkt span-verifiering snarare än via genereringsskriptet, vilket noteras som avvikelse från primär genereringsmetod.

**Begränsningar för utvärderingsanvändning:**
Datasetet är litet (27 entries) jämfört med modern NLP-praxis och utvärderingen är därför formativ snarare än summativ. Resultaten ger indikation om CombinationLayer:s prestanda och underlag för tröskelkalibrering, men inte statistiskt robusta mått. Detta är konsistent med examensarbetets DSR-positionering där datasetet är instrument för designkunskap, inte slutgiltig benchmark. Iteration 3 förväntas utvidga datasetet baserat på iteration 2:s utvärderingsutfall.