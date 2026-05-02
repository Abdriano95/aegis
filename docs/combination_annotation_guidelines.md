# Annoteringsguide: Pusselbitseffekten (CombinationLayer)

Version: Utkast 1 (2026-05-02) Författare: Abdulla Mehdi och Johanna Gull Status: Utkast för diskussion. Committas som docs/combination_annotation_guidelines.md när konsensus uppnåtts. Auktoritativ referens för: Issue #73 (testdataset, pusselbitseffekt-texter), FAS A:s genereringsskript och FAS B:s manuella granskning.

---

## 1. Syfte och scope

Denna guide etablerar gränsdragningskriterier för annotering av pusselbitseffekten enligt GDPR skäl 26. Den används i tre sammanhang. För det första läser FAS A:s genereringsskript guiden och injicerar relevanta sektioner i prompten per cell, så att kandidattexter genereras enligt explicita kategoriseringskrav. För det andra fungerar guiden som auktoritativ referens i FAS B när Abdulla och Johanna granskar oberoende. Konsensus vid avvikelser uppnås via guidens kriterier utan subjektiv kompromiss. För det tredje förankrar guiden bedömningarna juridiskt mot GDPR och tillgänglig vägledning, så att avgörandena går att försvara akademiskt.

Guiden täcker enbart det som är CombinationLayer:s ansvar enligt arkitektur.md sektion 6.2. Direkta personuppgifter enligt artikel 4 (personnummer, mejladresser, telefonnummer, IBAN, kortnummer) hanteras av Lager 1 och annoteras inte här. Personnamn, fullständiga adresser och plats-entiteter som geografisk information hanteras av Lager 2 och annoteras inte här. Artikel 9-data (hälsa, etniskt ursprung, politisk åsikt, religiös övertygelse, fackmedlemskap, biometrisk data, genetisk data, sexuell läggning) hanteras av Lager 3 enligt docs/annotation_guidelines.md och annoteras inte här.

Det som annoteras enligt denna guide är textavsnitt som i kombination kan göra
en individ identifierbar utan att direkta identifierare förekommer. Tre
signaltyper ingår i schemat: yrke, plats och organisation. Detta är ett
medvetet avgränsat schema motiverat av Beslut 18-19 (separation av kombinations-
logik från artikel 4 och artikel 9-detektion) och av implementationsläget i
#72. Andra potentiella signaltyper, exempelvis ålder, har övervägts men sköts
till iteration 3, se sektion 9. En fjärde dimension, narrativ specificitet,
används som bedömningsdimension för identifierbarhetsbedömningen men annoteras
inte som egen signal-typ.

## 2. Juridisk förankring

GDPR skäl 26 fastställer att man vid bedömning av om en uppgift är personuppgift ska ta hänsyn till "alla medel som rimligen kan komma att användas av den personuppgiftsansvarige eller av en annan person för att direkt eller indirekt identifiera en fysisk person". Detta är pusselbitseffektens juridiska kärna. En enskild kontextsignal som "lärare" eller "i Borås" är inte en personuppgift. I kombination kan flera signaler peka ut en specifik individ, och då omfattas hela kombinationen av artikel 4.1:s definition av personuppgift.

Artikel 4.1 definierar personuppgift som "varje upplysning som avser en identifierad eller identifierbar fysisk person". Ordet "identifierbar" är centralt. En person är identifierbar när hen kan särskiljas från andra, direkt eller indirekt, genom hänvisning till en eller flera faktorer som är specifika för individens fysiska, fysiologiska, genetiska, psykiska, ekonomiska, kulturella eller sociala identitet.

EU-domstolens dom i mål C-582/14 (Breyer mot Tyskland, ECLI:EU:C:2016:779) klargjorde att även information som kräver att flera källor kombineras kan utgöra personuppgift. Domstolen slog fast att "rimliga medel" inte kräver att identifieringen är möjlig för den personuppgiftsansvarige ensam, utan räcker med att den är möjlig genom kombination av tillgängliga uppgifter. Detta stödjer pusselbitseffektens centrala antagande att signaler vars enskild informationsvärde är låg kan, i kombination, möjliggöra identifiering.

IMY:s vägledning om personuppgiftsbegreppet bekräftar att indirekta identifierare omfattas av regelverket. Vägledningen ger exempel där "yrkestitel i kombination med arbetsplats och ort" pekas ut som potentiellt identifierande, vilket motsvarar de tre signaltyper som CombinationLayer detekterar.

Sammantaget är den juridiska principen klar: identifierbarhet är gradvis, beroende av kombinationens specificitet och kontextens "rimliga medel". Den operationella översättningen till annoteringskriterier är guidens uppgift och hanteras i sektion 4 och 5.

## 3. Signaltyper

CombinationLayer detekterar tre signaltyper. Varje signal annoteras som ett individuellt fynd med diskret minimalspann. Sammansatta spans tillåts inte för individuella signaler eftersom det skulle bryta #72:s implementation.

### 3.1 Yrke

Yrke avser en yrkesroll, titel eller funktion som beskriver vad en person gör. Det inkluderar formella titlar (chef, lärare, sjuksköterska, ekonomichef), generiska beskrivningar (anställd, medarbetare, frivillig) och specifika rollbeskrivningar (handläggare, projektledare, samordnare). Annoteringen ska vara minsta möjliga textsträng som identifierar yrket. I texten "Min chef på lagret" annoteras "chef" som yrke, inte "chef på lagret".

Sammansatta yrkesbeskrivningar med inbyggd specifikation, exempelvis "lärare i klassisk arabiska" eller "kirurg specialiserad på njurtransplantation", annoteras endast huvudordet som yrke ("lärare", "kirurg"). Specifikationen tas in som narrativ kontext i identifierbarhetsbedömningen enligt sektion 5 men annoteras inte som del av yrkes-spannet.

### 3.2 Plats

Plats avser geografiska platser som orter, stadsdelar, kommuner eller regioner. Det inkluderar stadsnamn (Borås, Stockholm, Hjo), stadsdelar (Linnéstaden, Hisingen), kommuner (Härryda kommun) och bredare regioner (Västra Götaland, Norrland). Annoteringen är minsta möjliga textsträng som identifierar platsen.

Adresser och gatunamn omfattas av Lager 2:s NER-detektion (LOC-entiteter) och annoteras inte som plats-signal i CombinationLayer. Gränsen är pragmatisk: om texten innehåller "Storgatan 5 i Borås" är "Storgatan 5" Lager 2:s ansvar och "Borås" är CombinationLayer:s plats-signal.

Beskrivande lokala referenser utan formellt platsnamn, exempelvis "den lilla bruksorten i Småland" eller "stationen vid älven", annoteras inte som plats-signal. De tas in som narrativ specificitet enligt sektion 5.

### 3.3 Organisation

Organisation avser företag, myndigheter, föreningar, institutioner eller arbetsplatser med formellt eller etablerat namn. Det inkluderar myndigheter (Skatteverket, Försäkringskassan), företag (Volvo Cars, IKEA), kommunala förvaltningar (Borås Stad, Göteborgs Stad), utbildningsinstitutioner (Högskolan i Borås, Hvitfeldtska gymnasiet) och vårdinrättningar (Sahlgrenska Universitetssjukhuset).

Generiska arbetsplatsreferenser utan namn, exempelvis "lagret", "kontoret", "fabriken", annoteras som organisation om kontexten antyder en specifik plats. Bedömningen är pragmatisk och styrs av sektion 4:s kriterier för organisationsspecificitet.

Avgränsning mot Lager 2: Lager 2:s NER-modell detekterar ORG-entiteter som mappas till context.organisation enligt Beslut 11. CombinationLayer:s detektion överlappar därför med Lager 2 för namngivna organisationer, men D5-korrigeringen i Beslut 19 säkerställer att isolerade context.*-fynd från Lager 2 inte ensamma höjer sensitivity. För testdatasetet annoteras ground-truth-organisationer enligt CombinationLayer:s perspektiv, alltså som context.organisation.

## 4. Specificitetskategorisering

Varje signal kategoriseras i en av tre nivåer baserat på hur mycket den smalnar av populationen av möjliga individer. Kategoriseringen är guidens hjärta och den är avgörande för identifierbarhetsbedömningen i sektion 5.

### 4.1 Yrkesspecificitet

Låg specificitet. Yrket beskriver en stor population utan ytterligare avgränsning. Hit hör generiska titlar som "anställd", "medarbetare", "tjänsteman", samt vanliga yrken med stor population som "lärare" (utan ämne), "sjuksköterska" (utan specialisering), "ekonom", "ingenjör".

Mellan specificitet. Yrket beskriver en avgränsad yrkesgrupp men inte en unik roll. Hit hör specialiserade yrken som "barnmorska", "narkossköterska", "skatterevisor", "patentingenjör", samt chefsroller på generell nivå som "avdelningschef", "HR-chef", "ekonomichef".

Hög specificitet. Yrket beskriver en unik eller nästan unik roll inom sitt sammanhang. Hit hör seniora chefsroller ("VD", "rektor", "förvaltningschef"), specifika fackmännrolller ("hovrättsdomare", "narkosläkare med transplantationsspecialisering"), och kombinationer av roll och specialisering ("lärare i klassisk arabiska", "lektor i medeltidshistoria").

### 4.2 Platsspecificitet

Låg specificitet. Platsen beskriver en stor geografisk region med många invånare. Hit hör Stockholm, Göteborg, Malmö, Uppsala (storstadsområden över 200 000 invånare), samt regionsbeskrivningar som "Västra Götaland", "Skåne", "Norrland".

Mellan specificitet. Platsen beskriver en mellanstor stad eller region. Hit hör städer mellan 30 000 och 200 000 invånare som Borås, Linköping, Helsingborg, Norrköping, Jönköping, samt mindre kommuner med tydlig avgränsning som Härryda eller Lerum.

Hög specificitet. Platsen beskriver en liten ort eller stadsdel. Hit hör orter under 30 000 invånare som Hjo, Trosa, Töreboda, samt namngivna stadsdelar inom större städer som Linnéstaden, Majorna, Mariehem, Östra Centrum.

### 4.3 Organisationsspecificitet

Låg specificitet. Organisationen är en riksomfattande myndighet, ett multinationellt företag eller en stor offentlig verksamhet med tusentals eller tiotusentals anställda. Hit hör Skatteverket, Försäkringskassan, Migrationsverket, Volvo Cars-koncernen, IKEA, Ericsson, Polismyndigheten.

Mellan specificitet. Organisationen är en regional aktör, ett mellanstort svenskt företag eller en kommunal förvaltning. Hit hör Borås Stad, Göteborgs Stad (som kommun), Volvo Cars Skövde (som specifik fabrik), Sahlgrenska Universitetssjukhuset, Högskolan i Borås, regionala vårdcentraler.

Hög specificitet. Organisationen är en enskild enhet inom större organisation, ett litet företag eller en specifik lokal arbetsplats. Hit hör Sahlgrenskas akutmottagning Mölndal, Hvitfeldtska gymnasiets musiklinje, IKEA Bäckebol som enskild butik, Café Java på Linnégatan, samt små företag och enskilda firmor.

### 4.4 Narrativ specificitet (bedömningsdimension)

Narrativ specificitet annoteras inte som signal men ingår i identifierbarhetsbedömningen. Den fångar kontextuella ledtrådar som smalnar av populationen utöver de tre signaltyperna.

Låg narrativ specificitet. Texten saknar ledtrådar utöver yrke, plats och organisation. Inga tidsmarkörer, händelsereferenser eller demografiska detaljer.

Mellan narrativ specificitet. Texten innehåller en tidsmarkör eller demografisk detalj men ingen unik händelsereferens. Exempel: "den nyanställde som började i höstas", "den ende mannen på avdelningen", "den äldsta i teamet".

Hög narrativ specificitet. Texten innehåller en händelsereferens eller kombination av tidsmarkörer och demografi som markant smalnar av populationen. Exempel: "den nya HR-chefen som rekryterades efter omorganisationen i augusti", "kvinnan som vann årets innovationspris", "förstärkningen som kom från huvudkontoret efter coronapausen".

## 5. Identifierbarhetsbedömning

is_identifiable är en binär bedömning som styr om aggregat-fyndet context.kombination ska annoteras. Bedömningen följer en tre-stegs-procedur.

### 5.1 Steg 1: Identifiera signaler

Granskaren identifierar alla signaler i texten enligt sektion 3. Varje signal noteras med signaltyp, textspann och specificitetsnivå enligt sektion 4. Narrativ specificitet bedöms enligt 4.4.

### 5.2 Steg 2: Applicera kombinationsregel

Kombinationsregeln avgör is_identifiable baserat på signalernas och narrativets specificitetsnivåer. Reglerna prioriteras top-down och stannar vid första matchande regel.

Regel A -- Identifierbar via två högspecifika. Om minst två signaler har hög specificitet, oavsett signaltyp, är is_identifiable=true. Exempel: "VD på Hvitfeldtska gymnasiets musiklinje" (yrke hög + organisation hög).

Regel B -- Identifierbar via tre eller fler mellanspecifika. Om tre eller fler signaler har minst mellan specificitet och åtminstone en av dem är hög eller mellan, är is_identifiable=true. Exempel: "barnmorska på Borås Stads förlossningsavdelning i Borås" (yrke mellan + organisation mellan + plats mellan).

Regel C -- Identifierbar via narrativ förstärkning. Om kombinationen har minst två signaler med minst mellan specificitet OCH narrativ specificitet är hög, är is_identifiable=true. Exempel: "den nya barnmorskan som började i augusti på Borås förlossningsavdelning" (yrke mellan + organisation mellan + narrativ hög).

Regel D -- Inte identifierbar (default). Alla andra kombinationer ger is_identifiable=false. Detta inkluderar isolerade signaler, kombinationer av enbart lågspecifika signaler, och kombinationer som inte uppfyller någon av Reglerna A-C.

### 5.3 Steg 3: Annotera aggregat-fyndet

Om is_identifiable=true annoteras context.kombination med ett sammansatt textspann som täcker kombinationen från första till sista signalen i texten. Exempelvis i texten "Den nya VD:n på Hvitfeldtska gymnasiets musiklinje fick utmärkelsen i fjol" annoteras spannet "VD:n på Hvitfeldtska gymnasiets musiklinje". Sammansatta spans tillåts enbart för aggregat-fyndet, aldrig för individuella signaler.

Om is_identifiable=false annoteras inget aggregat-fynd. Endast de individuella signalerna förblir som annotationer.

## 6. Datasetets fyra strukturella celler

Datasetet ska täcka fyra celler enligt issue #73:s acceptanskriterier. Målvolym 25-35 entries totalt.

### 6.1 Cell 1: Tydligt identifierbara kombinationer (8-12 entries)

Texter där minst Regel A eller B från sektion 5.2 utlöses. Variation eftersträvas i vilka regler som triggas och vilka signaltyper som dominerar. Minst tre entries per regelutfall. Förväntad annotering: två eller fler individuella signaler plus aggregat-fynd context.kombination med is_identifiable=true.

### 6.2 Cell 2: Gränsfall (6-8 entries)

Texter där bedömningen kunde gått åt båda hållen. Det är dessa texter som kalibrerar medium_threshold och high_confidence_bypass enligt Beslut 20. Exempel: kombinationer av två mellanspecifika signaler utan narrativ förstärkning (faller under Regel D men ligger nära Regel B), eller kombinationer där en hög och en låg signal förekommer (faller under Regel D men kan upplevas som identifierande). Förväntad annotering varierar och dokumenteras tydligt i datasetet med description-fält som motiverar bedömningen.

### 6.3 Cell 3: Negativa kontroller utan signaler (5-7 entries)

Texter som inte innehåller yrke, plats eller organisation alls. Funktionen är att verifiera att CombinationLayer inte hallucinerar signaler. Förväntad annotering: tom expected_findings-lista.

### 6.4 Cell 4: Negativa kontroller med signaler men inte identifierande (6-8 entries)

Texter som innehåller en eller flera signaler men där kombinationen inte är identifierande enligt Regel D. Funktionen är att verifiera D5-korrigeringen i Beslut 19, alltså att isolerade context.*-fynd inte ensamma höjer sensitivity. Förväntad annotering: en eller flera individuella context.{signal}-signaler utan aggregat-fynd. Exempel: "Många jobbar som lärare i Stockholm" (yrke låg + plats låg, ingen context.kombination).

## 7. Annoteringsexempel

### 7.1 Exempel 1: Cell 1, Regel A

Text: "VD:n på Hvitfeldtska gymnasiets musiklinje fick utmärkelsen."

Bedömning: yrke "VD" (hög), organisation "Hvitfeldtska gymnasiets musiklinje" (hög). Regel A utlöses (två högspecifika).

Annotering:

```
context.yrke: "VD" (start, end)
context.organisation: "Hvitfeldtska gymnasiets musiklinje" (start, end)
context.kombination: "VD:n på Hvitfeldtska gymnasiets musiklinje", is_identifiable=true
```

### 7.2 Exempel 2: Cell 4, Regel D

Text: "Många jobbar som lärare i Stockholm."

Bedömning: yrke "lärare" (låg), plats "Stockholm" (låg). Ingen regel utlöses, default Regel D.

Annotering:

```
context.yrke: "lärare" (start, end)
context.plats: "Stockholm" (start, end)
Inget aggregat-fynd.
```

### 7.3 Exempel 3: Cell 2, gränsfall

Text: "Barnmorskan på Sahlgrenska i Göteborg arbetade nattskift."

Bedömning: yrke "Barnmorskan" (mellan, formell yrkestitel), organisation "Sahlgrenska" (mellan), plats "Göteborg" (låg). Två mellan + en låg, ingen regel utlöses tydligt. Regel B kräver minst tre signaler med mellan-eller-bättre, vilket uppfylls strikt sett. Granskaren bedömer kombinationen som gränsfall mot Regel B och annoterar enligt egen bedömning, dokumenterar avvägningen i description.

### 7.4 Exempel 4: Cell 3, ingen signal

Text: "Mötet flyttades från tisdag till torsdag eftersom flera var sjuka."

Bedömning: inga signaler.

Annotering: tom expected_findings.

## 8. Praktiska annoteringsråd

Span-precision är kritisk. text.find() används vid validering, så alla text_span måste vara exakta substrings av originaltexten. Skiljetecken ingår inte i spannet. "VD:n" annoteras som "VD" om kolon-konstruktionen inte är del av yrkestiteln.

Vid osäkerhet om signaltyp, prioritera enligt följande ordning: organisation före plats, plats före yrke. Detta är pragmatisk konvention för att hantera konstruktioner som "Borås Stad" där "Borås" är både plats och del av organisationsnamn. Hela "Borås Stad" annoteras då som organisation och "Borås" som ensam textförekomst annoteras inte separat.

Vid sammansatta organisationsnamn, annotera hela namnet som ett spann. "Volvo Cars Skövde" är ett spann (organisation, mellan), inte två (organisation + plats).

Konsensus i FAS B uppnås via guiden, inte via subjektiv kompromiss. Om granskarna är oense, gå till relevant sektion i guiden och lös avvikelsen mot kriterierna. Om guiden är otydlig på punkten, dokumentera otydligheten som öppen fråga och justera guiden i en uppföljande revision.

## 9. Kända begränsningar och arkitektoniska val

Specificitetskategoriseringen i sektion 4 baseras delvis på kvantitativa storlekströsklar (invånare, anställda) som är pragmatiska snarare än empiriskt validerade. Trösklarna kan justeras i iteration 3 baserat på utvärderingsutfall.

Narrativ specificitet är guidens mest subjektiva dimension. Inter-rater agreement förväntas vara lägre på 4.4 än på 4.1-4.3. Detta är en känd metodologisk begränsning som dokumenteras i datasetets data statement.

Kombinationsreglerna i sektion 5.2 är deduktivt formulerade utan empirisk validering. Om iteration 2:s utvärdering visar att reglerna är för strikta eller för slappa, justeras de i iteration 3. Om narrativ specificitet visar sig oanvändbar empiriskt kan dimensionen strykas helt utan att schemat eller koden behöver röras.

Guiden täcker inte fall där pusselbitseffekten uppstår genom kombination med externt kända fakta (exempelvis "min granne som vann lotteriet förra månaden" där grannskapet är extern kunskap). Sådana fall ligger utanför CombinationLayer:s scope eftersom de inte kan detekteras enbart från textinnehållet.

Arkitektoniskt val: parallell pipeline med lagerovetskap. CombinationLayer detekterar inte artikel 4-fynd (personnummer, mejl, telefonnummer, IBAN, kortnummer, namn, adress) och inte artikel 9-fynd (hälsa, etniskt ursprung, politisk åsikt, religiös övertygelse, fackmedlemskap, biometrisk eller genetisk data, sexuell läggning). Dessa hanteras av Lager 1, Lager 2 respektive Lager 3 enligt arkitektur.md sektion 6. Korsläggsvalidering mellan lager sker i aggregatorn via Beslut 19:s Mekanism 3, inte genom att lager dubbeldetekterar varandras kategorier. Detta val bevarar lagerovetskaps-principen (sektion 2.2 i arkitektur.md) och utbytbarheten via Layer-protokollet (designprincip 2 i formaliseringsfasen).

Schemaval: tre signaltyper i iteration 2. Schemat allowed_signals = {yrke, plats, organisation} är låst för iteration 2 enligt #72:s implementation. Ålder identifierades under guidens utformning som potentiellt stark identifierare och möjlig fjärde signaltyp. Den utökningen sköts till iteration 3 eftersom (a) den kräver att #72 öppnas och Category-enumen utökas, vilket bryter koordinationsregeln för gdpr_classifier/core/, och (b) iteration 2 saknar tidsbudget för schemautökning innan nästa intressent-utvärdering. Beslutet är konsistent med ADR:s iterativa princip att schema formaliseras baserat på empiriska utfall, inte på initial intuition.

Exklusion av artikel 9-kategorier från CombinationLayer:s schema. Artikel 9-data triggar sensitivity oberoende av kontextkombination via Lager 3. Att även annotera dem som CombinationLayer-signaler skulle skapa dubbeldetektion på samma textspann och konceptuell förvirring kring sensitivity-orsak. Om iteration 3:s utvärdering visar att kombinationen artikel 9 + kontext bör amplifiera sensitivity ytterligare, är den korrekta åtgärden aggregatorlogik (exempelvis en regel "om artikel 9-fynd och context.kombination samexisterar, höj till HIGH"), inte schemautökning i Lager 4.

## 10. Versionering och spårbarhet

Guiden versioneras med datum i metadatablocket högst upp. Vid ändring av kriterier i sektion 4 eller 5 inkrementeras versionen och ändringen dokumenteras i Loggboken (Google Docs, fliken "Loggbok - iteration 2"). FAS A:s genereringsskript loggar guidens git-hash i .candidates_metadata.json så att varje genererad kandidat kan spåras till den version av guiden som var aktuell vid genereringen.
