# Testdata: Iteration 1 (Artikel 4-texter, Lager 1 + Lager 2)

Denna katalog innehåller testdatasetet för utvärdering av
gdpr-classifierns Lager 1 (`PatternLayer` — mönster- och
checksummabaserad igenkänning) och Lager 2 (`EntityLayer` — NER).
Filen `test_dataset.json` innehåller 80 entries: 68 positiva (med
förväntade fynd) och 12 okänsliga negativa kontroller.

## Konstruktionsmetod

Till skillnad från iteration 2 (Lager 3/4) konstruerades detta dataset
**innan** projektet formaliserade en datakonstruktionsmetodik. Det
finns därför **ingen** hybrid FAS A/FAS B-process, **ingen**
språkmodellsgenerering, **ingen** oberoende dubbelgranskning med
konsensuskrav och **inget** Data Statement enligt Bender & Friedman
(2018) för denna iteration.

Texterna konstruerades **manuellt av projektteamet** mot
issue-specifikationerna #18–#20 (minimiantal per kategori). Ett
temporärt Python-skript användes enbart för att bygga JSON-strukturen,
beräkna korrekta 0-indexerade teckenpositioner (kritiskt för `åäö`)
och validera spans och checksummor med `assert` — skriptet genererade
inte textinnehållet. Edge-case-texter (olika format, landsnummer,
okänslig kontext, parenteser) lades till manuellt enligt
specifikationen. Korrekta Luhn- och mod97-kontrollsiffror infördes för
hand efter att placeholder-checksummor upptäckts ge recall 0 % i
integrationstestet. Den fullständiga konstruktions- och
felsökningshistoriken finns i sessionsloggarna i
[`docs/iteration_1_planering.md`](../../../docs/iteration_1_planering.md).

## Kategorifördelning (förväntade fynd)

| Kategori | Fynd | Detekteras av |
|---|---|---|
| article4.namn | 33 | Lager 2 (NER) |
| article4.email | 19 | Lager 1 (mönster) |
| article4.personnummer | 18 | Lager 1 (Luhn) |
| context.organisation | 17 | Lager 2 (NER) |
| article4.adress | 15 | Lager 2 (NER) |
| article4.telefonnummer | 15 | Lager 1 (mönster) |
| article4.iban | 11 | Lager 1 (mod97) |
| article4.betalkort | 6 | Lager 1 (Luhn) |

## Känd begränsning: Lager 2 var en stub i iteration 1

`EntityLayer` (Lager 2 / NER) var en stub som returnerade tom lista
under iteration 1. Etiketterna för namn, adress och organisation fanns
i datasetet men testades inte funktionellt förrän NER implementerades i
iteration 2. Samma `test_dataset.json` används därefter som
utvärderingsunderlag för både Lager 1 och Lager 2.

## Förhållande till projektets datadeklaration

Detta dataset omfattas av repots övergripande deklaration att all data
är syntetisk; inga verkliga personuppgifter har hanterats
(Privacy by Design). Se [`DATA.md`](../../../DATA.md) i repo-roten.

Att detta dataset saknar ett formellt Data Statement är en medveten och
transparent konsekvens av att det föregår den metodformalisering som
infördes i iteration 2. Mognaden i datakonstruktionsmetodiken mellan
iteration 1 och 2 är ett resultat av projektets iterativa lärande
(Action Design Research) och dokumenteras som sådant i rapporten.
