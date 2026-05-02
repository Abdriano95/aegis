# FAS B-granskning av CombinationLayer-testdataset (\#73)

**Granskare:** \[Abdulla / Johanna\] **Datum:** 2026-05-02 **Kandidatfil:** `tests/data/iteration_2/combination_dataset_candidates.json` **Auktoritativ referens:** `docs/combination_annotation_guidelines.md` **Antal kandidater:** 29

---

## Granskningsinstruktion

Granska varje kandidat oberoende av medgranskaren. Ta inte hänsyn till vad du tror den andra kommer säga. Använd guiden som auktoritativ referens vid tveksamhet.

För varje entry, ta ställning till tre frågor:

1. **Är textens kvalitet acceptabel?** Idiomatisk svenska, fiktiv situation, inga direkta personuppgifter, inga artikel 9-data.  
2. **Är annotationerna korrekta enligt guiden?** Rätt signaltyper, rätt specificitetsnivåer (jämför mot 4.1, 4.2, 4.3, 4.4), korrekt is\_identifiable enligt 5.2:s regler.  
3. **Hör entryn till rätt cell enligt 6.1-6.4?** Cell 1 ska trigga A/B/C tydligt. Cell 2 ska vara genuint gränsfall. Cell 3 ska sakna signaler. Cell 4 ska ha signaler men inte vara identifierande.

Tre möjliga beslut per entry:

- **Behåll**: entryn är korrekt som den står  
- **Justera**: behåll entryn men ändra något (specificity\_level, ta bort hallucinerad signal, korrigera span). Notera exakt vad som ska ändras.  
- **Stryk**: entryn håller inte måttet och kan inte räddas via justering

---

## Cell 1 Regel A (entries 1-4)

### Entry 1

**Text:** "Förslagsgruppen bestod av VD för Hvitfeldtska gymnasiets musiklinje och professor emeritus vid Göteborgs universitet."

**FAS A-annotering:**

- yrke: "VD för Hvitfeldtska gymnasiets" (hög)  
- organisation: "Hvitfeldtska gymnasiets musiklinje" (hög)  
- aggregat: "VD för Hvitfeldtska gymnasiets musiklinje", is\_identifiable=true

**Mitt beslut:** \[ \] Behåll  \[x\] Justera  \[ \] Stryk **Motivering:**   
Hvistfeldska gymnasiet har ingen VD, konstig formulering. Vad betyder emeritus? Organisationen är inte "Hvitfeldtska gymnasiets musiklinje" utan snarare "Hvitfeldtska gymnasiets"   
yrke: VD (hög)   
---

### Entry 2

**Text:** "Rektor på Hvitfeldtska gymnasiets musiklinje har bett mig att kontakta läkare i Göteborg om akut tandvård för hennes dotter."

**FAS A-annotering:**

- yrke: "Rektor" (hög)  
- organisation: "musiklinje" (hög)  
- aggregat: "Rektor på Hvitfeldtska gymnasiets musiklinje", is\_identifiable=true

**Mitt beslut:** \[ \] Behåll  \[x\] Justera  \[ \] Stryk **Motivering:** musiklinje är inte organisationen Hvitfeldtska gymnasiets är det. Rektor som hög är bra, unikroll, finns bara en rektor på gymnasiet. 

---

### Entry 3

**Text:** "Professor Lars Eriksson, rektor på Hvitfeldtska gymnasiets musiklinje, meddelade personalen att de förväntade sig ett ökat antal elever."

**FAS A-annotering:**

- organisation: "Hvitfeldtska gymnasiets musiklinje" (hög)  
- yrke: "rektor" (hög)  
- aggregat: "rektor på Hvitfeldtska gymnasiets musiklinje", is\_identifiable=true

**Mitt beslut:** \[ \] Behåll  \[x\] Justera  \[ \] Stryk **Motivering:** organisationen är inte "Hvitfeldtska gymnasiets musiklinje" utan bara "Hvitfeldtska gymnasiets". Rektor hög är korrekt. 

---

### Entry 4

**Text:** "En legitimerad tandläkare vid Västra Götalandsregionens tandvårdscenter i Borås har rapporterat ett misstänkt fall av bakterielinfektion."

**FAS A-annotering:**

- yrke: "tandläkare" (mellan)  
- plats: "Västra Götalandsregionens tandvårdscenter i Borås" (hög)  
- organisation: "Västra Götalandsregionens tandvårdscenter" (mellan)  
- aggregat: "tandläkare vid Västra Götalandsregionens tandvårdscenter i Borås", is\_identifiable=true

**Mitt beslut:** \[ \] Behåll  \[x\] Justera  \[ \] Stryk **Motivering:** yrket på mellan är bra. plats är enbart Borås och inte hela "Västra Götalandsregionens tandvårdscenter i Borås". Och den borde vara mellan och inte hög. 

---

## Cell 1 Regel B (entries 5-6)

### Entry 5

**Text:** "Sjuksköterskan på intensivvården vid Sahlgrenska Universitetssjukhuset i Göteborg tog emot patienten från Hallands sjukhus."

**FAS A-annotering:**

- yrke: "Sjuksköterskan" (mellan)  
- plats: "Sahlgrenska" (mellan)  
- organisation: "intensivvården vid Sahlgrenska Universitetssjukhuset" (hög)  
- aggregat: "Sjuksköterskan på intensivvården vid Sahlgrenska Universitetssjukhuset", is\_identifiable=true

**Mitt beslut:** \[ \] Behåll  \[x \] Justera  \[ \] Stryk **Motivering:** Just Sahlgrenska är gigantiskt, och det finns en hel del sjuksköterskor som jobbar där. Så tillsammans borde det kanske vara lågt. Samtidigt hade det varit på "Högsbo Vårdcentral" är det kanske annorlunda. Jag vet inte riktigt. Sen plats, organisation borde vara Sahlgrenska och plats borde vara Göteborg. 

---

### Entry 6

**Text:** "Förläggaren för den nya elbilen, Volvo Cars, har etablerat ett produktionscenter i Trollhättan. De anställda där arbetar som montörer och mekaniker med hög specialisering inom elbilsteknik."

**FAS A-annotering:**

- yrke: "montörer" (mellan)  
- plats: "Trollhättan" (mellan)  
- organisation: "Volvo Cars" (mellan)  
- aggregat: "Volvo Cars, har etablerat ett produktionscenter i Trollhättan. De anställda där arbetar som montörer", is\_identifiable=true

**Mitt beslut:** \[ \] Behåll  \[x\] Justera  \[\] Stryk **Motivering:** Just för Volvo Cars är det ett väldigt stort företag och just montörer är det väldigt många som är det. Jag (av personlig erfarnhet) tror att det finns kring 4000 montörer på Volvo Cars. Rollerna är inte identifierbara. Finns ingen tydlig koppling till en specifik person. Volvo cars borde vara lågt \= enligt sektion 4.3. 

borde vara yrke \= låg (många montörer)  
plats \= mellan  
organisation \= låg

---

## Cell 1 Regel C (entries 7-9)

### Entry 7

**Text:** "Den nya IT-säkerhetskonsulten som anställs efter den stora datalekkaget i höstas är mycket uppskattad av personalen på kontoret."

**FAS A-annotering:**

- yrke: "IT-säkerhetskonsulten" (mellan)  
- organisation: "kontoret" (mellan)  
- aggregat: "IT-säkerhetskonsulten som anställs efter den stora datalekkaget i höstas är mycket uppskattad av personalen på kontoret", is\_identifiable=true

**Mitt beslut:** \[ \] Behåll  \[\] Justera  \[x\] Stryk **Motivering:**   
Beror egentligen på kontext. Det står inget företagsnamn. "kontoret" borde vara lågt här för det säger egentligen ingenting.   
---

### Entry 8

**Text:** "Förstärkningen som kom från huvudkontoret efter coronapausen fick en plats på den tekniska avdelningen i Halmstad. Han började direkt med att implementera det nya system för datahantering, vilket ska göra arbetet mer effektivt."

**FAS A-annotering:**

- yrke: "Förstärkningen" (mellan)  
- plats: "Halmstad" (mellan)  
- aggregat: "Förstärkningen som kom från huvudkontoret efter coronapausen fick en plats på den tekniska avdelningen i Halmstad", is\_identifiable=true

**Mitt beslut:** \[ \] Behåll  \[\] Justera  \[x\] Stryk **Motivering:** gränsfall kanske men det funkar, Förstärkningen är inte ett yrke. 

---

### Entry 9

**Text:** "Det nya lagret på industrivägen öppnar i morgon och de första anställda börjar sin utbildning. Den ansvariga förlogistikstrategen, som flyttat hit från huvudkontoret i Stockholm, har gett tydliga instruktioner om hur man ska hantera den höga arbetsbelastningen."

**FAS A-annotering:**

- yrke: "logistikstrategen" (mellan)  
- organisation: "huvudkontoret i Stockholm" (mellan)  
- aggregat: "logistikstrategen, som flyttat hit från huvudkontoret i Stockholm", is\_identifiable=true

**Mitt beslut:** \[ \] Behåll  \[x\] Justera  \[ \] Stryk **Motivering:** Kan identifera vem det är. Borde behållas.Fel kategorisering. huvudkontorekt i Stocholm borde vara lågt, säger ingenting. Plats borde vara med istället "Stockholm" och organisation borde inte ens finnas. För inget i texten anger någon organisation

---

## Cell 2 Gränsfall (entries 10-16)

### Entry 10

**Text:** "Under mötesdagen diskuterade projektledaren och den ekonomiska experten från huvudkontoret om de nya budgetplanerna för deras gemensamma projekt i Uppsala."

**FAS A-annotering:**

- yrke: "projektledaren" (mellan)  
- yrke: "ekonomiska experten" (mellan)  
- (inget aggregat)

**Mitt beslut:** \[x\] Behåll  \[ \] Justera  \[ \] Stryk **Motivering:** lite svårt att säga kanske, men det borde funka egentligen just som ett gränsfall. 

---

### Entry 11

**Text:** "Han jobbade som projektledare på den kommunala vårdcentralen i Karlskrona under 2022\. Han var inte nöjd med sin lön och började leta efter nya möjligheter."

**FAS A-annotering:**

- yrke: "projektledare" (mellan)  
- organisation: "kommunala vårdcentralen" (mellan)  
- (inget aggregat)

**Mitt beslut:** \[ \] Behåll  \[x\] Justera  \[ \] Stryk **Motivering:** missade plats \= Karlskrona. och den borde dessutom vara mellan. 

---

### Entry 12

**Text:** "Lagledningen på konferensen diskuterade vikten av att anställa fler medarbetare med erfarenhet inom dataanalys och digital marknadsföring för att möta framtidens utmaningar."

**FAS A-annotering:**

- yrke: "medarbetare" (mellan)  
- organisation: "Lagledningen" (mellan)  
- (inget aggregat)

**Mitt beslut:** \[ \] Behåll  \[x\] Justera  \[ \] Stryk **Motivering:** jättesvårt att säga från min del, men kanske värt att ha det kvar. medarbetare borde vara lågt. lagledningen med. Ingen nämner specifika namn om företag. Lagledning är inte heller någon organisation. Så vi har yrke och inget mer. Antigen strykas eller gränsfall. Svårt att avgöra. 

---

### Entry 13

**Text:** "Det var flera anställda som uttryckte oro över den nya strukturen på kontoret i Göteborg. Samtliga rapporterade att de kände sig mindre trygga med den decentraliserade organisationen och framförallt bristen på tydlig kommunikation från ledningen."

**FAS A-annotering:**

- yrke: "anställda" (mellan)  
- organisation: "ledning" (mellan)  
- (inget aggregat)

**Mitt beslut:** \[ \] Behåll  \[ \] Justera  \[x\] Stryk **Motivering:** Säger egentligen inte mycket, väldigt generellt. "Anställda" pekar inte på just en individ, kan vara med som helst eller vilka som helst. "Ledning" är ingen organisation

---

### Entry 14

**Text:** "På mötet diskuterade vi med den nya ekonomichefen hur projektet skulle drivas framåt. Han har tidigare arbetat som konsult inom IT-sektorn, men är nu ansvarig för vår avdelning här på fabriken i Borås."

**FAS A-annotering:**

- yrke: "ekonomichef" (mellan)  
- organisation: "fabriken i Borås" (mellan)  
- (inget aggregat)

**Mitt beslut:** \[ \] Behåll  \[x\] Justera  \[ \] Stryk **Motivering:** organistaion borde vara låg "fabriken i Borås" är för generell. Finns många fabriker i Borås. Ekonomichef, skulle kunna vara hög, relativt unik position. 

---

### Entry 15

**Text:** "Det var en anställd på receptionen som berättade att de nya systemen för bokning av mötesrum skulle bli tillgängliga i höst. Hon nämnde också att personalen på IT-avdelningen jobbade hårt med det, men att det fortfarande var lite oklart när exakt de skulle vara färdiga."

**FAS A-annotering:**

- yrke: "anställd" (mellan)  
- organisation: "IT-avdelningen" (mellan)  
- (inget aggregat)

**Mitt beslut:** \[ \] Behåll  \[x\] Justera  \[ \] Stryk **Motivering:** IT-avdelnngen säger ingen ting, borde vara låg. IT-avdelningen på företag x säger mycket. Fel kategorisering. anställd och it-avdelningen borde båda vara låga? IT-avdelning är ingen organisation. 

---

### Entry 16

**Text:** "Avdelningschefen på vårdcentralen i Karlskoga diskuterade med den nya sjuksköterskan om patientflödet."

**FAS A-annotering:**

- yrke: "Avdelningschefen" (mellan)  
- yrke: "sjuksköterskan" (mellan)  
- (inget aggregat)

**Mitt beslut:** \[ \] Behåll  \[x\] Justera  \[ \] Stryk **Motivering:** återigen, missar Karlskoga som plats. Missar även organisation “vårdcentralen i Karlskoga”. Det är väl yrke \+ plats \= identiferbart. nu är det bara yrke \+ yrke, säger inte mycket. men den kan annars funka 

---

## Cell 3 Inga signaler (entries 17-22)

### Entry 17

**Text:** "Den automatiserade processen aktiverades klockan 14.37. En loggsändning registrerades med kodnamn 'Fjärilsdans'. Det följande skedet, 'Stjärnfall', väntas inledas inom de närmaste fem minuterna."

**FAS A-annotering:** (tom expected\_findings)

**Mitt beslut:** \[x\] Behåll  \[ \] Justera  \[ \] Stryk **Motivering:** \_

---

### Entry 18

**Text:** "Systemet registrerar automatiskt alla förändringar i databasen. Varje uppdatering sparas med en timestamp för fullständig historik."

**FAS A-annotering:** (tom expected\_findings)

**Mitt beslut:** \[x\] Behåll  \[ \] Justera  \[ \] Stryk **Motivering:** \_

---

### Entry 19

**Text:** "Protokollen för uppdatering av databasen kommer att ske vid två tillfällen per dag. Första gången sker klockan 07:00 och den andra klockan 15:00. Under perioden mellan dessa uppdateringar kan det uppstå små variationer i informationen."

**FAS A-annotering:** (tom expected\_findings)

**Mitt beslut:** \[x\] Behåll  \[ \] Justera  \[ \] Stryk **Motivering:** \_

---

### Entry 20

**Text:** "En ny regel för hantering av digitala filer implementeras den 15 november. Det innebär att alla dokument ska sparas i en centraliserad plats med automatiskt numreringssystem."

**FAS A-annotering:** (tom expected\_findings)

**Mitt beslut:** \[x\] Behåll  \[ \] Justera  \[ \] Stryk **Motivering:** \_

---

### Entry 21

**Text:** "Automatiserad processen genomfördes enligt schema. Dataanalysen visade en ökning i volym under perioden, vilket påverkade systemhastigheten. Vidare utvärderades algoritmen för att minska energiförbrukning."

**FAS A-annotering:** (tom expected\_findings)

**Mitt beslut:** \[x\] Behåll  \[ \] Justera  \[ \] Stryk **Motivering:** \_

---

### Entry 22

**Text:** "Enligt protokoll från den senaste iterationen ska den optimerade modellen gå igenom en komplex serie testfall. Syftet är att säkerställa att algoritmen hanterar olika scenarier korrekt och utan fel."

**FAS A-annotering:** (tom expected\_findings)

**Mitt beslut:** \[x \] Behåll  \[ \] Justera  \[ \] Stryk **Motivering:** \_

---

## Cell 4 Signaler men inte identifierande (entries 23-29)

### Entry 23

**Text:** "Att jobba som försäljningskonsult i Malmö kan vara utmanande, men också väldigt givande. Det är viktigt att ha god kundservice och ett starkt nätverk för att lyckas."

**FAS A-annotering:**

- yrke: "försäljningskonsult" (mellan)  
- plats: "Malmö" (mellan)

**Mitt beslut:** \[ \] Behåll  \[x\] Justera  \[ \] Stryk **Motivering:** Malmö (låg) enligt guide, de i kombination borde vara låg. 

---

### Entry 24

**Text:** "På mötet diskuterade vi behovet av fler lärare inom den digitala utbildningen i Stockholm."

**FAS A-annotering:**

- yrke: "lärare" (låg)  
- plats: "Stockholm" (mellan)

**Mitt beslut:** \[ \] Behåll  \[x\] Justera  \[ \] Stryk **Motivering:** Stockholm (låg) enligt guide

---

### Entry 25

**Text:** "Förra veckan deltog många lärare från Stockholm i konferensen om digitalisering inom skolan."

**FAS A-annotering:**

- yrke: "lärare" (låg)  
- plats: "Stockholm" (mellan)

**Mitt beslut:** \[ \] Behåll  \[x \] Justera  \[ \] Stryk **Motivering:** Stockholm (låg) enligt guide

---

### Entry 26

**Text:** "På mötet diskuterade vi hur många anställda som arbetade på kontoret i Stockholm."

**FAS A-annotering:**

- yrke: "anställda" (låg)  
- plats: "Stockholm" (låg)

**Mitt beslut:** \[x \] Behåll  \[ \] Justera  \[ \] Stryk **Motivering:** \_

---

### Entry 27

**Text:** "Det är alltid roligt att träffa nya kollegor på konferenser. I år var många från banksektorn i Stockholm."

**FAS A-annotering:**

- yrke: "banksektorn" (låg)  
- plats: "Stockholm" (mellan)

**Mitt beslut:** \[ \] Behåll  \[x\] Justera  \[ \] Stryk **Motivering:** STOCKHOLM SKA VARA ALLTID VARA LÅG. "banksektorn" är inte riktigt ett yrke

---

### Entry 28

**Text:** "Vi har fått många ansökningar om tjänster som ekonomichef i Malmö, men det var svårt att hitta rätt profil."

**FAS A-annotering:**

- yrke: "ekonomichef" (mellan)  
- plats: "Malmö" (mellan)

**Mitt beslut:** \[ \] Behåll  \[x\] Justera  \[ \] Stryk **Motivering:** Malmö borde vara låg. 

---

### Entry 29

**Text:** "De nya anställda inom försäljningsavdelningen fick sig ett välkomnande möte i förra veckan. Bland annat fick de träffa den lokala HR-chefen som berättade om företagets vision och värderingar."

**FAS A-annotering:**

- yrke: "HR-chef" (mellan)  
- plats: "lokala" (låg)

**Mitt beslut:** \[ \] Behåll  \[\] Justera  \[x\] Stryk **Motivering:** Jag fattar inte vad den texten ska medföra egentligen. “Lokala” är ingen plats.

---

## Sammanfattning (fyll i efter slutförd granskning)

**Antal Behåll:** 8 / 29 **Antal Justera:** 17 / 29 **Antal Stryk:** 4 / 29

**Cell-fördelning efter granskning:**

- Cell 1: 7 (av 9 ursprungligen) — entries 7 och 8 strukna
- Cell 2: 6 (av 7) — entry 13 struken
- Cell 3: 6 (av 6) — alla godkänns
- Cell 4: 6 (av 7) — entry 29 struken

**Underrepresenterade celler som behöver manuell komplettering:** Cell 1 tappade 2 entries (entries 7 och 8) och är nu 7 — acceptabelt men tight. Cell 2 är nere på 6 efter att entry 13 strukits — fungerar men kan behöva en ny gränsfallsentry. Rekommendation: generera minst 1 ny Cell 1 Regel C-entry och överväg 1 ny Cell 2-entry.

**Divergenspunkter mellan granskarna:**

| Entry | Abdulla | Johanna | Konsensus | Motivering |
|---|---|---|---|---|
| 6 | Justera | Stryk | Justera | Texten håller men annoteringar korrigeras (yrke=låg, organisation=låg) |
| 9 | Justera | Stryk | Justera | Texten är identifierbar — behålls med rättade annoteringar (plats=Stockholm, organisation tas bort) |
| 13 | Stryk | Justera | Stryk | Texten är för generell; "anställda" och "ledning" ger inte identifierbar signal ens med korrigering |
| 23 | Behåll | Justera | Justera | Malmö ska vara låg enligt guiden — annoteringskorrigering krävs |
| 29 | Justera | Stryk | Stryk | "lokala" är ingen plats; texten ger inte tillräcklig signal för Cell 4 |

**Övergripande kommentar:** Granskarna var eniga om de flesta beslut — samtliga Cell 3-entries godkänns, entries 7 och 8 stryks av båda (ingen organisation eller korrekt yrkesbeteckning = Regel C uppfylls inte), och stockholms-/malmö-problematiken identifierades oberoende av varandra. Det vanligaste annotationsfelet är att storstäder klassificeras som "mellan" när de ska vara "låg". Övriga systematiska fel: felaktiga organisationsspann i entries 1–3 (musiklinje vs Hvitfeldtska gymnasiet), saknade plats- och organisationssignaler i entries 11 och 16, och "banksektorn" i entry 27 är inte ett yrke. Konsensus löste fem divergenspunkter: entry 6 och 9 behålls (texterna är identifierbara men annoteringar fel), entry 13 stryks (texten räddas inte via korrigering), entry 23 justeras (Malmö=låg), entry 29 stryks (lokala inte en plats).