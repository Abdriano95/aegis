# Annoteringsguide: artikel 9-data i svensk fritext

**Status:** Reviderad efter granskning av Johanna Gull och OT-domsverifiering 2026-05-01
**Senast reviderad:** 2026-05-01
**Avsedd användning:** Konsensus-granskning av testdataset för Article9Layer (Issue #71, FAS B). Refereras från `tests/data/iteration_2/data_statement.md` och från AEGIS-rapportens metoddel.

---

## 1. Syfte

Guiden definierar vad som ska klassificeras som artikel 9-data när ni granskar testtexter. Den ger er en gemensam referensram så att granskningen blir oberoende och konsensusbar utan att vara godtycklig. När ni är oense löses oenigheten genom att gå tillbaka till lagtexten, IMY:s formuleringar och den rättspraxis som refereras i denna guide, inte genom kompromiss.

Guiden är inte uttömmande juridisk vägledning. Den är ett operativt verktyg för att avgöra om en specifik text-passage i ett testfall ska annoteras som artikel 9-data eller inte.

## 2. Avgränsning

Guiden täcker enbart de åtta kategorierna i artikel 9.1. Den behandlar inte:

- Artikel 4-data (namn, personnummer, kontaktuppgifter). Dessa hanteras av Lager 1 och Lager 2 i `gdpr-classifier`.
- Övriga "integritetskänsliga" personuppgifter som IMY listar (löneuppgifter, lagöverträdelser, värderande uppgifter, skyddad identitet). Dessa ligger utanför Article9Layer:s scope i iteration 2.
- Pusselbitseffekten / indirekt identifierbarhet. Den hanteras av CombinationLayer (Lager 4), inte Article9Layer. *Notera:* Indirekt *avslöjande* av känslig kategori (se avsnitt 3) hanteras däremot av Article9Layer; det är en annan sak än indirekt identifierbarhet.

Om en text innehåller artikel 4-data utöver artikel 9-data, annotera bara artikel 9-delen i datasetet för #71.

## 3. Lagtextens grundregel och OT-domens tolkning

Artikel 9.1 GDPR förbjuder behandling av personuppgifter som *avslöjar* följande om en *fysisk person*:

> ras eller etniskt ursprung, politiska åsikter, religiös eller filosofisk övertygelse eller medlemskap i fackförening och behandling av genetiska uppgifter, biometriska uppgifter för att entydigt identifiera en fysisk person, uppgifter om hälsa eller uppgifter om en fysisk persons sexualliv eller sexuella läggning

EU-domstolens dom i mål **C-184/20 (OT-domen) av den 1 augusti 2022** (ECLI:EU:C:2022:601) preciserar tolkningen avgörande. Domstolen slog fast följande tolkningsprincip i punkt 123 och i domslutets andra punkt:

> Personuppgifter som "indirekt efter en intellektuell slutledning eller avstämning" kan avslöja känslig information om en fysisk person omfattas av artikel 9.1.

Konkret exempel i domen: namnuppgifter om make/maka, sambo eller partner kan indirekt avslöja sexuell läggning och omfattas därför av artikel 9.

**Konsekvenser av OT-domen för annoteringen:**

För det första: artikel 9 omfattar inte bara *direkta* angivelser ("Anna är muslim") utan även *indirekta indikatorer* som via slutledning avslöjar känslig kategori ("Anna är medlem i Stockholms moské-församling").

För det andra: tolkningen är symmetrisk över alla åtta kategorier. Domstolen avvisar uttryckligen tanken att vissa kategorier (hälsa, sexualliv, sexuell läggning) skulle ha en striktare "om"/"som rör"-formulering än andra. Indirekt avslöjande räcker för alla.

För det tredje: bedömningen ska göras utifrån vad uppgiften faktiskt kan avslöja, inte utifrån avsändarens avsikt eller mottagarens kunskap. Om en kombination av uppgifter via rimlig slutledning avslöjar känslig kategori, är det artikel 9-data.

**Tre frågor att alltid ställa till en kandidat-passage:**

1. Handlar uppgiften om en specifik fysisk person, eller är det generell information?
2. Avslöjar uppgiften — direkt eller via rimlig slutledning — något om personens egenskap eller tillstånd?
3. Är personen identifierad eller identifierbar i sammanhanget?

Bara om svaren är "specifik person", "ja, avslöjar (direkt eller indirekt)", "identifierbar" är det artikel 9-data.

**Viktigt om "fysisk person":** Generella förhållanden, organisationsfakta, projekt, områden eller produkter är inte artikel 9-data, även om kategoriorden förekommer i texten. "Företaget arbetar med hälsofrågor" är inte hälsodata. "Anders har diabetes" är hälsodata om Anders.

---

## 4. Kategorierna

### 4.1 Hälsodata (`article9.halsodata`)

**IMY:s definition:** Hälsouppgifter omfattar alla aspekter av en persons hälsa, till exempel uppgifter som kommer från tester eller undersökningar, uppgifter om sjukdom, sjukdomsrisk, sjukdomshistoria eller funktionshinder oavsett vilken källa uppgifterna kommer ifrån.

**Vad som ingår:**

- Specifika diagnoser om en namngiven person ("Anders har diabetes", "Maria är diagnosticerad med depression")
- Symptom kopplade till en person ("Eva har ont i ryggen sedan förra veckan", "Joakim är sjukskriven på grund av halsinfektion")
- Sjukdomshistoria ("Per har tidigare haft cancer")
- Sjukdomsrisk och predisposition ("Sara har förhöjd risk för hjärt-kärlsjukdom")
- Funktionshinder ("Anders rör sig med rullstol", "Karin är döv")
- Resultat från medicinska tester eller undersökningar
- Medicinering som indikerar sjukdom ("Lars tar antidepressiva")
- Hälsovårdens kontakt med personen som *avslöjar* eller indirekt antyder hälsofråga ("Anna har träffat onkologen", "Maria går till företagshälsan på torsdag")

**Vad som *inte* ingår (vanliga felannoteringar):**

- Yrke inom vården ("Anna arbetar som sjuksköterska") — detta är yrkesinformation, inte hälsodata om Anna
- Utbildning inom vårdämne ("Anna har gått en kurs i hälsovård") — utbildning är inte hälsodata om personen som gått den
- Generell hälsovårdsdiskussion utan koppling till specifik person ("Vi måste tänka på medarbetarnas hälsa")
- Hälso-relaterade projekt eller produkter ("Vi utvecklar en hälsoapp")
- Allmänna välmående-omdömen ("Hoppas du mår bra")
- Medicinering som är trivial och inte indikerar sjukdom ("har tagit värktablett")

**Gränsdragningsexempel:**

| Text | Annotering | Motivering |
|------|------------|------------|
| "Anders är sjukskriven sedan måndag" | Hälsodata | Sjukfrånvaro avslöjar hälsotillstånd |
| "Anders är på semester" | Inte hälsodata | Frånvaro av annan orsak |
| "Maria går till företagshälsan på torsdag" | Hälsodata | Indirekt avslöjande enligt OT-domen — företagshälsovårdsbesök antyder hälsofråga |
| "Företagshälsan har bjudit in alla till hälsokontroll" | Inte hälsodata | Generell aktivitet, ingen specifik person |
| "Karin har slutat röka efter sin hjärtinfarkt" | Hälsodata | Sjukdomshistoria |
| "Karin har slutat röka" | Inte hälsodata | Livsstilsförändring utan hälsokoppling |

### 4.2 Etniskt ursprung (`article9.etniskt_ursprung`)

**IMY:s definition:** Uppgifter som avslöjar någons etniska ursprung eller ras är känsliga personuppgifter. I svenska lagar används inte ordet ras, men dataskyddsförordningen använder det utan att godta teorier om skilda människoraser.

**Viktig avgränsning från IMY:** Nationalitet och medborgarskap är *inte* etniskt ursprung. Att en person är "svensk medborgare", "fransk medborgare" etcetera är juridisk status, inte etnisk tillhörighet. Etnicitet kräver kulturell, språklig eller härkomstbaserad markör.

**Vad som ingår:**

- Direkt angivelse av etnisk grupp ("Ahmed tillhör tigrinya-talande gruppen", "Familjen är romer")
- Födelseland när det kombineras med kontext som gör det till etnisk markör ("Sara är född i Eritrea och flyttade till Sverige som vuxen")
- Modersmål när det fungerar som etnisk markör ("Anna talar finska som modersmål och tillhör den sverigefinska minoriteten")
- Kulturell tillhörighet på etnisk grund ("Han firar samiska traditioner med sin familj")
- Referenser till hudfärg eller fysiska drag som etniska markörer
- Indirekta indikatorer enligt OT-domen ("Familjen Bergström har bott i samebyn i tre generationer" avslöjar samisk tillhörighet)

**Vad som *inte* ingår:**

- Geografisk hemvist eller kommun ("Anna från Stockholm", "Maria på Enköpings kontor") — geografi är inte etnicitet
- Företagets eller projektets geografiska anknytning ("samarbete med svenska företag") — företag har ingen etnicitet
- Nationalitet och medborgarskap utan kulturell kontext ("Per är svensk medborgare")
- Språkkunskap som arbetsfärdighet ("Anna talar tre språk")
- Resor eller internationell erfarenhet ("Per har arbetat två år i Tyskland")

**Gränsdragningsexempel:**

| Text | Annotering | Motivering |
|------|------------|------------|
| "Ahmed är född i Eritrea och tillhör tigrinya-folket" | Etniskt ursprung | Direkt etnicitetsangivelse |
| "Per är svensk medborgare" | Inte artikel 9 | Nationalitet, inte etnicitet (IMY) |
| "Anna kommer från Stockholm" | Inte artikel 9 | Geografisk hemvist |
| "Vi har kunder från Tyskland" | Inte artikel 9 | Generell affärsinformation |
| "Familjen Bergström har bott i samebyn i tre generationer" | Etniskt ursprung | Indirekt avslöjande av samisk tillhörighet (OT-domen) |
| "Han föredrar svenska kollegor" | Diskussionsfall | Kan vara etnisk preferens eller språkpreferens |

### 4.3 Politisk åsikt (`article9.politisk_asikt`)

**IMY:s definition:** Det är en känslig personuppgift att någon är med i ett visst politiskt parti.

Lagtextens "politiska åsikter" är bredare än partimedlemskap men kräver att uppgiften *avslöjar* personens politiska ställningstagande, direkt eller indirekt enligt OT-domen.

**Vad som ingår:**

- Partimedlemskap ("Lars är medlem i Socialdemokraterna")
- Partikandidatur ("Anna kandiderar för Centerpartiet i kommunvalet")
- Direkt uttryckta politiska ställningstaganden om en specifik person ("Erik är emot kärnkraft", "Maria röstar alltid på Vänsterpartiet")
- Politisk aktivism om en specifik person ("Han demonstrerade mot regeringens budget")
- Förtroendeuppdrag av politisk natur ("Hon sitter i kommunfullmäktige för Liberalerna")

**Vad som *inte* ingår:**

- Projekt eller produkter med politisk anknytning ("Vi arbetar med miljöpolitik" är inte politisk åsikt om någon)
- Yrkesmässig kontakt med politiska processer ("Anna är lobbyist" — yrkesinformation)
- Generella samhällsdiskussioner utan personlig ståndpunkt ("Vi måste ta hänsyn till politiska aspekter i strategin")
- Att personen arbetar med ett politiskt anknutet ämne ("Han forskar om partipolitik")
- Engagemang i ideella eller branschorganisationer som inte är partipolitiska
- Projektnamn eller produktnamn även om de låter politiska

**Gränsdragningsexempel:**

| Text | Annotering | Motivering |
|------|------------|------------|
| "Anton är aktiv i Miljöpartiet" | Politisk åsikt | Partimedlemskap |
| "Vi måste vara medvetna om politiska aspekter" | Inte politisk åsikt | Generell affärsdiskussion |
| "Projektet 'Hemliga Helgon'" | Inte politisk åsikt | Projektnamn, ingen åsikt |
| "Hon arbetar med miljöpolitik som tjänsteperson" | Inte politisk åsikt | Yrkesroll, inte ställningstagande |
| "Han röstade nej i folkomröstningen" | Politisk åsikt | Konkret ställningstagande |

### 4.4 Religiös eller filosofisk övertygelse (`article9.religios_overtygelse`)

**IMY:s definition:** Det är en känslig personuppgift att någon tillhör en viss religion eller inte tillhör någon religion alls.

**IMY-tillägg från video:** Det räcker inte med direkt angivelse ("Anna är muslim"). Även medlemskap i specifik församling, samfund eller religiös organisation räknas som indirekt avslöjande och omfattas av artikel 9.

Lagtexten omfattar både religiös och filosofisk övertygelse. Filosofisk övertygelse tolkas som världsåskådning av samma karaktär som religion (humanism, ateism, vissa livsåskådningar) snarare än vardagsfilosofi.

**Vad som ingår:**

- Religionstillhörighet om en specifik person ("Fatima är muslim", "Per är buddhist")
- Avsaknad av religion ("Anna är ateist", "Lars är inte troende")
- Församlingsmedlemskap eller medlemskap i religiös organisation ("Hon är medlem i Pingstkyrkan Stockholm", "Han tillhör Bromma församling")
- Religiös praktik som avslöjar tillhörighet ("Hon ber fem gånger om dagen", "Han firar Eid med familjen", "Familjen går i kyrkan varje söndag")
- Religiösa kläder eller attribut kopplade till specifik person ("Fatima bär hijab", "Han bär kippa")
- Religiös aktivitet inom samfund ("Hon är studiecirkel-ledare i Studieförbundet Bilda", "Han är diakon")
- Filosofisk övertygelse av världsåskådnings-karaktär ("Hon är övertygad humanist")

**Vad som *inte* ingår:**

- Religiösa platser, symboler eller traditioner i generell mening ("Vi besökte kyrkan", "Företaget har en julgran")
- Kulturell deltagande utan tillhörighetsangivelse ("Hon var med på julbordet")
- Religiösa projekt eller produkter ("Vi utvecklar en app för bibelstudier")
- Religiösa lokaler som geografisk referens ("Mötet är i moskén på Skånegatan")
- Religion som diskussionsämne utan personlig koppling
- Kyrkligt giftermål utan ytterligare kontext (se särskild gränsdragning nedan)

**Särskild gränsdragning: bröllop, begravningar, helger**

Att någon "var på Eriks bröllop i kyrkan" är inte religiös övertygelse om personen som var med. Att Erik själv gifte sig i kyrkan är i Sverige *vanligen kulturellt* snarare än ett uttryck för religiös övertygelse — den som inte är troende kan ändå välja kyrklig vigsel av tradition. Default-bedömningen är därför **inte religiös övertygelse**. Endast om kontexten gör tydligt att vigseln är ett trosval ("Erik gifte sig i kyrkan eftersom hans tro är central för honom") blir det artikel 9.

Samma princip gäller dop, konfirmation och kyrkliga begravningar: kulturellt deltagande omfattas inte; troskoppling i texten gör det.

**Gränsdragningsexempel:**

| Text | Annotering | Motivering |
|------|------------|------------|
| "Fatima bär hijab till skolan varje dag" | Religiös övertygelse | Attribut kopplat till tillhörighet |
| "Vi har en julgran i lobbyn" | Inte religiös övertygelse | Generell decor, ingen specifik person |
| "Anders går i kyrkan varje söndag" | Religiös övertygelse | Religiös praktik, specifik person |
| "Anders ska gifta sig i kyrkan" | Inte religiös övertygelse (default) | I Sverige kulturellt vanligt även utan trosval |
| "Hon är medlem i Sankt Eriks katolska församling" | Religiös övertygelse | Församlingsmedlemskap (IMY) |
| "Mötet hålls i Frälsningsarméns lokal" | Inte religiös övertygelse | Lokal som mötesplats |

### 4.5 Fackmedlemskap (`article9.fackmedlemskap`)

**IMY:s definition:** Att någon är med i en viss fackförening är en känslig personuppgift.

Detta är den mest avgränsade kategorin: kärnan är medlemskap i fackförening. Lagtexten säger "medlemskap i fackförening", vilket är specifikt.

**Vad som ingår:**

- Direkt fackmedlemskap om en namngiven person ("Anders är medlem i Unionen", "Maria tillhör Kommunal")
- Förtroendeuppdrag inom fackförening ("Hon är skyddsombud för IF Metall", "Han är fackklubbsordförande")
- Indirekt avslöjande genom fackrelaterad aktivitet enligt OT-domen ("Lars deltog i strejken som Byggnads organiserade")

**Vad som *inte* ingår:**

- Generella diskussioner om fackföreningar ("Föreningens fackmedlemmar bör informeras" — vilka? alla? detta är generellt)
- Att fackföreningar finns på arbetsplatsen
- Att en arbetsgivare har kollektivavtal
- Yrkesförbund eller branschorganisationer som inte är fackföreningar (Läkarförbundet är gränsfall — fungerar både som fack och som professionsförbund)
- Generell information om strejker eller fackliga aktiviteter

**Gränsdragningsexempel:**

| Text | Annotering | Motivering |
|------|------------|------------|
| "Joakim är medlem i fackföreningen" | Fackmedlemskap | Konkret medlemskap, specifik person |
| "Föreningens fackmedlemmar bör informeras" | Inte fackmedlemskap | Generellt, ingen specifik person identifierad |
| "Vi har kollektivavtal med Unionen" | Inte fackmedlemskap | Avtal mellan organisationer |
| "Anna är vald till skyddsombud" | Fackmedlemskap | Förtroendeuppdrag avslöjar facklig aktivitet |

### 4.6 Genetiska uppgifter (`article9.genetisk_data`)

**IMY:s definition:** Genetiska uppgifter rör en persons "nedärvda eller förvärvade genetiska kännetecken". Genetiska uppgifter kan till exempel framgå av en dna-analys.

**Vad som ingår:**

- DNA-analyser och deras resultat om en specifik person
- Genetisk testning ("Eriks gentest visade ärftlig predisposition")
- Genetiska sjukdomsrisker baserat på arvsmassa
- Information från genetisk släktforskning som avslöjar personens egen genetiska profil
- Genetisk släktskapsinformation som avslöjar genetiska kännetecken

**Vad som *inte* ingår:**

- Ärftlighet i sociologisk eller kulturell mening ("Det ligger i släkten att vi blir lärare")
- Generell forskning om genetik utan koppling till specifik person
- Att en person arbetar med genetisk forskning (yrkesinformation)
- Familjeträd utan genetisk information ("Hennes farfar var målare")

**Gränsdragningsexempel:**

| Text | Annotering | Motivering |
|------|------------|------------|
| "Erik har en genetisk predisposition för bröstcancer" | Genetisk data | Genetisk uppgift om specifik person |
| "Vi forskar på genetisk variation" | Inte genetisk data | Forskningsämne, generellt |
| "Hennes DNA-test visade europeiskt ursprung" | Genetisk data + etniskt ursprung | Båda kategorierna |
| "Sjukdomen är ärftlig i hennes familj" | Genetisk data | Avslöjar genetisk risk indirekt (OT-domen) |

**Notera:** Genetisk data och hälsodata överlappar ofta. När en text rör både (t.ex. genetisk sjukdomsrisk) annotera båda kategorierna med separata findings.

### 4.7 Biometriska uppgifter (`article9.biometrisk_data`)

**IMY:s definition:** Biometriska uppgifter rör en persons "fysiska, fysiologiska eller beteendemässiga egenskaper" och gör det möjligt att identifiera människor, till exempel genom fingeravtrycksavläsning eller ögonskanning. Foton på människor är *bara* biometriska uppgifter när de behandlas med teknik som möjliggör identifiering eller autentisering av en person, till exempel teknik för ansiktsigenkänning.

Detta är den striktaste definitionen. Lagtexten säger "biometriska uppgifter *för att entydigt identifiera en fysisk person*". Tekniken eller dess output måste användas för identifiering.

**Vad som ingår:**

- Fingeravtryck använda för identifiering om en specifik person ("Anders fingeravtryck registrerades i systemet")
- Ansiktsigenkänningsdata om en specifik person ("Annas ansikte är registrerat i face-ID-systemet")
- Iris- eller näthinneskanningar för identifiering
- Röstavtryck för identifiering
- Beteendebiometri om specifik person (gångmönster, tangentbordsanvändning) när det används för identifiering

**Vad som *inte* ingår:**

- Vanliga foton av personer som *inte* behandlas med igenkänningsteknik
- Generella beskrivningar av biometriska system ("Vi använder fingeravtrycksläsare på kontoret" — detta är systembeskrivning, inte biometrisk data om en person)
- Biometriska tekniker som diskussionsämne ("Vi utvärderar biometriska system")
- Kameror eller övervakningsutrustning som ej kopplas till en specifik person
- Personliga egenskaper som inte används för identifiering ("Han är 1.85 lång")

**Gränsdragningsexempel:**

| Text | Annotering | Motivering |
|------|------------|------------|
| "Anders fingeravtryck registrerades i passersystemet" | Biometrisk data | Biometri använd för identifiering, specifik person |
| "Vi använder ansiktsigenkänning för inloggning" | Inte biometrisk data | Systembeskrivning, ingen specifik person |
| "Annas face-ID fungerar bra" | Biometrisk data | Avslöjar att Annas biometri är registrerad |
| "Vi utvärderar biometriska lösningar" | Inte biometrisk data | Diskussionsämne |
| "Bilder från övervakningskameran sparas i 30 dagar" | Inte biometrisk data | Ingen ansiktsigenkänningsteknik nämnd |

### 4.8 Sexuell läggning eller sexualliv (`article9.sexuell_laggning`)

**IMY:s definition:** Uppgifter om personers sexualliv eller vilken sexuell läggning de har är känsliga personuppgifter.

**OT-domens centrala exempel:** Domen behandlar specifikt namnuppgifter om make/maka, sambo eller partner som *indirekt* avslöjande av sexuell läggning. Detta är den paradigmatiska tillämpningen av indirekt avslöjande och har direkt relevans för annoteringen.

Lagtexten omfattar två närliggande men distinkta begrepp: sexualliv (vad personen gör) och sexuell läggning (vem personen är attraherad av).

**Vad som ingår:**

- Direkt angivelse av sexuell läggning ("Maria är homosexuell", "Per är bisexuell")
- Indirekt avslöjande genom partner som avslöjar samkönad relation ("Anna gifte sig med sin fru", "Hans man hämtade honom efter mötet")
- Indirekt avslöjande genom bostadssituation som indikerar samkönad relation ("Anders bor med sin pojkvän Erik")
- HBTQ-engagemang och aktivism om specifik person ("Hon är aktiv i RFSL", "Han är aktiv i Pride-paraden")
- Sexualliv-uppgifter om specifik person
- Reproduktionsfrågor om specifik person när de avslöjar sexualitet eller sexualliv

**Vad som *inte* ingår:**

- Genus eller kön i sig (det är inte sexuell läggning)
- Civilstånd utan implicit information om läggning ("Per är gift" säger inget om läggning eftersom heteronormen är default-antagande)
- Hetero-implicerande partnerangivelser ("Annas make ringde", "Eriks fru hämtade barnen") — dessa avslöjar inte avvikande läggning enligt OT-domens logik, default-antagandet är inte avslöjande
- Yrkesmässig kontakt med HBTQ-frågor om det är klart yrkesroll ("Anna är jurist på en organisation som arbetar med HBTQ-rättigheter" — yrkesinformation om aktivisten själv är inte HBTQ-aktiv)
- Generella diskussioner om sexualpolitik
- Vagheter som inte tydligt avslöjar något

**Asymmetri-anmärkning:** OT-domen och IMY:s tolkning innebär en asymmetri som är värd att notera: hetero-implikationer ("hans fru") avslöjar inte sexuell läggning eftersom heteronormen är samhällets default-antagande, medan icke-hetero-implikationer ("hans man") *gör* det eftersom de avviker från default. Detta speglar inte någon värdering utan följer av "avslöjande"-testet — uppgiften måste ge information som inte redan är default-antagandet.

**Gränsdragningsexempel:**

| Text | Annotering | Motivering |
|------|------------|------------|
| "Hans man hämtade honom efter mötet" | Sexuell läggning | Indirekt avslöjande via partner (OT-domen) |
| "Annas make ringde" | Inte sexuell läggning | Hetero-implikation är default-antagande |
| "Anders bor med sin pojkvän" | Sexuell läggning | Bostadssituation avslöjar samkönad relation (IMY) |
| "Han är aktiv i Pride-paraden" | Sexuell läggning | Aktivism är indirekt avslöjande enligt OT-domen |
| "Hon kandiderar för RFSL:s styrelse" | Sexuell läggning | Stark indikation via aktivt engagemang |
| "Anna arbetar som jurist på RFSL" | Diskussionsfall | Yrke kan men måste inte avslöja personlig läggning — bedöm i kontext |

**Försiktighetsregel:** Sexuell läggning är den kategori där felaktig annotering riskerar att kränka individens integritet mest. Var konservativ vid genuint vaga formuleringar ("personliga aktiviteter", "privatliv generellt"). Vid genuin tvekan, annotera *inte* som sexuell läggning. Bättre falskt negativ än falskt positiv för denna kategori i testdataset-konstruktion.

Samtidigt: var inte överdrivet försiktig med tydliga indirekta indikatorer. OT-domen och IMY ger explicit stöd för att partneridentitet, bostadssituation och HBTQ-aktivism räknas. Att inte annotera dessa skulle gå emot rådande tolkning.

---

## 5. Övergripande gränsdragningsprinciper

Sex principer som löser de flesta gränsfall:

**Princip 1 — Specifik person:** Artikel 9-data gäller en identifierad eller identifierbar fysisk person. Generella kategoridiskussioner är inte artikel 9-data, oavsett ordval. Test: kan jag peka på *vem* uppgiften handlar om?

**Princip 2 — Avslöjande, direkt eller indirekt:** Uppgiften måste *avslöja* personens egenskap eller tillstånd, antingen direkt eller via rimlig slutledning enligt OT-domen. Test: efter att jag läst passagen, vet jag — eller kan rimligen sluta mig till — något konkret om personens hälsa/etnicitet/läggning som jag inte visste innan?

**Princip 3 — Yrke är inte tillstånd:** Att arbeta med ett ämne är inte att vara av det. En sjuksköterska har inte hälsodata om sig genom sitt yrke. En präst har inte religiös övertygelse-status genom sitt yrke (fast en präst har ofta det av andra skäl — bedöm i kontext). En facklig ombudsman som *själv* är fackmedlem är gränsfall.

**Princip 4 — Geografi och nationalitet är inte etnicitet:** Hemvist, ursprungsland, kommun, region, medborgarskap och nationalitet är inte automatiskt etniskt ursprung. Etnicitet kräver kulturell, språklig eller härkomstbaserad markör.

**Princip 5 — System är inte data om person:** Att en organisation använder biometriska system, hälsosystem eller liknande är inte artikel 9-data om en specifik person. Bara när systemet kopplas till en namngiven individ blir uppgifterna om individen artikel 9.

**Princip 6 — Default-antaganden avslöjar inte:** Uppgifter som överensstämmer med samhällets default-antagande (heteronorm, majoritetsetnicitet, sekularitet i Sverige) avslöjar inget i lagens mening. Bara avvikelser från default avslöjar. Detta gäller särskilt sexuell läggning.

---

## 6. Tillämpning vid granskning

När ni granskar en kandidat-text, tillämpa följande sekvens:

För det första: läs hela texten. Identifiera vilka personer som nämns och vilka uppgifter som framkommer om dem.

För det andra: för varje passage som kan vara artikel 9-data, ställ de tre frågorna från avsnitt 3 (specifik person? avslöjar direkt eller indirekt? identifierbar?).

För det tredje: kontrollera mot kategorins "vad som ingår" och "vad som *inte* ingår" i avsnitt 4.

För det fjärde: vid tvekan, tillämpa principerna i avsnitt 5.

För det femte: om det fortfarande är oklart, markera som "diskussionsfall" i ert kalkylblad och ta upp det i konsensus-mötet.

För det sjätte: om en text annoterats fel av kandidatgenererings-LLM:n, är det vanligaste felet att kategoriord nämnts utan att verklig artikel 9-data finns. Stryk fyndet eller hela texten beroende på allvarlighet.

---

## 7. Begränsningar i denna guide

Guiden är inte en juridisk auktoritet. Den är en operativ tolkning baserad på lagtexten i artikel 9.1 GDPR, IMY:s introduktionsmaterial om dataskyddsförordningen, och EU-domstolens dom i mål C-184/20 (OT-domen). För faktiska beslut om artikel 9-behandling i produktion krävs juridisk granskning.

Två områden där guiden är medvetet begränsad:

För det första: rättspraxis utöver OT-domen. EU-domstolen och nationella domstolar har bidragit med ytterligare tolkningar. Specifikt har OT-domen följts upp av senare domar som kan ytterligare precisera "indirekt avslöjande"-tolkningen — dessa har inte beaktats systematiskt i denna guide.

För det andra: branschspecifika tolkningar. IMY har vägledning för specifika sektorer (vård, skola, arbetsliv) som kan precisera vad som räknas som artikel 9-data i deras kontext. Denna guide använder den allmänna tolkningen och kan vara striktare eller mer generös än sektor-specifik vägledning kräver.

---

## 8. Källor

**Primärkälla:**

- Europaparlamentets och rådets förordning (EU) 2016/679 (GDPR), artikel 9.1.

**Auktoritativ rättspraxis:**

- EU-domstolens dom av den 1 augusti 2022 i mål C-184/20, *OT mot Vyriausioji tarnybinės etikos komisija* (ECLI:EU:C:2022:601). Stora avdelningen. Punkt 123 och domslutets andra punkt fastställer att artikel 9.1 omfattar uppgifter som indirekt via slutledning avslöjar känslig kategori.

**Sekundärkälla:**

- Integritetsskyddsmyndigheten (IMY), "Introduktion till GDPR" / "Känsliga personuppgifter" på imy.se.
- IMY:s informationsfilm om känsliga personuppgifter (granskad av Johanna Gull 2026-05-01) som klargör att (a) nationalitet inte är etniskt ursprung, (b) församlingsmedlemskap räknas som religiös övertygelse, (c) bostadssituation kan indirekt avslöja sexuell läggning.

---

## 9. Revisionshistorik

| Datum | Ändring | Av |
|-------|---------|-----|
| 2026-05-01 | Initial version | Arkitekt-instans |
| 2026-05-01 | Revidering efter OT-domsverifiering och IMY-tillägg från JG: nationalitet exkluderad från etniskt ursprung, församlingsmedlemskap inkluderat under religiös övertygelse, kyrklig vigsel default-klassificerad som icke-religiös, Pride-aktivism inkluderad under sexuell läggning, princip 6 om default-antaganden tillagd, OT-dom-referenser preciserade | Arkitekt-instans efter granskning av JG |