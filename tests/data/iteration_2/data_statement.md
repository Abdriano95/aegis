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
