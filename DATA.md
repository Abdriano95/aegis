# Datadeklaration

> Auktoritativ, kortfattad deklaration om all data i detta repo. Den
> fullständiga metodologiska redogörelsen för iteration 2:s dataset
> (Lager 3/4 — curation rationale, Data Statement enligt Bender &
> Friedman 2018, granskningsprotokoll, kända begränsningar) finns i
> [`tests/data/iteration_2/data_statement.md`](tests/data/iteration_2/data_statement.md)
> och [`tests/data/iteration_2/README.md`](tests/data/iteration_2/README.md).
> Iteration 1:s dataset (Lager 1/2) konstruerades med en annan, mindre
> formaliserad metod som beskrivs i
> [`tests/data/iteration_1/README.md`](tests/data/iteration_1/README.md).

## All testdata är syntetisk

Detta repo är artefakten i ett akademiskt examensarbete om automatisk
GDPR-klassificering av svensk text. **All test-, utvärderings- och
demonstrationsdata är syntetisk.** Detta gäller samtliga dataset under
`tests/data/`, alla genererade exempel i `scripts/`, samtliga
demo-snapshots under `demo/snapshots/` och alla exempeltexter i `docs/`.

### Personuppgifter

Alla personuppgifter i datan är **helt fabricerade** och avser, beskriver
eller härrör **inte** från någon verklig fysisk person. Detta omfattar
utan begränsning:

- namn på individer (för- och efternamn),
- personnummer och samordningsnummer,
- e-postadresser och telefonnummer,
- adresser,
- hälsouppgifter och övriga särskilda kategorier av personuppgifter
  enligt GDPR artikel 9 samt uppgifter enligt artikel 10.

Texterna skapades med olika metoder beroende på iteration. Iteration
1:s dataset (Lager 1/2, `tests/data/iteration_1/`) konstruerades
manuellt av projektteamet mot issue-specifikationer, med ett
engångsskript enbart för att beräkna korrekta teckenpositioner och
validera checksummor — ingen språkmodell genererade innehållet.
Iteration 2:s dataset (Lager 3/4, `tests/data/iteration_2/`) skapades
enligt en formaliserad hybridmetod: språkmodellsgenererade kandidater
(FAS A) följt av oberoende manuell granskning med konsensuskrav
(FAS B). Inga verkliga personuppgifter har vid något tillfälle
hanterats, samlats in eller behandlats i projektet (Privacy by Design). Eventuell likhet mellan ett syntetiskt namn och en
verklig person är en oavsiktlig och statistiskt ofrånkomlig egenskap hos
fabricerad provdata och innebär ingen koppling till den personen.

### Organisations- och myndighetsnamn

Vissa texter och annoteringsriktlinjer innehåller namn på verkliga
organisationer, företag och myndigheter (t.ex. Volvo, Ericsson, SEB,
IKEA, Skatteverket, Försäkringskassan, Sahlgrenska Universitetssjukhuset,
Göteborgs universitet, Hvitfeldtska gymnasiet, Borås Stad,
Västra Götalandsregionen, Högskolan i Borås). Dessa är **offentliga
entiteter** som används **enbart som realistiska, icke-individ­identifierande
exempel** för att efterlikna språkbruket i autentisk arbetsplatstext.

Förekomsten av ett organisationsnamn innebär **inte**:

- att någon verklig data om organisationen behandlas eller förekommer,
- någon koppling, partnerskap, sponsring eller medverkan,
- något påstående om eller riktat mot organisationen i fråga.

## Personer i projektet

De enda verkliga personer som namnges i repot är projektets
upphovspersoner och handledare (Abdulla Mehdi, Johanna Gull, handledare
Johannes Sahlin vid Högskolan i Borås) samt akademiskt citerade
författare i referenslistan ([`docs/arkitektur.md`](docs/arkitektur.md)
§15). Inga andra verkliga individer förekommer.

## Licens

Koden licensieras under MIT (se [`LICENSE`](LICENSE)). Datadeklarationen
ovan är ett klargörande om datans natur och påverkar inte
licensvillkoren.
