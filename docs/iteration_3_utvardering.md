## Del 8: Dubbel baslinjemätning — `legacy` mot `cross_validating` (I-7d)

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
| Testkorpus | 159 texter (84 iteration-1 + 36 artikel-9 + 39 kombination) |
| LLM-modell | `qwen2.5:7b-instruct` (samma som iteration 2–3) |
| Temperatur | 0,0 (hårdkodad i `ollama_provider.py`, inget seed) |
| Trösklar | `medium_threshold=0.7`, `high_confidence_bypass=0.85`, `min_evidence_count=2` (Beslut 20/51) |
| Promptversioner | Article9Layer v5, CombinationLayer v5 |
| Fyndlista | LLM-anrop en gång per text, samma lista till båda aggregatorerna |

Varierat: enbart `cross_validation_mode` (`"legacy"` respektive
`"cross_validating"`).

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
| I-7d `legacy` | 212 | 70 | 21 | 75,18 % | 90,99 % | 82,33 % |
| I-7d `cross_validating` | 212 | 70 | 21 | 75,18 % | 90,99 % | 82,33 % |

`legacy` och `cross_validating` är **byte-identiska** på alla mätvärden (0
sanity-avvikelser över 159 texter, se 8.4). Förändring mot
iteration-2-baslinjen, identisk i båda lägena: TP +4, FP −47, FN −4, precision
**+11,18 procentenheter**, recall **+1,72 procentenheter**, F1 **+7,78
procentenheter**. Hela den mätbara förbättringen ligger alltså mot iteration 2
och syns lika i båda lägena — den är I-7c-mappningens effekt, inte
`cross_validating`-modes.

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

#### 8.3.4 Per-`evidence_basis` (`cross_validating`) — H3:s data

Endast `context.kombination` kan bära icke-default `evidence_basis`
(`_apply_evidence_weighting` lämnar R1–R5/R7 vid `no_support_required`).
Fördelning över **samtliga** 282 predikterade fynd (212 TP + 70 FP):

| `evidence_basis` | TP | FP | Totalt |
|---|---|---|---|
| `structural_support` | 0 | 1 | 1 |
| `high_confidence_no_support` | 9 | 10 | 19 |
| `no_support_required` | 203 | 59 | 262 |

Restringerat till `context.kombination` (H3:s nämnare, 20 fynd = 9 TP + 11 FP):

| `evidence_basis` | TP | FP | Totalt | Andel |
|---|---|---|---|---|
| `structural_support` | 0 | 1 | 1 | **5,0 %** |
| `high_confidence_no_support` | 9 | 10 | 19 | **95,0 %** |
| `no_support_required` | 0 | 0 | 0 | 0,0 % |

Explicit TP-vs-FP för `high_confidence_no_support`-bucketen (Beslut 21
fail-safe-bypass): 9 TP mot 10 FP — FP-andel **52,6 %**.

### 8.4 Hypotesutvärdering

**Förkontroll — mode-paritet.** Sanity-asserten (per text: identiska
`identifiability`, `data_class`, `sensitivity` mellan lägena) fallerade i **0
av 159** texter. `legacy` och `cross_validating` gav alltså byte-identiska
klassifikationsutfall, exakt som arkitekturen föreskriver (I-7b:s
`test_legacy_mode_unchanged` bekräftas empiriskt). All hypotesprövning av H1/H2
sker därför mot iteration-2-baslinjen, inte mot mode-skillnaden.

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

**H3.** Av de 20 predikterade `context.kombination`-fynden taggades **95,0 %**
(19/20) som `high_confidence_no_support`, **5,0 %** (1/20) som
`structural_support` och **0 %** som `no_support_required`. H3 är därmed
infriad deskriptivt med ett konkret tal. Tolkning: nästan inga
kombinationsfynd uppnår generaliserad Mekanism 3-validering (≥ 2 överlappande
strukturella stödfynd) — endast 1 av 20. De övriga passerar via
hög-konfidens-bypassen (Beslut 21, GDPR artikel 25-fail-safe). Bland
bypass-fynden är precisionen låg (9 TP mot 10 FP, FP-andel 52,6 %). Detta är
konkret, kvantifierat underlag för framtida tröskelkalibrering: bypassen bär i
praktiken hela pusselbitseffekten i denna korpus och är samtidigt den
svagaste evidensgrunden.

**Sammanfattning:** H1 infriad, H2 infriad, H3 infriad (deskriptiv).
`cross_validating`-modes bidrag är transparens (H3), inte precision —
precisionseffekten är I-7c-mappningen mätt mot iteration 2 och syns identiskt
i båda lägena.

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

### 8.6 Tolkning och rekommendation

**Default-frågan (§9.6.4).** Eftersom `legacy` och `cross_validating` ger
byte-identiska klassifikationsutfall (0/159 avvikelser) är en default-flipp
inom I-7d:s mätscope en **transparens-fråga, inte en precisions-fråga**: den
ändrar vad systemet *redovisar* om sina kombinationsfynd
(`evidence_basis` / `weakest_evidence_basis`), inte vad det *klassificerar*.
Mätningen ger underlag men fattar inget beslut; rekommendationen lämnas till
manuell granskning och dokumenterat Loggbok-beslut.

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
