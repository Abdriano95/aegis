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

---

## Del 9: Probe #107 — modelljämförelse `qwen2.5:7b-instruct` mot `qwen3:14b` (checkpoint 6 + efteranalys)

> Källa: sessionspost 2026-05-17 i `docs/iteration_3_implementation.md` (operativt
> händelseförlopp). Denna Del 9 är SSOT för probe #107:s kvantitativa utfall och
> efteranalys; sessionsposten håller endast den kvalitativa "vad gjordes"-noteringen.

### 9.1 Bakgrund och frågeställning

Probe #107 (I-7) frågar om iteration 2:s prestandatak i Lager 3 (Article9Layer) och
Lager 4 (CombinationLayer) är **modellbundet** eller **uppgiftsbundet**. Checkpoint 1–5
(sessionsloggar, pre-I-7c/pre-I-7e-kod) jämförde mot `iteration_3_post_num_ctx_fix.json`
(F1 79,33 %). Checkpoint 6 gör om fullpipeline-mätningen **metodologiskt rent** på
post-I-7g-koden via samma instrument som producerade Del 8:s baslinje
(`scripts/run_i7d_baseline.py`, detect-once aggregate-twice), så att qwen3:14b ställs
mot den arkitektoniskt aktuella post-I-7g qwen2.5:7b-baslinjen i stället för ett
äldre, instrumentmässigt inkompatibelt tal.

Frågeställning: höjer ett modellbyte inom samma familj (qwen2.5:7b-instruct → qwen3:14b)
det globala talet, och var i pipelinen sitter rörelsen — och är ett observerat
precisionslyft **ärligt** eller ett mät-/aggregeringsfel?

### 9.2 Experimentell setup

| Variabel | Värde |
|---|---|
| Skript | `scripts/run_i7d_baseline.py` (detect-once aggregate-twice, `legacy` + `cross_validating`) |
| Testkorpus | 159 texter (80 iteration-1 + 52 artikel-9 + 27 kombination) |
| Baslinje | `qwen2.5:7b-instruct` — arkiv `i7d_*_qwen25_baseline.json`, git_commit `2d6c302` (= Del 8 §8.3.1 I-7f post-I-7e-raden, 212/70/21) |
| Probe-kandidat | `qwen3:14b` — `i7d_legacy.json` / `i7d_cross_validating.json`, git_commit `8144ae1` (post-I-7g-tip) |
| Provider | Ollama, `temperature=0.0`, `num_ctx=16384`, `think=False` |
| Promptversioner | Article9Layer v5, CombinationLayer v5 (oförändrade) |
| Trösklar | `medium_threshold=0.7`, `high_confidence_bypass=0.85`, `min_evidence_count=2` |
| Körtid qwen3 | 40 min 41 s (2026-05-16T22:30:07Z → 23:10:48Z), exit 0 |
| Sanity-avvikelser | **0 / 159** legacy↔cross_validating — **första qwen3-verifikationen** av mode-pariteten (I-7f:s 0/159 gällde qwen2.5) |

`legacy` och `cross_validating` är byte-identiska på konfusionsmatrisen för qwen3:14b
(som för qwen2.5 i Del 8); tabellerna nedan rapporterar därför `legacy`-talen, vilka
är identiska med `cross_validating`.

### 9.3 Resultat

#### 9.3.1 Total-jämförelse

| Konfiguration | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| `qwen2.5:7b-instruct` (post-I-7g baslinje; = Del 8 §8.3.1 I-7f post-I-7e) | 212 | 70 | 21 | 75,18 % | 90,99 % | 82,33 % |
| `qwen3:14b` (checkpoint 6) | 213 | 44 | 20 | 82,88 % | 91,42 % | 86,94 % |
| **Δ (qwen3 − qwen2.5)** | **+1** | **−26** | **−1** | **+7,70 pp** | **+0,43 pp** | **+4,61 pp** |

Lyftet är **precision-drivet** (FP 70 → 44) med nästan platt recall. qwen3:14b:s
precision (82,88 %) ligger över iteration 2:s V1-riktmärke på ≈80 %.

#### 9.3.2 Per-kategori (F1-rörelse ≥ 5 pp i någon riktning, `legacy`)

| Kategori | q2.5 TP/FP/FN | q2.5 F1 | q3 TP/FP/FN | q3 F1 | ΔF1 |
|---|---|---|---|---|---|
| context.yrke | 16/20/6 | 55,17 % | 18/6/4 | 78,26 % | +23,1 pp |
| article9.sexuell_laggning | 4/0/2 | 80,00 % | 6/0/0 | 100,00 % | +20,0 pp |
| article9.religios_overtygelse | 5/1/1 | 83,33 % | 6/0/0 | 100,00 % | +16,7 pp |
| article9.halsodata | 5/4/2 | 62,50 % | 4/0/3 | 72,73 % | +10,2 pp |
| context.kombination | 9/11/0 | 62,07 % | 8/6/1 | 69,57 % | +7,5 pp |
| context.organisation | 23/19/4 | 66,67 % | 21/9/6 | 73,68 % | +7,0 pp |
| article9.fackmedlemskap | 5/0/1 | 90,91 % | 6/2/0 | 85,71 % | −5,2 pp |
| article9.politisk_asikt | 6/0/0 | 100,00 % | 5/0/1 | 90,91 % | −9,1 pp |
| context.plats | 14/10/0 | 73,68 % | 14/17/0 | 62,22 % | −11,5 pp |

Övriga kategorier (article4.* m.fl.) rörde sig < 5 pp och utelämnas.

#### 9.3.3 Per-lager (`legacy`)

| Lager | q2.5 TP/FP | q2.5 F1 | q3 TP/FP | q3 F1 | ΔF1 |
|---|---|---|---|---|---|
| pattern | 68/0 | 100,00 % | 68/0 | 100,00 % | ±0,0 pp |
| article9 | 36/7 | 91,14 % | 38/3 | 96,20 % | +5,1 pp |
| context | 63/49 | 72,00 % | 68/30 | 81,93 % | +9,9 pp |
| entity | 45/14 | 86,54 % | 39/11 | 87,64 % | +1,1 pp |

> **Mätinstrumentbegränsning (per-lager).** `_build_report` i
> `scripts/run_i7d_baseline.py` nycklar lagermängden enbart ur
> `cm.layer_tp + cm.layer_fp` (ingen `layer_fn`). Per-lager-recall är därför
> strukturellt 100 % och per-lager-F1 är precisions-driven — talen är **inte**
> lagrens faktiska recall och får inte refereras som om de inkluderar lagrets
> missade fynd. Samma egenskap som checkpoint 5 flaggade för
> `build_demo_snapshot.py`. Kvarstår som öppen punkt (egen framtida issue: inkludera
> `layer_fn` i nyckelmängden); inget rört i checkpoint 6.

#### 9.3.4 Per-`evidence_basis` (`cross_validating`, endast `context.kombination`)

| evidence_basis | qwen2.5 TP/FP | qwen3 TP/FP |
|---|---|---|
| structural_support | 5/2 | 4/1 |
| high_confidence_no_support | 4/9 | 4/5 |
| no_support_required | 0/0 | 0/0 |

### 9.4 Efteranalys — verifiering att precisionslyftet är ärligt

Read-only-analys (slängbart script i OS-temp, inget repo-avtryck) som svarar på frågan
"är lyftet ärligt eller ett mätfel". Sammanfattat verdikt: **ärligt, inte ett mätfel.**

- **9.4.1 Aritmetisk sanity — grön.** I båda snapshots: Σ`per_category{tp,fp,fn}` =
  `report.total`, samples-rollup (`Σ false_positives`/`false_negatives`) = `total`,
  och omräknat P/R/F1 = lagrat (exakt). Idx-join snapshot↔dataset giltig för alla 159
  (samples-ordning = datasetordning). Precisionslyftet är inget aggregeringsfel.
- **9.4.2 FP-differens — netto −26 avstämt.** 47 försvunna och 21 nytillkomna FP
  (47 − 21 motsvarar ΔFP via nettoriktningen; |q3| − |q25| = 44 − 70 = −26). De
  försvunna är till överväldigande del äkta qwen2.5-överprediktioner (hallucinerad
  Lager 3/4-taggning, t.ex. "sökt för samma besvär"→`article9.halsodata`, "leddes
  av"→`context.yrke`) som qwen3 inte gör. De nytillkomna domineras av
  `context.plats`-överprediktion (→ §9.4.5).
- **9.4.3 TP-deltat (+1) härlett.** Via FN-mängddifferens (ground truth identisk
  mellan körningar): 10 q25-only FN (q3 vann TP) − 9 q3-only FN (q3 förlorade TP)
  = +1 = −ΔFN. Stämt av mot per_category-TP-rörelse (sexuell_laggning +2, yrke +2,
  religios +1, fackmedlemskap +1; halsodata −1, politisk_asikt −1, kombination −1,
  organisation −2 → netto +1).
- **9.4.4 De tre största F1-hoppen — textverifierade legitima.** `context.yrke`:
  qwen3 droppar uppenbart skräp ("leddes av", "Anställd", "lars.berg@privat.se"
  taggat som yrke). `article9.sexuell_laggning`: qwen3 fångar indirekta ledtrådar
  q25 missade som FN ("sin flickvän" idx125, "hennes fru Lisa" idx127).
  `article9.religios_overtygelse`: qwen3 droppar spurious FP "köpa böcker om
  religion" (idx88) och fångar FN "fira påsk i kyrkan" (idx121). Inga artefakter.
- **9.4.5 `context.plats`-regressionen — genuint qwen3-beteende, ej GT/matcher.**
  q25 14/10/0 → q3 14/17/0 (oförändrad TP & FN, +7 FP; 9 nya FP-texter). I samtliga
  9 saknas `article4.adress` i facit → `{ADRESS, PLATS}`-aliaset (Beslut 45) är
  uteslutet som orsak. FP:erna är genuina överprediktioner av vardagliga substantiv
  ("kyrkan", "biometriska låssystem", "sjukhuset", "industrivägen", "receptionen",
  "konferensen") eller felmärkning av icke-plats (idx86 "Unga Socialdemokrater"
  överlappar `article9.politisk_asikt`; idx140 "Skövde" överlappar
  `context.organisation`; idx73 "example.com" överlappar `article4.email`). Detta är
  probe-arbetets enda materiella regression och fördjupas med större modell.
- **9.4.6 Ground-truth-sanity — ren.** 0 snapshot-FN (över både q25 och q3) saknas
  verbatim i datasetets `expected_findings` → matcher/loader läser facit korrekt,
  alla FN är äkta facit-spans. 0 q3-FP överlappar en same/aliasad expected → ingen
  matcher-felscoring, inget FP är dolt TP. Lyftet är inte uppblåst av en scoring-bugg.

### 9.5 Tolkning (probe-svar, delvis)

- **Lager 3 (Article9Layer) är modellbundet.** Lagret F1 91,14 → 96,20 med
  recall-vinst på indirekta artikel 9-ledtrådar (`sexuell_laggning` 80,0 → 100,0,
  `religios_overtygelse` 83,3 → 100,0). Mönstret replikerar checkpoint 3 (pre-I-7c).
- **Lager 4 (CombinationLayer) lyfter måttligt.** `context.kombination`
  F1 62,07 → 69,57; ej fullt avgjort om primärt uppgifts- eller modellbundet.
- **Asymmetri-mönstret från checkpoint 3–5** (modellbunden precisionsvinst på
  Lager 3, blandad/uppgiftspräglad rörelse på Lager 4, materiell `context.plats`-
  regression) **replikeras på post-I-7g-koden**. Globalt thesis-rapporterbart:
  +4,61 pp total-F1 inom samma modellfamilj utan recall-kostnad.

### 9.6 Transparensnotering — I-7c-källomsourcing

En del av FP-churnen mellan qwen2.5 och qwen3 är *samma* fel-span omsourcad mellan
`entity.spacy_LOC` och `context.plats` snarare än ett genuint nytt/borttaget fel —
t.ex. idx88 "Södermalm" och idx126 "Mellanöstern" (`context.plats(src=entity.spacy_LOC)`
i q25 → `context.plats(src=context.plats)` i q3). Eftersom FP-nyckeln i efteranalysen
inkluderar `source` räknas dessa i både försvunna- och nytillkomna-listorna (§9.4.2);
nettoneutralt och påverkar **inte** netto −26 eller F1, men relevant om rapporten
senare gör en per-source-uppdelning.

### 9.7 Begränsningar

- **LLM-icke-determinism.** Endast `temperature=0.0`, inget seed. qwen2.5-baslinjen
  är en lagrad I-7f-körning (commit `2d6c302`), qwen3 en separat körning (`8144ae1`).
  Kodvägen är oförändrad mellan commits (endast #140:s defaultflipp, irrelevant då
  `run_i7d_baseline.py` instansierar båda lägena explicit), men residual
  modell-stokasticitet mellan sessioner kvarstår som confounder.
- **Per-lager-recall strukturellt 100 %** (§9.3.3-rutan) — per-lager-F1 ej lagrens
  faktiska recall.
- **Testkorpusstorlek.** 159 texter, dataset-bias enligt Pilán et al. (2022);
  absoluta tal små, indikativa snarare än stabila populationsestimat.
- **Probe-frågan endast delvis besvarad.** Lager 4:s modell-vs-uppgift inte avgjord;
  molnmodell-jämförelse (AnthropicProvider) är ett separat utforskande steg, inte
  klart. Probe-syntes till rapportens kapitel 6.5/6.7 sker när probe-arbetet är
  slutfört. Issue #107 förblir 🔄 Pågår.

## Del 10: Probe #107 - molnmodell-jämförelse `claude-opus-4-7` mot `qwen3:14b` (checkpoint 7 + efteranalys)

> Källa: sessionspost 2026-05-17c i `docs/iteration_3_implementation.md` (operativt
> händelseförlopp). Denna Del 10 är SSOT för probe #107 checkpoint 7:s kvantitativa
> utfall och efteranalys; sessionsposten håller endast den kvalitativa
> "vad gjordes"-noteringen. Del 10 fortsätter Del 9 (checkpoint 6, qwen3:14b mot
> qwen2.5) och använder Del 9 §9.3.1:s qwen3:14b-rad som baslinje.

### 10.1 Probe-frågan och bakgrund

V4 rekommenderade i iteration 2 att proben skulle inkludera en stor molnmodell via
API, för att avgöra om prestandataket i Lager 3 (Article9Layer) och Lager 4
(CombinationLayer) ligger i modellens kapacitet eller i uppgiftens inneboende
komplexitet. Checkpoint 1-6 jämförde endast lokala modeller (qwen2.5:7b-instruct,
qwen3:14b). Checkpoint 7 stänger den öppna punkten genom att ställa Claude Opus 4.7
mot den arkitektoniskt aktuella post-I-7g qwen3:14b-baslinjen (Del 9 §9.3.1) via
samma instrument som producerade Del 8 och Del 9.

Molnmodell-jämförelsen möjliggjordes av LLMProvider-abstraktionen (Beslut 17): en
AnthropicProvider implementerades samma dag enligt samma kontrakt som
OllamaProvider och GeminiProvider, vilket gör modellbytet till en
konfigurationsändring utan ingrepp i pipeline eller lager. Providern är sanktionerad
endast för utforskande bruk (ingen verklig persondata), inte produktion, per
Beslut 17.

En vägledande beslutsregel förregistrerades innan körningen: om Opus 4.7 ger total
precision > 85 % OCH recall > 90 % är det underlag för att överväga molnprovider
trots Beslut 17; annars dokumenteras utfallet som försök och qwen3:14b behålls.
Regeln är vägledande, inte bindande; slutligt produktionsval kräver Loggboks-beslut
(Beslut 60, se §10.6).

### 10.2 Korpus och konfiguration

| Variabel | Värde |
|---|---|
| Skript | `scripts/run_i7d_baseline.py` (detect-once aggregate-twice, `legacy` + `cross_validating`) |
| Testkorpus | 159 texter (80 iteration-1 + 52 artikel-9 + 27 kombination) |
| Baslinje | `qwen3:14b` - `i7d_legacy.json`, git_commit `8144ae1` (= Del 9 §9.3.1 checkpoint 6-raden, 213/44/20) |
| Probe-kandidat | `claude-opus-4-7` - `i7d_legacy_opus47.json` / `i7d_cross_validating_opus47.json`, git_commit `928f042` |
| Provider | AnthropicProvider (Anthropic API); `temperature` utelämnad (Opus 4.7 avvisar explicit `temperature` med HTTP 400), `max_tokens=4096`, `max_retries=3` |
| LLM-anrop | 318 (159 article9 + 159 combination; ingen gating, samtliga texter träffar båda LLM-lagren) |
| Promptversioner | Article9Layer v5, CombinationLayer v5 (oförändrade) |
| Trösklar | `medium_threshold=0.7`, `high_confidence_bypass=0.85`, `min_evidence_count=2` (Beslut 51) |
| Aggregator-mode | `cross_validating` default (Beslut 58) |
| Körtid | 12,1 min, exit 0, 0 st 429-retries, `llm_failures.count = 0` |
| Sanity-avvikelser | **1 / 159** legacy↔cross_validating (qwen3 hade 0/159; analys i §10.5) |

`legacy` och `cross_validating` är byte-identiska på konfusionsmatrisen för Opus 4.7
(som för qwen3 i Del 9 och qwen2.5 i Del 8); tabellerna nedan rapporterar därför
`legacy`-talen, vilka är identiska med `cross_validating`. Suffixet `_opus47` valdes
så att qwen3:14b-baslinjen (`i7d_legacy.json`) lämnades orörd.

### 10.3 Resultat

#### 10.3.1 Total-jämförelse

| Konfiguration | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| `qwen3:14b` (Del 9 checkpoint 6-baslinje) | 213 | 44 | 20 | 82,88 % | 91,42 % | 86,94 % |
| `claude-opus-4-7` (checkpoint 7) | 217 | 44 | 16 | 83,14 % | 93,13 % | 87,85 % |
| **Δ (opus − qwen3)** | **+4** | **0** | **−4** | **+0,26 pp** | **+1,71 pp** | **+0,91 pp** |

Opus 4.7 är strikt bättre på varje totalmått: fyra FN konverterade till TP utan en
enda ny FP. Rörelsen är recall-driven (FN 20 → 16) med nästan platt precision.
Den förregistrerade beslutsregeln är **inte uppfylld**: recall-tröskeln klaras
(93,13 % > 90 %) men precisionströskeln missas med 1,86 pp (83,14 % < 85 %).

#### 10.3.2 Per-lager (`legacy`)

| Lager | q3 TP/FP | q3 F1 | opus TP/FP | opus F1 | ΔF1 |
|---|---|---|---|---|---|
| pattern | 68/0 | 100,00 % | 68/0 | 100,00 % | ±0,0 pp |
| article9 | 38/3 | 96,20 % | 39/6 | 92,86 % | −3,3 pp |
| context | 68/30 | 81,93 % | 78/26 | 85,71 % | +3,8 pp |
| entity | 39/11 | 87,64 % | 32/12 | 84,21 % | −3,4 pp |

> **Mätinstrumentbegränsning (per-lager).** Som i Del 9 §9.3.3: `_build_report`
> nycklar lagermängden enbart ur `cm.layer_tp + cm.layer_fp` (ingen `layer_fn`).
> Per-lager-recall är därför strukturellt 100 % och per-lager-F1 är
> precisions-driven; talen är inte lagrens faktiska recall och får inte refereras
> som om de inkluderar lagrets missade fynd. Kvarstår som öppen punkt (egen
> framtida issue); inget rört i checkpoint 7.

Per-kategori-prosa: `context.plats` rör sig mest: q3 14/17/0 (P 45,16 %, F1 62,22 %)
→ opus 14/8/0 (P 63,64 %, F1 77,78 %), alltså FP 17 → 8 (−9, ΔF1 +15,6 pp) med
oförändrad TP och recall. Pusselbits-aggregatet `context.kombination` rör sig
marginellt åt fel håll: aggregat-FP 6 → 7, noll FN→TP-konverteringar och noll
TP→FN-regressioner (§10.4).

### 10.4 Efteranalys (textverifiering)

Read-only-analys i samma session (slängbart script i OS-temp, inget repo-avtryck)
som kartlade fynd-deltat per text och kategori mot facit. Sammanfattat verdikt:
nettolyftet är ärligt, men totalsiffrorna döljer churn och probe-rapportens
initiala per-lager-tolkning behöver nyanseras.

- **10.4.1 Aritmetisk sanity - grön.** I båda snapshots: Σ`per_category{tp,fp,fn}`
  = `report.total` och samples-rollup (`Σ false_positives`/`false_negatives`) =
  `total`. Idx-join snapshot↔snapshot giltig för alla 159 (samples-ordning =
  datasetordning, noll textmismatch). Nettolyftet är inget aggregeringsfel.
- **10.4.2 Per-text-deltakarta.** 128 texter identiska, 16 strikt bättre med Opus,
  9 strikt sämre, 6 churn (summa 159). Strikt-sämre-index: 25, 91, 92, 95, 100,
  119, 133, 136, 139. Churn-index: 51, 75, 77, 127, 142, 144. Opus är netto bättre
  (16 mot 9) men inte monotont; 31 texter ändrades, endast nettot favoriserar Opus.
- **10.4.3 FN→TP - 8 vunna, 4 förlorade, netto −4.** Åtta facit-fynd som Opus
  räddade, råtext-verifierade (predikterat span = facit-span): fyra organisationer
  (`Skatteverket` idx70, `Sigma IT` idx75, `Swedbank` idx76, `Teknik AB` idx77),
  tre hälsa-vardagsuttryck (`ont i knät` idx81, `reumatologbesök` idx82, `ont i
  magen` idx84) och ett yrke (`logistikstrategen` idx142). Fyra regressioner
  (TP→FN): `article9.fackmedlemskap` idx92, `article9.biometrisk_data` idx95
  (span-skifte), `context.yrke` idx139, `context.organisation` idx144. Probe-
  rapportens "+4 FN→TP" är ett netto av 8 vunna minus 4 förlorade, inte en monoton
  förbättring.
- **10.4.4 Nya Article9-FP - inga hallucinationer.** Fyra nya article9-FP, samtliga
  textförankrade (ordet finns i texten), bedömda mot `docs/annotation_guidelines.md`:
  idx100 `genetisk_data "hans genetiska profil"` är enligt guidens §4.6 äkta
  genetisk data (klient gjorde DNA-analys; facit underannoterar spannet); idx127
  `sexuell_laggning "ordförande i företagets HBTQ-nätverk"` är genuint känsligt
  (texten säger explicit "öppet homosexuell"; span-oenighet mot facit); idx95
  `biometrisk_data "logga in med ansiktet"` är en möjlig facit-inkonsistens mot
  guidens §4.7 (systembeskrivning av ansiktsigenkänning är enligt guiden inte
  biometrisk data, men facit annoterar ändå ett närliggande span); idx136
  `halsodata "bakterielinfektion"` är en defensibel bred läsning (generisk klinisk
  rapport utan namngiven person). Hypotesen att Opus tolkar v5-Article9-instruktionen
  bredare via hallucination stöds **inte**; precisionstappet är
  facit-granularitetsdrivet, inte en modellkvalitetsregression.
- **10.4.5 `context.plats`-reduktion - genuin.** Alla nio borttagna FP är
  spanlöst hos Opus (taggar dem inte alls): `example.com` idx74, `Unga
  Socialdemokrater` idx87, `kyrkan` idx88, `biometriska låssystem` idx96,
  `sjukhuset` idx99, `Skövde` idx141, `industrivägen` idx142, `receptionen`
  idx146, `konferensen` idx153. Per `combination_annotation_guidelines.md` §3.2/§8
  är inget av dessa formella platsnamn (`Skövde` ⊂ organisationsnamnet "Volvo Cars
  Skövde"). Detta är en äkta, guide-konsistent reduktion av qwen3:s övertaggning,
  inte ett mätinstrumentartefakt - den motsatta riktningen mot Del 9 §9.4.5:s
  qwen3-regression.
- **10.4.6 CombinationLayer-aggregatet regredierar svagt.** `context.kombination`:
  noll FN→TP, noll TP→FN, aggregat-FP 6 → 7. Hela "context"-lagrets +10 TP / −4 FP
  kommer från **individuella signaler** (organisations-recall: de fyra
  FN→TP-organisationerna i §10.4.3; plats-precision: −9 FP i §10.4.5; yrke), inte
  från pusselbits-bedömningen. De sju Opus-kombinations-FP bär självsäkra
  resonemang men hävdar `is_identifiable=true` där facit tillämpar den konservativa
  Regel D-defaulten (`combination_annotation_guidelines.md` §5.2).

### 10.5 Sanity-avvikelse

Text 137 ("Sjuksköterskan på intensivvården vid Sahlgrenska Universitetssjukhuset
i Göteborg ..."): `legacy` gav dimensions none/none/none, `cross_validating` gav
identifiability=indirect, data_class=none, sensitivity=low. Avvikelsen ligger i
aggregator-mode-skillnaden i identifiability-härledning, inte i fynd-listan: texten
har FP=2 (`context.organisation "Hallands sjukhus"`, `context.plats "Hallands"`)
och FN=0 **identiskt i båda modes**, vilket är varför `legacy` och
`cross_validating` är byte-identiska på totalerna. Mätvärdena räknas från fynd, ej
dimensioner, så avvikelsen påverkar inte precision/recall/F1. Antalet (1) ligger
under skriptets > 2-abortgräns. Verifierat ofarligt.

### 10.6 Slutsats och Beslut 60

qwen3:14b behålls som lokal produktionsmodell per Beslut 17. Probe #107:s
Opus-utfall är ett vetenskapligt bidrag (modellkapacitet kontra
uppgiftskomplexitet), inte underlag för produktionsbyte; den vägledande
beslutsregeln uppfylldes inte (precisionströskeln missad med 1,86 pp). Detta är
formaliserat som Beslut 60 i Loggboken iteration 3.

Tre nyanseringar av probe-rapportens initiala tolkning följer av textverifieringen.
Per-lager-asymmetrins "inversion" relativt checkpoint 1-5 är delvis ett
mätinstrumentfenomen snarare än ren modellkvalitet: Article9-lagrets precisionstapp
drivs av facit-granularitet och span-oenighet på genuint känsligt innehåll, inte av
hallucination, och den pusselbits-kombinatoriska logiken håller fortfarande som
uppgiftsbunden eftersom `context.kombination`-aggregatet inte förbättrades utan
regredierade svagt. Article9-precisionstappet är alltså facit-granularitetsdrivet,
inte hallucinationsdrivet. Och "+4 FN→TP" är ett netto av åtta vunna minus fyra
förlorade konverteringar, inte en monoton recall-förbättring.

En fjärde observation är central för probe-frågan: den lokala modellen är empiriskt
tillräcklig för uppgiften. qwen3:14b når 82,88 % precision, över V1:s 80
%-riktmärke från iteration 2, och marginalen till Claude Opus 4.7 är endast 0,26
procentenheter precision. Det indikerar att uppgiftens svårighet och
prompt-konfigurationen sätter prestandataket före modellkapaciteten - en starkare
modell flyttar inte taket nämnvärt på precisionssidan, vilket är probe #107:s
huvudsakliga svar för rapportens kapitel 6.

### 10.7 Öppna punkter

- **Facit-granskning.** [95] biometri (möjlig inkonsistens mot
  `annotation_guidelines.md` §4.7) och [100] genetik (möjlig underannotering mot
  §4.6) är åtgärdskandidater för framtida facit-revision. De förskjuter
  Article9-precisionsjämförelsen mätbart till Opus nackdel utan kvalitetsgrund.
  Out of scope för iteration 3 (påverkar båda modellerna symmetriskt och ändrar
  inte Beslut 60).
- **Modellfamiljsjämförelse.** Endast qwen-familjen och Claude Opus 4.7 är testade;
  gemma, llama och mistral är otestade. Bredare modellfamiljsjämförelse är
  framtida arbete i rapportens kapitel 6.10.
- **Probe-rapportintegration.** Probe-resultaten (checkpoint 1-7) är fullständigt
  dokumenterade i Del 9/10 ovan samt Beslut 59/60 (Loggbok iteration 3). Det som
  återstår är styckenivå-integration i rapporten (5.2 teknisk prestanda, 6.9
  begränsningar, 6.10 framtida forskning) — inte en separat syntes. Issue #107
  (I-7) är därmed ✅ Klar (2026-05-17); den tidigare formuleringen om "syntes till
  kapitel 6.5/6.7" var en felaktig framställning (6.7 = metodologiska bidrag, inte
  syntesplats för probe-resultat) som propagerade via en sessionslogg och utgår.
