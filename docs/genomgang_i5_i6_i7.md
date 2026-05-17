# Genomgång: I-5, I-6, I-7 och I-7-spårarbetet (I-7a→g)

> **Vad detta dokument är:** en informell, pedagogisk genomgång av vad som hänt
> i koden under iteration 3 — skriven för att kunna förklaras vidare till
> teamkollega. Detta är **inte** SSOT. Auktoritativa källor är
> `docs/arkitektur.md` (arkitektur), `docs/iteration_3_implementation.md`
> (sessionsloggar), `docs/iteration_3_utvardering.md` Del 8/9 (siffror) och
> Loggboken iteration 3 (beslutsmotiveringar). Vid konflikt gäller dem, inte
> detta dokument.

---

## 0. Den korta versionen (säg detta först till Johanna)

Vid slutet av iteration 2 låg vi på **Precision 64 % / Recall 89 % / F1 75 %**.
Problemet var precisionen: **117 falska positiva** — systemet skrek "personuppgift!"
på massor av text som inte var det.

Efter iteration 3:s pipeline-arbete ligger vi på **Precision 75 % / Recall 91 % /
F1 82 %**, och med den större lokala modellen (qwen3:14b) på **Precision 83 % /
Recall 91 % / F1 87 %**.

Den förbättringen kommer från **två** saker, inte tjugo:

1. **En enda rad kod (I-7c):** vi slutade felklassa ortnamn som gatuadresser.
   Det ensamt lyfte precisionen från 64 % till 75 %.
2. **Modellbytet (probe #107):** qwen3:14b hallucinerar inte känsliga
   kategorier lika ofta som qwen2.5:7b gjorde. Det lyfte precisionen från
   75 % till 83 %.

Allt annat (I-5, I-6) **flyttade inte siffrorna** — och det är i sig ett
viktigt forskningsresultat, inte ett misslyckande. Mer om det nedan.

---

## 1. Bakgrund: vad var sönder efter iteration 2?

En FP-rotorsaksanalys (2026-05-04) bröt ner de 117 falska positiva på orsaker.
De stora bidragen:

| Rotorsak | Ungefärlig FP-volym | Åtgärd i iteration 3 |
|---|---|---|
| `article4.adress` blandas ihop med `context.plats` | 17 FP (+ motsv. FN) | I-2 (alias) + **I-7c (själva fixen)** |
| CombinationLayer övertaggar `context.yrke` / `context.organisation` | 53 FP | I-1 (promptskärpning) |
| Aggregatorn dubbelräknar samma kategori över lager | 11 FP | I-3 (deduplicering) |
| Svaga artikel 9-kategorier | — | I-4 (prompt v6 → rollback till v5) |

Recall var redan bra (89 %). Hela iteration 3:s pipeline-mål var: **lyft
precisionen mot ~80 % utan att tappa recall**.

---

## 2. I-5 — Tvådimensionsoperationalisering (#105)

### Vad vi gjorde

Tidigare hade en klassificering **ett** mått: `SensitivityLevel`
(NONE/LOW/MEDIUM/HIGH) plus ett `mechanism_used`-fält som beskrev *hur*
bedömningen togs. Det blandade ihop två helt olika frågor:

- **Hur identifierbar** är personen? (GDPR artikel 4)
- **Hur känslig** är uppgiften? (GDPR artikel 9 / 10)

I-5 delade upp detta i **två oberoende dimensioner** i kärnmodellen:

- `Identifiability`: **NONE / INDIRECT / DIRECT**
- `DataClass`: **NONE / SPECIAL / CRIMINAL**

`SensitivityLevel` finns kvar, men **härleds** nu från paret via en ren
funktion `derive_sensitivity(identifiability, data_class)` — en deterministisk
9-cellstabell:

|              | NONE | SPECIAL | CRIMINAL |
|--------------|------|---------|----------|
| **NONE**     | NONE | LOW     | LOW      |
| **INDIRECT** | LOW  | MEDIUM  | MEDIUM   |
| **DIRECT**   | LOW  | HIGH    | HIGH     |

Fältet `mechanism_used` togs **bort** helt — paret (identifiability, data_class)
bär hela klassifikationen, så "hur" blev redundant.

### Varför vi gjorde det

GDPR behandlar de här två sakerna som separata axlar. En direkt identifierbar
person med bara ett namn är inte "känslig" men är personuppgift; en anonym
mening om en sjukdom är artikel 9-känslig men inte identifierande. Att tvinga
in båda i en enda skala dolde information. V1/V4-intressenterna i iteration 2:s
utvärdering bad uttryckligen att få **se de två skalorna separat** i demon.

Detta gjordes i tre commits + en fixup (där den första, glidande
NONE/LOW/MEDIUM/HIGH-modellen ersattes med den kategoriska NONE/INDIRECT/DIRECT
efter en GDPR-juridisk omläsning — det är Beslut 49 reviderad).

### Varför det INTE ändrade siffrorna

Det här är centralt och måste sägas tydligt: **I-5 är en modellrefaktorering,
inte en precisionsåtgärd.** Det ändrar *hur systemet redovisar* en
klassificering, inte *vilka fynd det hittar*. Precision/recall/F1 räknas på
fyndnivå och rörs inte av att vi byter representation av känslighet. Värdet av
I-5 är arkitektoniskt (renare domänmodell, spårbar mot GDPR-artiklarna) och
ligger som underlag till designprinciperna i fas 4 — inte i mätvärdena.

### Kärnändringar (filer)

- `gdpr_classifier/core/classification.py` — nya enums `Identifiability`,
  `DataClass`; `mechanism_used` borttaget.
- `gdpr_classifier/aggregator.py` — `derive_sensitivity` (ren funktion),
  `_determine_dimensions` ersätter gamla `_determine_sensitivity`.
- `evaluation/report.py` + `runner.py` — `MechanismStats` → `DimensionStats`.
- `demo/callbacks.py` — två separata färgade skalor sida vid sida i UI.

---

## 3. I-6 — Empirisk tröskelkalibrering (#106)

### Vad vi *trodde* vi skulle göra

Idén var: aggregatorn har tre trösklar (`medium_threshold`,
`high_confidence_bypass`, `min_evidence_count`). Skruva på dem i ett rutnät av
16 konfigurationer och hitta de som lyfter precisionen mot ~80 %.

### Vad vi faktiskt hittade — "invariansfyndet"

Vi körde 14 av 16 konfigurationer. **TP/FP/FN var exakt 212/100/21 i alla 14.**
Trösklarna ändrade ingenting i mätvärdena.

Förklaringen är arkitektonisk och elegant: trösklarna styr bara
`Classification.identifiability` (slutbedömningens dimensionsetikett). Men
TP/FP/FN räknas på **fyndlistan**, och fyndlistan är redan färdig *innan*
aggregatorns tröskellogik kör. Matcher/lager (Lager 1–3) och aggregatorn
(Lager 4) är medvetet separerade (Single Responsibility, Beslut 18).

**Konsekvens:** att lyfta precisionen via trösklar är inte "svårt" — det är
**arkitektoniskt omöjligt**. Det var det egentliga forskningsfyndet. I-6
omformulerades (Beslut 51): behåll Beslut 20-defaultarna
(0.7 / 0.85 / 2), och leverera i stället en **arkitektonisk designinsikt** till
rapporten.

### Sidofyndet: num_ctx-buggen (Beslut 50)

Under I-6 upptäcktes att `OllamaProvider` aldrig satte `num_ctx`. Ollama
defaultade då till **4096 tokens**, men våra Article9-prompter var ~6000 tokens
— alla 79 mätta texter låg över gränsen. Prompterna trunkerades tyst.

Vi satte explicit `num_ctx=16384`. Den **empiriska** effekten visade sig
försumbar (F1 −0.15 pp, inom brus — Ollama trunkerar tydligen från
prompt-början, inte själva texten). Men fixen är **arkitektoniskt** korrekt:
providern får inte vara beroende av vad Ollama Desktop råkar ha för
klient-default (DP3-symmetri mot molnprovidern).

### Kärnändringar (filer)

- `gdpr_classifier/layers/llm/ollama_provider.py` — `num_ctx=16384` explicit.
- Ingen tröskeländring (defaults behållna). TEMP-instrumentering
  arkiverad i `docs/iteration_3_temp_instrumentation_archive.md`.

---

## 4. I-7 / Probe #107 — Modellskalningsprob

Probe-frågan: **är prestandataket i Lager 3 (Article9Layer) och Lager 4
(CombinationLayer) modellbundet eller uppgiftsbundet?** Dvs — om vi ger
pipelinen en *större* lokal modell, löser det problemet, eller är själva
uppgiften så svår att en större modell inte hjälper?

Sex checkpoints, qwen2.5:7b-instruct jämfört med qwen3:14b:

- **Cp 1:** smoke-test (qwen3:14b laddar, svarar svenska, giltig JSON).
- **Cp 2:** infrastruktur (`AEGIS_MODEL`-env, `--subset`-flagga).
- **Cp 3 (Lager 3, 52 texter):** qwen3 lyfter F1 +10 pp, **precision-drivet**.
- **Cp 4 (Lager 4, 27 texter):** ingen materiell förbättring (inom brus).
- **Cp 5 (full pipeline):** +2.98 pp F1 globalt, precision-drivet.
- **Cp 6 (post-I-7g, ren metodik):** se siffror nedan.

### Probe-svaret (med nyans)

Resultatet är **asymmetriskt per lager**:

- **Lager 3 (Article9Layer) är modellbundet.** qwen3 fångar indirekta
  artikel 9-ledtrådar som qwen2.5 missade ("sin flickvän" → sexuell läggning,
  "fira påsk i kyrkan" → religiös övertygelse). `sexuell_laggning` och
  `religios_overtygelse` går till 100 % F1.
- **Lager 4 (CombinationLayer) lyfter bara måttligt** — pusselbitsbedömningen
  enligt skäl 26 är en kvalitativ resonemangsuppgift som en större modell inom
  samma familj inte löser påtagligt bättre. Det pekar mot **uppgiftsbundet**.
- En materiell **`context.plats`-regression** fördjupas faktiskt med den
  större modellen (qwen3 övertaggar vardagsord som "kyrkan", "sjukhuset" som
  plats). Probe-arbetets enda materiella försämring.

Slutsats: taket är inte enhetligt — modellbundet på Lager 3:s precision,
uppgiftsbundet på Lager 4:s kvalitativa bedömning.

---

## 5. I-7a→g — Cross-Validating Aggregator (sidospåret som lyfte precisionen)

Detta är ett **sidospår** (#133–#140) som ligger på probe-branchen
`107-probe-...`, inte mergat till main. Sju delissues:

### I-7a — Designspecifikation

Skrev `docs/arkitektur.md` §9.6: en **evidensvägningspolicy** med en deklarativ
beslutstabell R1–R7 per (lager, kategori). Generaliserar gamla "Mekanism 3"
(som bara gällde `context.kombination`) till en allmän primitiv. Ingen kod —
bara spec.

### I-7b — Implementation av transparenslagret

Implementerade specen i kod **utan att ändra klassificeringen**:

- `Finding.evidence_basis` — ny tagg: `no_support_required` /
  `high_confidence_no_support` / `structural_support`.
- `Classification.weakest_evidence_basis` — sammandrag på toppnivå.
- `cross_validation_mode`-flagga (`legacy` / `cross_validating`),
  default `legacy` initialt.
- `_count_structural_support` — generaliserad Mekanism 3-primitiv.

Viktigt: `cross_validating` lägger bara **etiketter** på fynden. Det ändrar
inte `identifiability`, `data_class` eller `sensitivity`. Det är ett rent
**transparenslager** — systemet redovisar *varför* det tror på ett
kombinationsfynd, men beslutar samma sak.

### I-7c — DEN HÄR ÄR PRECISIONSFIXEN (#135)

> Detta är ändringen du frågade om — "article 4 adress går inte längre direkt
> till entity location". Egentligen var det tvärtom: **entity-location gick
> tidigare till article4.adress**, och det är det vi slutade med.

**Före:** EntityLayer använder SpaCy:s namnigenkänning (NER). SpaCy taggar
geografiska namn med etiketten `LOC`. Mappningstabellen `_label_map` sa:

```python
"LOC": (Category.ADRESS, "entity.spacy_LOC")   # gammalt
```

Alltså: varje gång SpaCy hittade "Göteborg", "Stockholm", "Mellanöstern" →
tystnade det som **`article4.adress`** (en personuppgift, en gatuadress till en
fysisk person).

**Problemet:** ett ortnamn är **inte** en gatuadress till en specifik person
enligt GDPR artikel 4. "Han bor i Göteborg" identifierar inte en individ.
Resultatet var att systemet genererade **systematiska falska positiva** — varje
stadsnamn i korpusen blev en felaktig `article4.adress`-träff.

**Fixen (en rad):**

```python
"LOC": (Category.PLATS, "entity.spacy_LOC")     # nytt
```

Nu mappas `LOC` till **`context.plats`** — en *kontextuell* signal (en
pusselbit enligt skäl 26), inte en personuppgift i sig. Source-taggen
`entity.spacy_LOC` **bevaras medvetet**, så att den generaliserade Mekanism 3
fortfarande kan räkna ett ortnamn som *strukturellt stöd* när det ingår i en
verklig pusselbitskedja.

Detta är en omprövning av **Beslut 11** från en tidigare iteration.

**Effekten (det här är siffran att visa Johanna):**

| | it2 | efter I-7c |
|---|---|---|
| `article4.adress` FP | 22 | **0** |
| `article4.adress` recall | 93,33 % | 93,33 % (oförändrad) |
| `entity`-lagrets precision | 51,58 % | **76,27 %** |
| **Total precision** | **64,00 %** | **75,18 %** (+11,18 pp) |
| Total recall | 89,27 % | 90,99 % (steg också) |

Hela precisionslyftet i pipeline-arbetet kommer från den här raden. Recall
sjönk inte — den steg till och med.

**Varför recall inte kraschade:** I-2 (#102) hade redan lagt ett
**matcher-alias** `{ADRESS, PLATS}` i `evaluation/matcher.py`. Facit har ~12
"nakna städer" annoterade som `article4.adress`. Utan aliaset hade de blivit
falska negativa när vi bytte kategori. Aliaset gör att ett predikterat
`context.plats` ändå matchar en `article4.adress`-etikett i utvärderingen —
mätinstrument-FN blev **0**. (Det här aliaset är en öppen punkt: det neutraliserar
mätinstrumentskiftet, men ska omprövas — se Del 8:s begränsningar.)

### I-7d — Dubbel baslinjemätning

Bevisade experimentellt: `legacy` och `cross_validating` ger **byte-identiska**
klassifikationsutfall (0/159 avvikelser). Hela den mätbara precisionseffekten
ligger mot iteration-2-baslinjen och syns lika i båda lägena — den är I-7c, inte
`cross_validating`. Hypoteserna H1 (precision upp, recall hålls), H2 (artikel
9-recall ej sämre) och H3 (transparens kvantifierad) infriades.

### I-7e — Source-medveten evidensräkning

Fixade en blind fläck i mätinstrumentet: dedupliceringen tog bort
`entity.spacy_LOC`-stöd *innan* evidensvägningen hann se det. Efter fixen
(mode-gateat `deduplicated_sources`-tillägg) flyttades 6 kombinationsfynd från
"bara hög konfidens" till "har strukturellt stöd" — `structural_support` gick
**5 % → 35 %**. Inte en beteendeändring, en *mätinstrumentförbättring*.

### I-7f — Omkörning + Del 8-uppdatering

Körde om baslinjen på post-I-7e-koden. Konfusionsmatrisen oförändrad
(212/70/21). Bekräftade I-7e:s mode-gate på korpusskala.

### I-7g — Default-flipp

Bytte default `legacy` → `cross_validating` så att den naturalistiska
utvärderingen (I-18) automatiskt får den rättvisande evidensredovisningen.
Eftersom modes är byte-identiska i klassificering är detta en ren
transparens-leverans, ingen precisions-/recall-ändring.

### Checkpoint 6 — qwen3:14b på den färdiga koden

| Konfiguration | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| qwen2.5:7b (post-I-7g baslinje) | 212 | 70 | 21 | 75,18 % | 90,99 % | 82,33 % |
| **qwen3:14b** | 213 | **44** | 20 | **82,88 %** | **91,42 %** | **86,94 %** |
| Δ | +1 | **−26** | −1 | **+7,70 pp** | +0,43 pp | +4,61 pp |

Precision-drivet (FP 70 → 44, nästan platt recall). En read-only-efteranalys
verifierade att lyftet är **ärligt** — qwen3 slutar hallucinera
Lager 3/4-taggar som qwen2.5 hittade på ("sökt för samma besvär" →
felaktig `article9.halsodata`; "leddes av" → felaktig `context.yrke`). Detta
föranledde omprövning av Beslut 17 — qwen3:14b är nu default lokal modell.

---

## 6. Sammanfattning: arkitektoniska kärnändringar

| Fil | Ändring | Issue |
|---|---|---|
| `core/classification.py` | `Identifiability` + `DataClass` enums; `mechanism_used` borttaget; `weakest_evidence_basis` tillagt | I-5, I-7b |
| `core/finding.py` | `evidence_basis`-fält tillagt | I-7b |
| `aggregator.py` | `derive_sensitivity` (ren 9-cellsfunktion); `_determine_dimensions` ersätter `_determine_sensitivity`; `cross_validation_mode`; `_apply_evidence_weighting` (R1–R7); `_count_structural_support` (generaliserad Mek 3); default nu `cross_validating` | I-5, I-7b/e/g |
| `layers/entity/entity_layer.py` | **`_label_map` LOC: `Category.ADRESS` → `Category.PLATS`** (source bevarad) | **I-7c** |
| `evaluation/matcher.py` | `CATEGORY_ALIASES = {ADRESS, PLATS}` | I-2 |
| `evaluation/report.py` + `runner.py` | `MechanismStats` → `DimensionStats` | I-5 |
| `layers/llm/ollama_provider.py` | `num_ctx=16384` explicit | I-6 |

**Den enda raden som flyttade precisionen mest:** `entity_layer.py` rad 21.
Allt annat var antingen stödarbete (alias, dedup, prompt), transparens
(evidence_basis) eller forskningsfynd som visade att en åtgärd *inte* gick
(I-6:s invarians).

---

## 7. Resultatresan i en mening per steg

1. **it2-slut:** P 64 / R 89 / F1 75 — 117 FP, precisionsproblem.
2. **I-1/I-2/I-3/I-4:** stödåtgärder (promptskärpning, alias, dedup); I-4
   rullades tillbaka (negativ empiri).
3. **I-5:** delade känslighet i två dimensioner — renare modell, **rörde inte
   siffrorna**.
4. **I-6:** upptäckte att trösklar *inte kan* flytta siffrorna (invarians) +
   fixade num_ctx; behöll defaults.
5. **I-7c:** slutade felklassa ortnamn som adress → **P 64 → 75 %**.
6. **I-7b/d/e/f/g:** byggde och bevisade transparenslagret runtomkring (ändrar
   inte klassificeringen).
7. **Probe #107 / qwen3:14b:** bättre modell hallucinerar mindre → **P 75 →
   83 %, F1 87 %**.
