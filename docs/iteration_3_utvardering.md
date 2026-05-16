## Del 8: Dubbel baslinjemätning — `legacy` mot `cross_validating` (I-7d, uppdaterad post-I-7e i I-7f)

> **Uppdateringsnot (I-7f, 2026-05-16).** Del 8 är omkörd på post-I-7e-koden
> (commit `2d6c302`). I-7e gjorde `_count_structural_support` source-medveten via
> ett **mode-gateat** `deduplicated_sources`-tillägg i `cross_validating`-läget
> (`docs/arkitektur.md` §9.6.5). Pre-I-7e-talen (I-7d, commit `e6ab2f8`) **bevaras
> ordagrant** nedan; post-I-7e-talen redovisas parallellt så att I-7e:s faktiska
> effekt är synlig. H1 och H2:s falsifieringsvillkor är **oförändrade** (de mäter
> mot iteration-2-baslinjen, inte mot modes). H3:s formulering utökas från en
> ren andelsmätning till en **delta-analys** pre-I-7e → post-I-7e (8.4). Pre-I-7e-
> snapshots är arkiverade till `demo/snapshots/i7d_{legacy,cross_validating}_pre_i7e.json`.

### 8.1 Bakgrund och hypoteser

Cross-Validating Aggregator-arbetsströmmen har levererat tre konstruktions-
issues: I-7a (designspecifikation, `docs/arkitektur.md` §9.6), I-7b
(implementation av `cross_validation_mode` med `evidence_basis`-taggning och
generaliserad Mekanism 3) och I-7c (EntityLayer mappar SpaCy `LOC` till
`context.plats` i stället för `article4.adress`, source-taggen
`entity.spacy_LOC` bevarad). I-7d är arbetsströmmens enda mätfokuserade
leverans: ett kontrollerat experiment som kvantifierar den samlade effekten av
I-7b plus I-7c mot iteration-2-baslinjen.

En avgörande klargöring styr hur resultatet redovisas. `cross_validating`-läget
i I-7b lägger `evidence_basis`-taggar på `context.kombination`-fynd och härleder
`weakest_evidence_basis` på `Classification`. Det ändrar **inte** vilka fynd som
finns, **inte** `identifiability`, **inte** `data_class`, **inte**
`sensitivity` — `_determine_dimensions` och `_has_validated_kombination` är inte
mode-gatade (`Aggregator._apply_evidence_weighting` använder
`dataclasses.replace` och rör endast `evidence_basis`-fältet). I-7c:s
`LOC → context.plats`-mappning sker dessutom i EntityLayer **uppströms**
aggregatorn och påverkar därför båda lägena lika. Konsekvensen är att
jämförelsen `legacy` mot `cross_validating` isolerar **enbart**
transparens-bidraget; den mätbara precisions-/recall-effekten ligger mot
iteration-2-baslinjen och syns lika i båda lägena. Detta är inte en
mätbegränsning — det är vad designcykel 3 faktiskt levererade och redovisas
sanningsenligt.

Hypoteserna (ordagrant från issuespecifikationen):

> **H1 (huvudhypotes):** Post-I-7c-koden (oavsett aggregator-mode, eftersom
> mappnings-fixen verkar uppströms) ger högre totalprecision än iteration
> 2-baslinjen (64,00 procent) utan att totalrecallen sjunker under iteration
> 2-baslinjen (89,27 procent).
> Falsifieringsvillkor: H1 falsifieras om totalrecall < 89,27 procent i
> någondera mode; H1 falsifieras om totalprecision ≤ 64,00 procent i någondera
> mode; H1 infrias om totalprecision > 64,00 procent OCH totalrecall ≥ 89,27
> procent i båda modes; H1 partiellt infrias om precision går upp men recall är
> marginellt under baslinjen (inom 1 procentenhet) — redovisas explicit.

> **H2 (artikel 9-skydd, sekundär):** Artikel 9-recall i båda modes är minst
> lika hög som iteration 2-baslinjen för respektive `article9.*`-underkategori.
> Falsifieras om recall för någon `article9.*`-underkategori är lägre än
> iteration 2-baslinjen för samma underkategori.

> **H3 (transparens, ny):** I `cross_validating`-mode taggas en mätbar andel
> av `context.kombination`-fynd som `high_confidence_no_support`. Andelen
> kvantifieras explicit och redovisas som underlag till framtida
> tröskelkalibrering. H3 är deskriptiv, inte falsifierbar i samma mening som
> H1/H2; den infrias om mätningen ger ett konkret tal.

### 8.2 Experimentell setup

Mätningen kördes med en *detect-once, aggregate-twice*-strategi i en separat
offline-harness (`scripts/run_i7d_baseline.py`, ingen ändring i
`gdpr_classifier/` eller `evaluation/`). De fyra lagren kördes **en gång per
text** och den identiska fyndlistan matades genom två aggregator-instanser. Det
gör mode-jämförelsen exakt kontrollerad eftersom `aggregate()` aldrig muterar
sin input (`Finding` är frozen, evidence-weighting använder
`dataclasses.replace`, containment/dedup returnerar nya listor) och halverar
LLM-tiden (159 i stället för 318 textgenomgångar).

Konstant mellan de två aggregator-körningarna:

| Variabel | Värde |
|---|---|
| Testkorpus | 159 texter (80 iteration-1 + 52 artikel-9 + 27 kombination)¹ |
| LLM-modell | `qwen2.5:7b-instruct` (samma som iteration 2–3) |
| Temperatur | 0,0 (hårdkodad i `ollama_provider.py`, inget seed) |
| Trösklar | `medium_threshold=0.7`, `high_confidence_bypass=0.85`, `min_evidence_count=2` (Beslut 20/51) |
| Promptversioner | Article9Layer v5, CombinationLayer v5 |
| Fyndlista | LLM-anrop en gång per text, samma lista till båda aggregatorerna |

¹ **Korpuskompositionskorrigering (I-7f).** I-7d:s ursprungliga text angav
"84 iteration-1 + 36 artikel-9 + 39 kombination" — en transkriptionsmiss
(summan 159 var korrekt). Den faktiska kompositionen, verifierad mot
datasetfilerna (`tests/data/iteration_1/test_dataset.json` = 80,
`tests/data/iteration_2/article9_dataset.json` = 52,
`tests/data/iteration_2/combination_dataset.json` = 27) och bekräftad av
harnessens egen `load_dataset` samt snapshot-metadata för **både** pre- och
post-I-7e-körningen, är **80 + 52 + 27 = 159**. Korrigeringen påverkar inga
mätvärden (korpusen var hela tiden densamma; endast textbeskrivningen var fel).

Varierat: enbart `cross_validation_mode` (`"legacy"` respektive
`"cross_validating"`).

> **Post-I-7e-omkörning (I-7f).** Den uppdaterade körningen använder exakt samma
> harness (`scripts/run_i7d_baseline.py`, orörd sedan I-7d), samma korpus
> (harnessens utskrift för denna körning: 159 texter = 80 iteration-1 + 52
> artikel-9 + 27 kombination), samma modell, trösklar och promptversioner. Den
> **enda** kodskillnaden mot pre-I-7e är I-7e:s mode-gateade
> `deduplicated_sources`-tillägg i `_count_structural_support`
> (`cross_validating` enbart). `legacy`-vägen är därför oförändrad och förväntas
> ge byte-identiskt utfall — vilket verifieras explicit i 8.4.

Validitetsbegränsning: residual icke-determinism kvarstår **endast** mot
iteration-2-baslinjen (`qwen2.5:7b` är inte seed-pinnat, och
iteration-2-reproduktionen kördes med CombinationLayer v4 medan I-7d använder
v5). Mellan `legacy` och `cross_validating` finns ingen residual
icke-determinism alls — samma fyndlista används. Se 8.7.

### 8.3 Resultat

#### 8.3.1 Total-jämförelse

| Konfiguration | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| Iteration-2-baslinje (#80) | 208 | 117 | 25 | 64,00 % | 89,27 % | 74,55 % |
| I-7d `legacy` (pre-I-7e) | 212 | 70 | 21 | 75,18 % | 90,99 % | 82,33 % |
| I-7d `cross_validating` (pre-I-7e) | 212 | 70 | 21 | 75,18 % | 90,99 % | 82,33 % |
| **I-7f `legacy` (post-I-7e)** | 212 | 70 | 21 | 75,18 % | 90,99 % | 82,33 % |
| **I-7f `cross_validating` (post-I-7e)** | 212 | 70 | 21 | 75,18 % | 90,99 % | 82,33 % |

`legacy` och `cross_validating` är **byte-identiska** på alla mätvärden (0
sanity-avvikelser över 159 texter, se 8.4). Förändring mot
iteration-2-baslinjen, identisk i båda lägena: TP +4, FP −47, FN −4, precision
**+11,18 procentenheter**, recall **+1,72 procentenheter**, F1 **+7,78
procentenheter**. Hela den mätbara förbättringen ligger alltså mot iteration 2
och syns lika i båda lägena — den är I-7c-mappningens effekt, inte
`cross_validating`-modes.

**Post-I-7e (I-7f).** Konfusionsmatrisen är **oförändrad** mot pre-I-7e i båda
lägena (TP/FP/FN = 212/70/21; P/R/F1 = 75,18 %/90,99 %/82,33 %), och
`legacy` ≡ `cross_validating` kvarstår (0/159 sanity-avvikelser i omkörningen).
I-7e:s effekt är alltså **inte** en precisions- eller recall-förändring utan
**enbart** en omfördelning av `evidence_basis`-taggar inom
`cross_validating`-läget (8.3.4) — exakt det transparens-scope §9.6.5/I-7e
föreskriver. Sanity-kontrollen post-I-7e legacy mot pre-I-7e legacy är
byte-identisk i `report.total`, `per_category`, `per_layer` och
`per_dimension` (endast `metadata.generated_at`/`git_commit` skiljer sig), vilket
verifierar I-7e:s mode-gate på korpusskala (8.4).

#### 8.3.2 Per-kategori (iteration 2 → I-7d, identiskt mellan modes)

Kategorier med förändrade tal mot iteration 2:

| Kategori | it2 TP/FP/FN | it2 P / R | I-7d TP/FP/FN | I-7d P / R |
|---|---|---|---|---|
| `article4.adress` | 14 / 22 / 1 | 38,89 % / 93,33 % | 14 / 0 / 1 | **100,00 %** / 93,33 % |
| `context.plats` | 12 / 15 / 2 | 44,44 % / 85,71 % | 14 / 10 / 0 | 58,33 % / **100,00 %** |
| `context.organisation` | 23 / 41 / 4 | 35,94 % / 85,19 % | 23 / 19 / 4 | 54,76 % / 85,19 % |
| `context.yrke` | 16 / 23 / 6 | 41,03 % / 72,73 % | 16 / 20 / 6 | 44,44 % / 72,73 % |
| `context.kombination` | 7 / 6 / 2 | 53,85 % / 77,78 % | 9 / 11 / 0 | 45,00 % / 100,00 % |

Den enskilt största effekten är `article4.adress`: 22 falska positiva försvinner
helt (FP 22 → 0) medan recall är oförändrad (93,33 %). Detta är exakt I-7c:s
mekanism — EntityLayer felklassade tidigare SpaCy-`LOC` som `article4.adress`
och genererade systematiska FP; efter ommappningen till `context.plats`
upphör de. `context.plats` får i sin tur recall 100 % (FN 2 → 0). De återstående
kategorierna är **byte-identiska** mot iteration 2:

- `article4.namn` 32/3/1, `article4.iban` 10/0/1; `article4.betalkort`,
  `article4.email`, `article4.personnummer`, `article4.telefonnummer` samtliga
  100 % precision och recall, oförändrade.
- Samtliga `article9.*`-underkategorier oförändrade (se 8.4, H2).

#### 8.3.3 Per-lager (iteration 2 → I-7d, identiskt mellan modes)

| Lager | it2 TP/FP | it2 Precision | I-7d TP/FP | I-7d Precision |
|---|---|---|---|---|
| `pattern` | 68 / 0 | 100,00 % | 68 / 0 | 100,00 % |
| `entity` | 49 / 46 | 51,58 % | 45 / 14 | **76,27 %** |
| `article9` | 36 / 7 | 83,72 % | 36 / 7 | 83,72 % |
| `context` | 55 / 64 | 46,22 % | 63 / 49 | 56,25 % |

`entity`-lagrets precision stiger kraftigt (51,58 % → 76,27 %): FP faller 46 →
14 när `LOC`-fynden inte längre felklassas som `article4.adress`. `pattern` och
`article9` är oförändrade. `context`-lagret förbättras (fler TP, färre FP),
delvis I-7c, delvis CombinationLayer v4 → v5 och LLM-variation (se 8.7).

#### 8.3.4 Per-`evidence_basis` (`cross_validating`) — H3:s data, pre-I-7e mot post-I-7e

Endast `context.kombination` kan bära icke-default `evidence_basis`
(`_apply_evidence_weighting` lämnar R1–R5/R7 vid `no_support_required`).
Detta är I-7f:s kärnredovisning: pre-I-7e (I-7d, commit `e6ab2f8`) och post-I-7e
(I-7f, commit `2d6c302`) i samma tabeller så att I-7e-deltat är direkt synligt.
Fördelning över **samtliga** 282 predikterade fynd (212 TP + 70 FP — oförändrat
totalantal):

| `evidence_basis` | pre TP | pre FP | pre Tot | post TP | post FP | post Tot | Δ Tot |
|---|---|---|---|---|---|---|---|
| `structural_support` | 0 | 1 | 1 | 5 | 2 | 7 | **+6** |
| `high_confidence_no_support` | 9 | 10 | 19 | 4 | 9 | 13 | **−6** |
| `no_support_required` | 203 | 59 | 262 | 203 | 59 | 262 | 0 |

Restringerat till `context.kombination` (H3:s nämnare, 20 fynd = 9 TP + 11 FP
**i båda körningarna** — samma fynd, omtaggade):

| `evidence_basis` | pre Tot | pre Andel | post Tot | post Andel | Δ Andel |
|---|---|---|---|---|---|
| `structural_support` | 1 | **5,0 %** | 7 | **35,0 %** | **+30,0 pe** |
| `high_confidence_no_support` | 19 | **95,0 %** | 13 | **65,0 %** | **−30,0 pe** |
| `no_support_required` | 0 | 0,0 % | 0 | 0,0 % | 0,0 pe |

Bucket-kvalitet (TP-vs-FP), pre → post:

- `structural_support`: 0 TP / 1 FP (precision 0 %) → **5 TP / 2 FP** (precision
  **71,4 %**). De fynd I-7e flyttar in i strukturellt stöd är till **5/7
  sanna**, mot pre-I-7e:s enda fynd som var en FP.
- `high_confidence_no_support` (Beslut 21 fail-safe-bypass): 9 TP / 10 FP
  (FP-andel **52,6 %**) → **4 TP / 9 FP** (FP-andel **69,2 %**). Bypass-bucketen
  krymper med 6 fynd; de 5 sanna som lämnar den får nu *redovisad* strukturell
  evidens i stället för att vila på fail-safe-bypassen.

Konkret rörelse: **6 `context.kombination`-fynd flyttade
`high_confidence_no_support` → `structural_support`** efter I-7e (5 TP + 1 FP).
Totalantalet `context.kombination`-fynd (20 = 9 TP + 11 FP) och hela
konfusionsmatrisen (8.3.1) är oförändrade — I-7e omtaggar evidensgrunden, den
ändrar inte vilka fynd som finns eller hur de klassificeras.

### 8.4 Hypotesutvärdering

**Förkontroll — mode-paritet.** Sanity-asserten (per text: identiska
`identifiability`, `data_class`, `sensitivity` mellan lägena) fallerade i **0
av 159** texter. `legacy` och `cross_validating` gav alltså byte-identiska
klassifikationsutfall, exakt som arkitekturen föreskriver (I-7b:s
`test_legacy_mode_unchanged` bekräftas empiriskt). All hypotesprövning av H1/H2
sker därför mot iteration-2-baslinjen, inte mot mode-skillnaden.

> **Post-I-7e (I-7f).** Omkörningen ger **0/159** sanity-avvikelser igen, trots
> att `cross_validating` nu konsulterar `deduplicated_sources` i Mekanism 3.
> Dessutom är post-I-7e `legacy`-snapshotten byte-identisk med pre-I-7e
> `legacy`-snapshotten i `report.total`, `per_category`, `per_layer` och
> `per_dimension` (`identifiability` none/indirect/direct = 84/16/59 i båda;
> endast `metadata.generated_at`/`git_commit` skiljer sig). Detta är den
> empiriska verifikationen av I-7e:s **mode-gate** på korpusskala: legacy-vägen
> är bevisat oförändrad, och de extra strukturella stöd som
> `deduplicated_sources` återupptäcker i `cross_validating` ändrade **inget**
> dimensionsutfall — `_has_validated_kombination`/`identifiability` rör sig
> inte, omtaggningen sker enbart i `_apply_evidence_weighting`
> (transparenslagret). H1/H2 prövas därför fortsatt mot iteration-2-baslinjen
> med oförändrade post-I-7e-tal.

**H1.** Redovisas mot iteration 2 med två recall-siffror enligt
falsifieringsmatrisen:

- **A. Rå totalrecall:** TP / (TP + FN) = 212 / (212 + 21) = **90,99 %**.
- **Mätinstrument-FN:** identifierades konkret som förväntade
  `article4.adress`-etiketter som blev FN och vars span överlappas av ett
  predikterat `entity.spacy_LOC`-fynd. Antalet är **0**. Det förväntade
  mätinstrumentskiftet (≈12 nakna städer som facit annoterar `article4.adress`
  skulle bli FN efter I-7c) materialiserades **inte**, eftersom matcher-aliaset
  `{ADRESS, PLATS}` (Beslut 45) absorberar kategoriskiftet på utvärderingssidan
  och låter ett `context.plats`-fynd matcha en `article4.adress`-etikett.
- **B. Justerad totalrecall:** TP / (TP + FN − 0) = 212 / 233 = **90,99 %**,
  identisk med rå recall (ingen justering behövs när mätinstrument-FN = 0).
- **Precision:** 75,18 % > 64,00 % i båda lägena.

Både rå och justerad recall ≥ 89,27 % **och** precision > 64,00 % →
**H1 är infriad** (matrisens rad "både rå och justerad recall ≥ 89,27 % → H1
infriad"). Differensen mellan rå och justerad recall är noll; tolkningen är att
regressionen från mätinstrumentskiftet uteblev därför att aliaset fortfarande
neutraliserar den (en validitetspunkt, 8.7) — inte att systembeteendet
försämrades.

**H2.** Recall per `article9.*`-underkategori, I-7d mot iteration 2:

| Underkategori | it2 recall | I-7d recall | Utfall |
|---|---|---|---|
| `article9.biometrisk_data` | 100,00 % | 100,00 % | = |
| `article9.fackmedlemskap` | 83,33 % | 83,33 % | = |
| `article9.genetisk_data` | 71,43 % | 71,43 % | = |
| `article9.halsodata` | 71,43 % | 71,43 % | = |
| `article9.politisk_asikt` | 100,00 % | 100,00 % | = |
| `article9.religios_overtygelse` | 83,33 % | 83,33 % | = |
| `article9.sexuell_laggning` | 66,67 % | 66,67 % | = |
| `article9.etniskt_ursprung` | — | — | N/A* |

\*`article9.etniskt_ursprung` saknar förväntade fynd i korpusen (TP = FN = 0) i
både iteration 2 och I-7d; recall är odefinierad i båda och utgör ingen
regression. Ingen underkategori har lägre recall än iteration 2 →
**H2 är infriad**. (Att tabellen är identisk är väntat: Article9Layer kördes
med samma promptversion v5 i båda mätningarna och påverkas inte av
I-7c-mappningen.)

**H3 (pre-I-7e, I-7d).** Av de 20 predikterade `context.kombination`-fynden
taggades **95,0 %** (19/20) som `high_confidence_no_support`, **5,0 %** (1/20)
som `structural_support` och **0 %** som `no_support_required`. H3 var därmed
infriad deskriptivt med ett konkret tal. Tolkning vid I-7d: nästan inga
kombinationsfynd uppnådde generaliserad Mekanism 3-validering (≥ 2 överlappande
strukturella stödfynd) — endast 1 av 20. De övriga passerade via
hög-konfidens-bypassen (Beslut 21, GDPR artikel 25-fail-safe). Bland
bypass-fynden var precisionen låg (9 TP mot 10 FP, FP-andel 52,6 %).

**H3 omformulerad — delta-analys (post-I-7e, I-7f).** I-7e visade att den höga
bypass-andelen i I-7d delvis var ett *mätartefakt*: `_count_structural_support`
såg inte stöd som `_deduplicate_same_category_overlap` hade tagit bort vid
same-category-källkollaps. När `cross_validating` efter I-7e även konsulterar
`deduplicated_sources` faller bypass-andelen för `context.kombination` från
**95,0 % → 65,0 %** (−30,0 procentenheter) och `structural_support` stiger
**5,0 % → 35,0 %** (+30,0 pe). Konkret: **6 av 20 kombinationsfynd** flyttade
`high_confidence_no_support` → `structural_support`, varav **5 sanna (TP) och 1
falskt (FP)**. `structural_support`-bucketens kvalitet vänder från 0 TP / 1 FP
(pre) till 5 TP / 2 FP (post, precision 71,4 %). Tolkning: en betydande del av
pusselbitseffekten *hade* genuint strukturellt stöd redan i I-7d — det var
osynligt för mätinstrumentet, inte frånvarande. Bypassen bär fortfarande
majoriteten (65 %) och är fortfarande den svagaste evidensgrunden, men inte
längre "i praktiken hela pusselbitseffekten". Detta är det uppdaterade,
kvantifierade underlaget för framtida tröskelkalibrering: andelen genuint
stödda kombinationsfynd är ~7× högre än I-7d-mätningen antydde (7 mot 1), och
de återstående 13 bypass-fynden (4 TP / 9 FP, FP-andel **69,2 %**) är den
bucket en framtida kalibrering bör rikta in sig på. H3 är därmed infriad även
post-I-7e, nu som en delta mellan två mätinstrumentversioner snarare än ett
enskilt tal.

**Sammanfattning (pre-I-7e):** H1 infriad, H2 infriad, H3 infriad (deskriptiv).
`cross_validating`-modes bidrag är transparens (H3), inte precision —
precisionseffekten är I-7c-mappningen mätt mot iteration 2 och syns identiskt
i båda lägena.

**Sammanfattning (post-I-7e, I-7f):** H1 och H2 **oförändrat infriade**
(post-I-7e-talen är identiska med pre-I-7e: P 75,18 %, R 90,99 %, alla
`article9.*`-recall ≥ iteration 2). H3 **infriad i sin omformulerade
delta-form**: I-7e flyttar bypass-andelen 95,0 % → 65,0 % och avslöjar att
strukturellt stöd var underrapporterat i I-7d, inte frånvarande.
`cross_validating`-modes bidrag är fortfarande **transparens, inte precision**
(konfusionsmatrisen oförändrad, 0/159 sanity-avvikelser), men transparensen är
efter I-7e *mer rättvisande*: `structural_support` är nu meningsfullt nåbart
och bär 7 av 20 kombinationsfynd i stället för 1.

### 8.5 Isolerad Degerfors-verifikation

Två texter som **inte** finns i datasetet eller facit kördes (detect en gång
per text, aggregering med båda aggregatorerna — fyra körningar):

- `text_stockholm` = "En 25-åring med blått hår bor i Stockholm."
- `text_degerfors` = "En 25-åring med blått hår bor i Degerfors."

| Text | Mode | Findings | identifiability / data_class / sensitivity | weakest_evidence_basis |
|---|---|---|---|---|
| Stockholm | `legacy` | `context.plats` "Stockholm" [32:41], `entity.spacy_LOC`, conf 0,80, `no_support_required` | none / none / none | None |
| Stockholm | `cross_validating` | `context.plats` "Stockholm" [32:41], `entity.spacy_LOC`, conf 0,80, `no_support_required` | none / none / none | None |
| Degerfors | `legacy` | `context.plats` "Degerfors" [32:41], `entity.spacy_LOC`, conf 0,80, `no_support_required` | none / none / none | None |
| Degerfors | `cross_validating` | `context.plats` "Degerfors" [32:41], `entity.spacy_LOC`, conf 0,80, `no_support_required` | none / none / none | None |

**Pedagogisk kontrastanalys.** Tre observationer:

1. **I-7c verifierad isolerat.** I båda texterna och båda lägena mappas
   ortnamnet till `context.plats` med source `entity.spacy_LOC` — aldrig
   `article4.adress`. Source-taggen är bevarad så att generaliserad Mekanism 3
   fortsatt kan räkna `LOC` som strukturellt stöd (§9.6.7).
2. **Mode-paritet verifierad isolerat.** `legacy` och `cross_validating` är
   identiska rad för rad, vilket speglar 8.4:s 0 sanity-avvikelser.
3. **Kontrasten neutraliserades av en uppströms-orsak.** CombinationLayer
   producerade **inget** `context.kombination`-fynd för någondera texten —
   varken den lilla orten Degerfors (i princip mer identifierande) eller
   storstaden Stockholm. Pusselbitskedjan "25-åring + blått hår + ort" plockades
   inte upp av den LLM-drivna Lager 4. Därför exercerades aldrig
   `evidence_basis`-maskineriet i detta isolerade fall, och båda texter slutar i
   `identifiability=none`. Detta avviker från §9.6.7:s tänkta Degerfors/Stockholm-
   kontrast men är ett ärligt utfall: kontrasten förutsätter att Lager 4 först
   genererar ett kombinationsfynd, vilket inte skedde för dessa exakta meningar
   (jämför 8.3.4 där bypass bär nästan all kombinationsdetektion — ett
   konfidensberoende beteende som inte triggades här).

**Post-I-7e-omkörning (I-7f).** Den isolerade verifikationen kördes om på
post-I-7e-koden. Utfallet är **byte-identiskt** med pre-I-7e: båda texterna, i
båda lägena, ger ett enda `context.plats`-fynd ("Stockholm"/"Degerfors"
[32:41], source `entity.spacy_LOC`, conf 0,80, `evidence_basis =
no_support_required`), `identifiability/data_class/sensitivity = none/none/none`,
`weakest_evidence_basis = None`.

| Text | Mode | Findings | identifiability / data_class / sensitivity | weakest_evidence_basis |
|---|---|---|---|---|
| Stockholm | `legacy` (post-I-7e) | `context.plats` "Stockholm" [32:41], `entity.spacy_LOC`, conf 0,80, `no_support_required` | none / none / none | None |
| Stockholm | `cross_validating` (post-I-7e) | `context.plats` "Stockholm" [32:41], `entity.spacy_LOC`, conf 0,80, `no_support_required` | none / none / none | None |
| Degerfors | `legacy` (post-I-7e) | `context.plats` "Degerfors" [32:41], `entity.spacy_LOC`, conf 0,80, `no_support_required` | none / none / none | None |
| Degerfors | `cross_validating` (post-I-7e) | `context.plats` "Degerfors" [32:41], `entity.spacy_LOC`, conf 0,80, `no_support_required` | none / none / none | None |

**Får Degerfors `structural_support` efter I-7e? Nej — och det är det väntade
utfallet.** I-7e:s `deduplicated_sources`-tillägg aktiveras endast när det finns
ett `context.kombination`-fynd vars same-category-stöd dödats av
`_deduplicate_same_category_overlap`. Här genererar Lager 4 **inget**
kombinationsfynd alls (samma uppströms-orsak som pre-I-7e, punkt 3 ovan), så
I-7e:s mekanism exercerades aldrig i detta isolerade par. Den isolerade
verifikationen bekräftar därför fortsatt I-7c och mode-paritet men kan
**konstruktionsmässigt inte** demonstrera I-7e — I-7e:s effekt är synlig på
**korpusskala** (8.3.4: 6 fynd flyttade till `structural_support`,
bypass 95,0 % → 65,0 %), inte i dessa två meningar. Detta är ett ärligt och
arkitektoniskt väntat negativt delresultat, inte en regression.

### 8.6 Tolkning och rekommendation

**Default-frågan (§9.6.4).** Eftersom `legacy` och `cross_validating` ger
byte-identiska klassifikationsutfall (0/159 avvikelser) är en default-flipp
inom I-7d:s mätscope en **transparens-fråga, inte en precisions-fråga**: den
ändrar vad systemet *redovisar* om sina kombinationsfynd
(`evidence_basis` / `weakest_evidence_basis`), inte vad det *klassificerar*.
Mätningen ger underlag men fattar inget beslut; rekommendationen lämnas till
manuell granskning och dokumenterat Loggbok-beslut.

**Default-frågan post-I-7e (I-7f).** Slutsatsen står kvar — flippen är fortsatt
en transparens-fråga (0/159 sanity-avvikelser, oförändrad konfusionsmatris) —
men `cross_validating`-modes *värde* är efter I-7e **större** än I-7d antydde.
I-7d gav bilden att transparenslagret nästan uteslutande producerar den
svagaste taggen (`high_confidence_no_support`, 95 %); post-I-7e visar att
`structural_support` är meningsfullt nåbart (35 %, 7/20 kombinationsfynd, 5
sanna). En framtida default-flipp skulle alltså ge en *mer informativ*
`weakest_evidence_basis` än I-7d:s siffror indikerade. Detta stärker underlaget
men ändrar inte beslutskaraktären: rekommendation och eventuell ombaslinje
lämnas alltjämt till manuell granskning och dokumenterat Loggbok-beslut
(I-7f fattar inget default-beslut — uttryckligen out of scope).

**Designprincip-kandidat för fas 4.** Arbetsströmmens arkitektoniska bidrag är
det generaliserade Mekanism 3-mönstret: en deklarativ beslutstabell (R1–R7)
plus en konfigurerbar evidensräknings-primitiv (`_count_structural_support`
med `valid_source_prefixes`) och `evidence_basis`-transparens. Mönstret är
öppet för utvidgning utan ändring i konsumerande lager och är en
designprincip-kandidat för formaliseringsarbetet i fas 4.

**Framtida arbete.** Om `cross_validating`-läget i en framtida iteration
faktiskt ska *gate-a* dimensioner (låta `evidence_basis` påverka
`identifiability`/`data_class`) är det ett separat designval. En sådan ändring
skulle **invalidera I-7b:s `test_legacy_mode_unchanged`** och kräva omarbetning
av legacy-paritetsantagandena samt en ny ombaslinje — en scope-implikation som
en framtida läsare måste förstå innan alternativet övervägs.

### 8.7 Begränsningar

- **LLM-determinism mot iteration-2-baslinjen.** `qwen2.5:7b-instruct` är inte
  seed-pinnat (endast `temperature=0.0`). Mode-jämförelsen `legacy` ↔
  `cross_validating` är exakt kontrollerad (samma fyndlista), men jämförelsen
  mot iteration 2 bär residual icke-determinism. Iteration-2-reproduktionen
  (#80) kördes dessutom med CombinationLayer **v4** medan I-7d använder **v5**;
  delar av `context.*`-förbättringen i 8.3.2/8.3.3 kan härröra ur
  promptversionsskillnaden snarare än enbart I-7c. Det rena I-7c-bidraget är
  tydligast i `article4.adress` (FP 22 → 0) och `entity`-lagrets precision.
- **Testkorpusstorlek.** 159 texter med dataset-bias enligt Pilán et al.
  (2022); absoluta tal (t.ex. 20 kombinationsfynd för H3) är små och ska tolkas
  som indikativa, inte som stabila populationsestimat.
- **Mätinstrumentskiftet neutraliserades.** De förväntade ≈12 nakna städerna
  blev **inte** FN (mätinstrument-FN = 0) eftersom matcher-aliaset
  `{ADRESS, PLATS}` (Beslut 45, §9.2.1) fortfarande är aktivt och absorberar
  kategoriskiftet. Per-kategori-jämförbarheten för `article4.adress`/
  `context.plats` mot iteration 2 påverkas av detta alias; en omprövning av
  aliaset är skjuten till efter I-7d och kvarstår som öppen punkt.
- **Sanity-avvikelser.** 0 av 159 — inga avvikelser att dokumentera enligt
  Justering 1; mode-paritetsantagandet håller empiriskt i denna körning.
- **Degerfors-kontrasten.** Den isolerade §9.6.7-kontrasten kunde inte
  observeras eftersom Lager 4 inte genererade något kombinationsfynd för de
  exakta meningarna (8.5); verifikationen bekräftar I-7c och mode-paritet men
  inte pusselbitseffektens evidensvägning i just det fallet.
- **I-7e är en post-I-7d arkitektonisk ändring (mätinstrumentrevision).**
  Pre-I-7e-talen i Del 8 mättes på commit `e6ab2f8` (I-7c); post-I-7e-talen på
  `2d6c302` (I-7e). I-7e ändrade inte klassificeringspolicyn utan
  *mätinstrumentet för evidensgrund*: `_count_structural_support` blev
  source-medveten i `cross_validating` via ett **mode-gateat**
  `deduplicated_sources`-tillägg. §9.6.5:s ursprungliga formulering "källdriven,
  mode-agnostisk" reviderades därför till "källdriven med mode-gateat
  `deduplicated_sources`-tillägg i `cross_validating`". Mode-gaten är ett
  medvetet bakåtkompatibilitetsavsteg (annars hade legacy-dimensioner ändrats
  via `_has_validated_kombination → _passes_mechanism_3`). Konsekvensen för
  tolkningen av Del 8 är att jämförelsen pre/post **inte** är två oberoende
  körningar av samma instrument utan en *instrumentförbättring*: 8.3.4:s delta
  mäter hur mycket strukturellt stöd som var underrapporterat i I-7d, inte en
  beteendeförändring i systemet. Containment-källkollaps
  (`_remove_context_covered_by_article9` m.fl.) propagerar fortfarande inte
  source och är en kvarstående, oadresserad parallell väg (ev. framtida I-7g).
  Motiveringen för mode-gate-avsteget och containment-punkten dokumenteras i
  **Loggboken iteration 3** (skrivs manuellt av användaren utanför agent-flödet).
