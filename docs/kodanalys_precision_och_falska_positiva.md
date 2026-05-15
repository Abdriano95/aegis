# Kodanalys: varför precisionen är låg och var de falska positiva kommer ifrån

> Fristående teknisk genomgång av detektionspipelinen och utvärderingsramverket.
> Syftet är att svara på en enda fråga: är de svaga precisionssiffrorna ett
> kodfel, ett logikfel, en språkmodellsbegränsning eller något annat. Ingen kod
> har ändrats under analysen. Rapporten är medvetet skild från probe-arbetet och
> innehåller inget om modellskalning.

Författad av Claude Code (Opus 4.7) på begäran. Avsedd att läsas av hela
projektteamet. All data är hämtad direkt ur en persisterad utvärderingssnapshot
och korskörd mot ground truth, inte ur sekundära sammanställningar.

---

## 1. Sammanfattning för den som har bråttom

Pipelinen ger hög recall (cirka 92 procent) men låg precision (cirka 75 procent).
Frågan var om det beror på en bugg, på språkmodellen eller på prompten.

Svaret är tydligt: **det är varken aritmetiken, språkmodellen eller prompten som
är huvudproblemet.** Räkneformlerna är korrekta. Det LLM-drivna lagret som
detekterar känsliga uppgifter står för 3 av 73 falska positiva. Den låga
precisionen drivs i stället av tre saker, i fallande storleksordning:

1. **En deterministisk kategorikrock i NER-lagret.** SpaCy:s grova etikett `LOC`
   (alla geografiska namn) mappas rakt till den fina GDPR-kategorin
   `article4.adress`. Det ensamt skapar 33 av 73 falska positiva, helt utan att
   språkmodellen är inblandad.
2. **Utvärderingsmekanik.** Matchern matchar en förväntad etikett mot exakt ett
   fynd och saknar dedup mellan närliggande kategorier. Det förvandlar korrekta
   detektioner till falska positiva. 23 av 73 är av den sorten.
3. **Uttömmande detektion mot selektiv annotering.** Datasetet etiketterar bara
   de entiteter som är relevanta för respektive textscenario, medan NER och
   signal-extraktionen flaggar alla. Många av felen är detektioner som är
   korrekta i verkligheten men oetiketterade i just den texten.

De tre punkterna är överlappande linser på samma 73 falska positiva, inte
addender. Den exakta ömsesidigt uteslutande uppdelningen finns i avsnitt 5.2.

Av de 92 felen totalt (73 falska positiva, 19 falska negativa) är exakt 12
entydigt språkmodells- eller promptdrivna: 3 på precisionssidan (Article9Layers
falska positiva) och 9 på recall-sidan (6 missade artikel 9-etiketter, 3 missade
`context.yrke`). Det är drygt 13 procent. Det är ett golv, inte en uppskattning,
och härleds exakt i avsnitt 5.2. Resten har en icke-LLM-orsak: arkitektur,
mätinstrument och annoteringsmetodik.

En praktisk konsekvens värd att säga rakt ut: det mesta i den här rapporten är
inte buggar att rätta utan design- och mätval att förklara och motivera. Den
enda isolerade kodmiss som inte rör mätinstrumentet är ett missat IBAN-nummer
(avsnitt 5.1).

---

## 2. Vad som undersöktes och hur

Hela den utvärderingsrelevanta koden lästes igenom: matchern, metrikformlerna,
confusion-matrisen, aggregatorn, pipelinen och alla fyra detektionslager med
samtliga mönster-recognizers. Därefter dekomponerades varje enskild falsk positiv
och falsk negativ ur en persisterad snapshot, span för span, mot dataset­ets
ground truth (159 texter: 80 + 52 + 27). Varje fel klassificerades som antingen
ett genuint modellfel, en mätartefakt eller en annoteringseffekt.

Inga filer ändrades. Inga körningar gjordes om. Allt nedan är härlett ur kod och
befintlig snapshot.

---

## 3. Är räknemaskineriet korrekt? Ja.

### 3.1 Metrikformlerna

Standardformlerna i [evaluation/metrics.py](evaluation/metrics.py) är korrekta:

```python
def precision(tp, fp):
    denominator = tp + fp
    if denominator == 0:
        return 0.0
    return tp / denominator

def f1(tp, fp, fn):
    p = precision(tp, fp)
    r = recall(tp, fn)
    ...
    return 2 * (p * r) / denominator
```

Inget fel här. Den låga precisionen är inte ett räknefel. Den är ett genuint
högt antal falska positiva, och frågan är vad de består av.

### 3.2 Matchern: korrekt, men med två avgörande designval

[evaluation/matcher.py](evaluation/matcher.py) avgör vad som räknas som träff.
Logiken är korrekt implementerad, men två val formar siffrorna mer än något
annat.

**Val 1: exakt kategorilikhet, med ett enda undantag.**

```python
CATEGORY_ALIASES = frozenset({
    frozenset({Category.ADRESS, Category.PLATS}),
})
```

En förutsägelse räknas som träff bara om kategorin är exakt lika med den
förväntade (eller ingår i det enda alias-paret adress/plats). Hittar modellen
rätt textavsnitt men sätter en närliggande kategori, räknas det som **både** en
falsk positiv (förutsägelsen) **och** en falsk negativ (den förväntade
etiketten). Samma fel straffas två gånger, och det finns inget alias för
context-interna förväxlingar eller för artikel 9-syskonkategorier.

**Val 2: en förväntad etikett kan matchas av exakt ett fynd, det med högst
confidence vinner.**

```python
sorted_predictions = sorted(predicted, key=lambda p: p.confidence, reverse=True)
...
for p in sorted_predictions:
    ...
    if p.category == e.category and p.start < e.end and e.start < p.end:
        true_positives.append((p, e))
        matched_expected_ids.add(id(e))   # etiketten är nu upptagen
```

Om två lager korrekt detekterar samma verkliga entitet, blir bara det ena en
sann positiv. Det andra, som också är korrekt, blir en falsk positiv. Det här är
inte ett fel i koden, det är en konsekvens av en-till-en-matchningen, och det
visar sig vara en stor post (avsnitt 5).

Notera också att spann-överlappet är mycket generöst: `p.start < e.end and
e.start < p.end` betyder att en enda gemensam teckenposition räcker. Den låga
precisionen beror alltså **inte** på för sträng spann-matchning. Tvärtom.

### 3.3 Confusion-matrisen: korrekt, med en rapporteringsartefakt

[evaluation/confusion_matrix.py](evaluation/confusion_matrix.py) ackumulerar
korrekt på total- och kategorinivå. Men per-lager-attributionen har en strukturell
egenskap värd att känna till:

```python
# False negatives
for e in result.false_negatives:
    self.total_fn += 1
    self.category_fn[e.category] += 1
    # ingen rad som ökar self.layer_fn
```

Falska negativa attribueras aldrig till något lager (logiskt, en missad
detektion har inget producerande lager). Konsekvensen är att per-lager-recall
**alltid är 100 procent** och per-lager-F1 i praktiken är ett rent
precisionsmått. Det påverkar inte total precision eller recall, men per-lager-F1
får aldrig läsas som lagrets verkliga prestanda. Detta är en
rapporteringsartefakt att dokumentera, inte en bugg att rätta, och inte heller
rättbar i nuvarande form eftersom en falsk negativ saknar källa.

---

## 4. Den enskilt största orsaken: EntityLayer-mappningen

Detta är rapportens viktigaste avsnitt.

[gdpr_classifier/layers/entity/entity_layer.py](gdpr_classifier/layers/entity/entity_layer.py)
mappar SpaCy:s namnentitetstyper till GDPR-kategorier:

```python
self._label_map = {
    "PRS": (Category.NAMN,         "entity.spacy_PRS"),
    "LOC": (Category.ADRESS,       "entity.spacy_LOC"),   # <-- problemet
    "ORG": (Category.ORGANISATION, "entity.spacy_ORG"),
}
```

`LOC` i SpaCy:s svenska modell omfattar **alla** geografiska namn: städer,
länder, regioner, stadsdelar, landmärken. Koden mappar samtliga rakt till
`article4.adress`, som i GDPR-mening betyder en gatuadress till en fysisk person.

Beviset, span för span: hela 159-textkorpusen innehåller bara **15**
`article4.adress`-etiketter. Den analyserade snapshoten producerade **15 sanna
positiva plus 33 falska positiva** för den kategorin, och **alla 33 falska
positiva har `source = entity.spacy_LOC`.** Textavsnitten är nästan uteslutande
ortnamn, plus några avskalade gatunamnstokens utan husnummer:

> Stockholm, Malmö, Göteborg, Borås, Uppsala, Örebro, Linköping, Karlskrona,
> Trollhättan, Karlskoga, Sveavägen, Vasagatan, Södermalm, Rosengård,
> Mellanöstern, "Hallands", "Västra Götalandsregionens", och till och med det
> generiska ordet "kommun".

Inget av dem är en komplett gatuadress med husnummer. De är ortnamn (städer,
regioner, stadsdelar) eller avskalade gatunamnstokens som "Sveavägen" och
"Vasagatan" där SpaCy taggat enbart gatunamnet och husnumret fallit utanför
spannet. De numrerade formerna "Sveavägen 44" och "Vasagatan 12" är i stället
de äkta adress-etiketterna och behandlas i avsnitt 14. Det här är
deterministiskt, oberoende av språkmodell och oberoende av prompt: EntityLayer
rör aldrig en LLM.

### 4.1 Samma krock skapar också falska negativa

Felet träffar mätningen två gånger. När SpaCy taggar ett myndighets- eller
organisationsnamn som `LOC`, blir det `article4.adress` (en falsk positiv)
samtidigt som den förväntade `context.organisation`-etiketten missas (en falsk
negativ). Bredare uttryckt är detta
`LOC → adress`-spegelsidan: en `context.*`-etikett (organisation eller
kombination) missas för att SpaCy lade `article4.adress` på spannet. Det utgör
tre av de fyra kategoriförväxlings-falska-negativa i avsnitt 5.2; det fjärde är
ett `context.yrke` som modellen kallade `context.kombination`. Adress↔plats-
aliaset hjälper inte, eftersom sanningen här är `organisation`, inte `plats`.

Ett enda exempel räcker för att se det: i en text om ett kommunalt ärende blir
"Malmö", "kommun" och "Rosengård" tre adress-falskpositiva från `LOC`, medan
"Malmö kommun" blir en organisation-falsknegativ, allt ur samma mening.

### 4.2 Krocken läcker in i den tvådimensionella klassificeringen

Detta är en knock-on-effekt som är lätt att missa.
[gdpr_classifier/aggregator.py](gdpr_classifier/aggregator.py) bestämmer
identifierbarhet så här:

```python
has_article4 = any(f.category.value.startswith("article4.") for f in findings)
if has_article4:
    identifiability = Identifiability.DIRECT
```

Eftersom EntityLayer producerar `article4.adress` för varje ortnamn, får varje
text som bara nämner en stad identifierbarhet `DIRECT`. I snapshoten klassas 82
av 159 texter som `DIRECT`. Den exakta andelen spuriöst DIRECT går inte att
isolera ur snapshoten ensam, men mekanismen är strukturell: NER-bruset stannar
inte på spann-nivå, det propagerar in i den dimension som kommuniceras till
intressenten. Detta är värt att nämna i uppsatsen som en designkoppling, inte
som ett räknefel.

---

## 5. Felbudgeten: hur mycket är modell, mätning respektive annotering

Varje falsk positiv klassificerades mot ground truth i fyra ömsesidigt
uteslutande kategorier:

| Bucket | Antal | Andel | Vad det är |
|---|---:|---:|---|
| B: dubblett av redan räknad sann positiv | 23 | 32 % | Modellen hittade en *verklig etiketterad* entitet, men ett annat fynd hade redan tagit den. Ren mätartefakt. |
| D: genuint spurious | 36 | 49 % | Inget förväntat på spannet alls. |
| C: kategoriförväxling mot redan räknad etikett | 9 | 12 % | Spannet är verklig persondata, fel kategori, rätt redan räknad. |
| A: kategoriförväxling mot missad etikett | 5 | 7 % | Verklig persondata, syskonkategori, skulle bli sann positiv med bredare alias. |

**Bucket B (23 stycken) är inte modellfel.** Det är mestadels
adress↔plats-dubbletten: SpaCy säger `article4.adress` "Stockholm" och
CombinationLayer säger `context.plats` "Stockholm" om samma verkliga plats. En
blir sann positiv, dubbletten blir falsk positiv på grund av
en-till-en-matchningen. Modellen har alltså rätt två gånger och får poäng för en,
straff för en.

**Bucket D ser värst ut men är till stor del inte hallucination.** De faktiska
exemplen är icke-etiketterade men verkliga entiteter: personnamn som dyker upp
i löptext, ett universitet, ett fackförbund, yrkesord som "mekaniker" och
"ordförande", platser som "sjukhuset". Datasetet annoterar **selektivt** (bara
scenariorelevanta entiteter per text) medan NER och signal-extraktionen
detekterar **uttömmande**. Den krocken, inte modellsvaghet, står för merparten
av bucket D, och den är koncentrerad till exakt samma två lager som allt annat:
entity och combination.

Det renaste minimala exemplet i hela korpusen:

> **Text:** "Projektledare: Gunnar Strand. Ansvarig tekniker: Sofia Lund."
>
> **Utfall:** två falska positiva, `context.yrke` "Projektledare" och
> `context.yrke` "Ansvarig tekniker".

Modellen är faktiskt korrekt, båda *är* yrken, och får ändå två falska positiva
enbart för att den textens annotering inte etiketterar yrken i det scenariot.
Det här fallet bör ligga centralt i en metoddiskussion.

### 5.1 Falska negativa, samma mönster spegelvänt

Av 19 falska negativa är 4 kategoriförväxlingar (modellen flaggade spannet men
med fel kategori, parat med en falsk positiv) och 15 genuina missar. De genuina
missarna är semantiska randfall, inte systemfel:

- Vardagligt symtomspråk som "ont i knät", "ont i magen", "reumatologbesök" som
  inte fångas som `article9.halsodata`.
- Ett icke-nordiskt personnamn som SpaCy:s svenska modell inte känner igen
  (en täckningslucka i NER, inte i språkmodellen, och dessutom en rättviseaspekt
  värd att nämna).
- Ett IBAN-nummer som mönster-recognizern missade trots att lagret annars är
  100 procent. Sannolikt mellanslagsgrupperingen i numret. Detta är den enda
  isolerade kodmiss i hela analysen som inte rör mätinstrumentet.
- Generiska roll- och organisationsord ("anställd", "medarbetare") som
  signal-lagret är konservativt med.

De entydigt språkmodells- eller promptdrivna recall-missarna är de 6 missade
artikel 9-etiketterna (hälsodata 3, genetisk 2, politisk 1) och de 3 missade
`context.yrke`-etiketterna, tillsammans 9 av de 19 falska negativa.
Entydigheten följer av att `article9.*` enbart produceras av Article9Layer och
`context.yrke` enbart av CombinationLayer, så en miss där kan per konstruktion
inte ha en deterministisk icke-LLM-orsak.

### 5.2 Den konsoliderade felbudgeten

Felbudgeten redovisas i tre tabeller. Var och en är ömsesidigt uteslutande och
summerar exakt. De är tre linser på samma 73 falska positiva och 19 falska
negativa och får **inte** adderas tvärs över varandra. Källa: span-för-span-
dekomponeringen i avsnitt 5 och per-källa-uppdelningen i bilagan till avsnitt 10.

**De 73 falska positiva, per utvärderingsbucket (summa 73):**

| Bucket | Antal | Orsak |
|---|---:|---|
| B dubblett av redan räknad TP | 23 | Mätmekanik: en-till-en-matchning utan korskategori-dedup |
| D genuint spurious | 36 | Annoteringsmetodik: uttömmande detektion mot selektiv etikettering |
| C kategoriförväxling mot redan räknad etikett | 9 | Delvis äkta: spannet är persondata, fel kategori |
| A kategoriförväxling mot missad etikett | 5 | Delvis äkta: syskonkategori |

**Samma 73 falska positiva, per producerande källa (summa 73):**

| Källa | Antal | Språkmodell? |
|---|---:|:---:|
| entity (`spacy_LOC` 33, `spacy_ORG` 4, `spacy_PRS` 3) | 40 | Nej, SpaCy är LLM-fritt |
| context / CombinationLayer (`plats` 13, `yrke` 6, `kombination` 6, `organisation` 5) | 30 | Ja, LLM-lager |
| article9 / Article9Layer (`fackmedlemskap` 2, `biometrisk_data` 1) | 3 | Ja, LLM-lager |
| pattern | 0 | Nej |

**De 19 falska negativa (summa 19):**

| Typ | Antal | Orsak |
|---|---:|---|
| E kategoriförväxling: 3 `LOC → adress`-spegelsida + 1 `yrke` som modellen kallade `kombination` | 4 | NER-mappning (3) respektive brett kombinations-span (1) |
| F genuin miss, artikel 9 (hälsodata 3, genetisk 2, politisk 1) | 6 | LLM-/promptkonservatism |
| F genuin miss, `context.yrke` (generiska rollord) | 3 | LLM-/promptkonservatism |
| F genuin miss, `context.organisation` (täckningslucka) | 4 | NER och LLM missar samtidigt |
| F genuin miss, `article4.namn` (icke-nordiskt namn) | 1 | Deterministisk SpaCy-lucka |
| F genuin miss, `article4.iban` (mellanslagsgruppering) | 1 | Deterministisk recognizer-lucka |

**Kausal attribution.** Det enda som entydigt kan tillskrivas språkmodellen
eller prompten är de fel vars kategori saknar en icke-LLM-producent: de 3
article9-falska-positiva, de 6 missade artikel 9-etiketterna och de 3 missade
`context.yrke`-etiketterna, tillsammans **12 av 92** fel. `article9.*`
produceras enbart av Article9Layer och `context.yrke` enbart av
CombinationLayer, så ett fel där kan per konstruktion inte ha en deterministisk
orsak. Allt annat har en icke-LLM-orsak: den deterministiska `LOC →
adress`-mappningen, matcherns en-till-en-mekanik, annoteringsmetodiken, eller en
samtidig NER- och LLM-täckningslucka. De 33 `LOC → adress`-felen och deras tre
FN-spegelfall (av de fyra i bucket E) är samma designval sett från FP-
respektive FN-sidan; det fjärde bucket-E-felet är ett `context.yrke` som
CombinationLayers breda kombinations-span fångade som `context.kombination`.

---

## 6. Confidence: en konstant som avgör utfallet

Mönster-recognizers sätter hög confidence, men på olika grund. Personnummer,
IBAN och betalkort sätter 1.0 *därför att de checksummevalideras* (Luhn
respektive mod97), vilket gör matchningen nära binär. E-post sätter också 1.0
men enbart via regex utan checksumma, och telefon 0.9 likaså via regex utan
checksumma. Det är samma åtskillnad som avsnitt 13 vilar på. EntityLayer sätter
däremot en **hårdkodad konstant för allt**:

```python
findings.append(Finding(
    ...
    confidence=0.8,             # samma för PRS, LOC och ORG, oavsett NER-säkerhet
    source=source,
))
```

LLM-lagren returnerar en modellgenererad confidence som varierar. Matchern
sorterar på confidence fallande och låter det högsta fyndet ta den förväntade
etiketten.

Den intressanta kvantifieringen: i samtliga 23 fall i bucket B (dubblett av en
redan räknad sann positiv) är det förlorande fyndets confidence exakt 0.8, och
samtliga 23 kommer från entity-lagret. Med andra ord avgörs utgången i 100
procent av dubblett-förlusterna av en konstant, inte av en kalibrerad signal.
Värdet 0.8 förlorar systematiskt varje korskategori-kapplöpning mot ett
LLM-fynd vars modellreturnerade confidence råkar överstiga 0.8. Det är inte
fel i sak, men det betyder att en designkonstant, inte en sannolikhet, styr en
mätbar del av resultatet.

---

## 7. Skyddsmatrisen: vad aggregatorn fångar och inte

[gdpr_classifier/aggregator.py](gdpr_classifier/aggregator.py) gör tre saker
innan matchning: containment-regler, same-category-dedup och överlappsdetektion.
Skyddet är glest och medvetet riktat.

**Skyddade situationer:**

| Situation | Mekanism |
|---|---|
| Två fynd, samma `Category`, överlappande spann | `_deduplicate_same_category_overlap` behåller högst confidence |
| Telefonnummer som överlappar ett IBAN | `_remove_telefon_covered_by_iban` |
| `organisation`/`yrke` helt inuti ett `article9.*`-fynd | `_remove_context_covered_by_article9` |

**Oskyddade situationer (empiriskt dominanta):**

| Situation | Konsekvens |
|---|---|
| `article4.adress` mot `context.plats`, överlappande | Ej dedupad, bara matcher-aliasad, dubbletten blir FP (bucket B, 23 st) |
| `context.kombination` mot sina egna delsignaler (yrke/plats/organisation) | Det breda kombinations-spannet överlappar redan räknade signaler och blir FP (se kombinations-FP i avsnitt 5.2) |
| Artikel 9-syskon mot syskon (t.ex. hälsodata mot genetisk) | Ej skyddat |
| `organisation`/`yrke` som bara *delvis* överlappar ett `article9.*`-fynd | Regeln kräver fullständig inneslutning, partiella överlapp lever kvar |

Mönstret är konsekvent: skyddet täcker tre specifika fall och lämnar adress↔plats
och kombination-mot-signaler oskyddade, vilket är exakt de par som dominerar
felbudgeten.

---

## 8. Dimensionslogiken: korrekt, men kopplad

Härledningen av känslighetsnivå i `derive_sensitivity` är logiskt korrekt och
total. Alla nio celler i (identifierbarhet, dataklass)-tabellen verifierades mot
den dokumenterade härledningstabellen och stämmer:

| identifierbarhet \ dataklass | NONE | SPECIAL | CRIMINAL |
|---|---|---|---|
| NONE | NONE | LOW | LOW |
| INDIRECT | LOW | MEDIUM | MEDIUM |
| DIRECT | LOW | HIGH | HIGH |

`_determine_dimensions` följer sitt dokumenterade kontrakt. Den enda anmärkningen
är kopplingen från avsnitt 4.2: eftersom `DIRECT` triggar på vilket som helst
`article4.*`-fynd och EntityLayer producerar `article4.adress` för varje ortnamn,
ärver dimensionen NER-bruset. Vidare räknar Mekanism 3 (`_passes_mechanism_3`)
överlappande `entity.*`-fynd som "bevis" för en validerad kombination, så det
över-genererande NER-lagret kan i princip validera kombinationer på svaga
bevis. På den här korpusen är den vägen empiriskt liten (få texter blir
`INDIRECT`), men designkopplingen är reell och värd en mening i uppsatsen.

Slutsats: ingen logikbugg i dimensionslogiken. Den ärver däremot det redan
identifierade NER-problemet.

---

## 9. Latenta soliditetshål utan uppmätt effekt

Tre saker är värda att känna till men påverkar inte de aktuella siffrorna:

1. **`text.find` binder till första förekomsten.** De LLM-drivna lagren får inte
   teckenpositioner från modellen, de rekonstruerar dem med strängsökning i
   [article9_layer.py](gdpr_classifier/layers/article9/article9_layer.py) och
   [combination_layer.py](gdpr_classifier/layers/combination/combination_layer.py).
   Om spannsträngen förekommer flera gånger hamnar fyndet på fel ställe.
   Empiriskt: noll falska negativa i den här korpusen har ett flerförekomst-span
   i LLM-lagren. Reellt hål, noll uppmätt effekt här.
2. **Den rekonstruerade kombinations-spannvägen** i combination_layer kan
   syntetisera ett godtyckligt brett span (`min(start)..max(end)` av
   delsignalerna) när modellens span inte hittas. Strukturellt svagt, bidrar
   till kombination-förväxlingarna men är inte en räknebugg.
3. **Död kod.**
   [gdpr_classifier/layers/context/context_layer.py](gdpr_classifier/layers/context/context_layer.py)
   är en stub som returnerar `[]` och inte är inkopplad i den aktuella
   pipelinen (Article9Layer och CombinationLayer har ersatt den). Värt att
   städa eller dokumentera, ingen funktionell påverkan.

---

## 10. Slutsats och vad det betyder för uppsatsen

Koden är logiskt sund där det räknas. Metrikformlerna är korrekta, matchern och
confusion-matrisen gör vad de ska, dimensionslogiken är korrekt härledd. Den
enda isolerade kodmiss vi hittade är ett missat IBAN-nummer.

Den låga precisionen förklaras, i fallande ordning, av:

1. En deterministisk grov-till-fin-mappning i SpaCy-lagret (`LOC → adress`,
   `ORG → organisation`) som är helt oberoende av språkmodell och prompt.
2. Ett medvetet utvärderingsmekaniskt val (en-till-en-matchning utan
   korskategori-dedup) som gör korrekta detektioner till falska positiva.
3. En uttömmande-mot-selektiv annoteringskrock som inte är ett kodproblem alls.

Språkmodellen och prompten är den minst skyldiga delen. Det LLM-drivna artikel
9-lagret har cirka 93 procent precision och står för 3 av 73 falska positiva.
Entydigt LLM-/promptattribuerbara fel är 12 av 92, 3 falska positiva och 9
falska negativa, härlett exakt i avsnitt 5.2.
Den höga recallen och låga precisionen är dessutom delvis den uttalade
`recall > precision`-designens avsedda utfall: i ett GDPR-sammanhang är en
falsk negativ allvarligare än en falsk positiv, och systemet är trimmat
därefter.

**Rekommendation, inte åtgärd.** Det mesta här är design- och mätval att
förklara och motivera, inte buggar att jaga. En uppsats vinner mer på att
redovisa exakt *varför* precisionen ser ut som den gör, vilket den här rapporten
kvantifierar, än på att ändra kod sent i processen. Varje ändring i matchern,
aggregatorn eller NER-mappningen ändrar dessutom mätinstrumentet och gör tidigare
mätvärden ojämförbara, vilket i ett spårbarhetsdrivet metodupplägg kräver ett
dokumenterat beslut och omkörning av allt. Det enda som kan röras isolerat utan
att påverka mätinstrumentet är det missade IBAN-formatet.

### Bilaga: hur siffrorna hänger ihop

Per lager i den analyserade snapshoten: mönster 68/0 (100 procent precision),
entity 40/40 (cirka 50 procent), article9 (LLM) 38/3 (cirka 93 procent), context
(LLM) 68/30 (cirka 69 procent). Summan av falska positiva per källa stämmer
exakt mot per-kategori- och per-lager-aggregaten, vilket gör dekomponeringen i
avsnitt 5 tillförlitlig: entity 40, context 30, article9 3, mönster 0, totalt 73.

---

## 11. Proveniens: var beslutet kom ifrån

Spårat genom git-historik och projektets egna dokument. Slutsatsen är att
`LOC → article4.adress` aldrig var en bugg eller en kodolycka, utan en kedja av
tre öppet dokumenterade beslut. Ingen enskild person bär ansvar, och själva
spårbarheten är ett styrketecken för metodupplägget.

**Akt 1, designtidsförenkling (cirka 2026-04-17).** Mappningen specificerades i
SSOT [docs/arkitektur.md](docs/arkitektur.md) avsnitt 5 innan EntityLayer
implementerades (stub i commit `eb8e676`). Samma avsnitt märker `confidence =
0.8` som "ett medvetet iteration-1-val". Båda svagheterna är alltså
arkitekturbeslut, inte kod som glidit. Valet var rimligt i sitt sammanhang:
SpaCy:s svenska modell ger bara tre användbara etiketter (PRS, LOC, ORG),
ContextLayer var en avsiktlig stub i iteration 1 så det fanns ingenstans att
routa en plats, och `article4.adress` var den enda artikel 4-kategori en
plats kunde mappas till. Commit `57430c6` (2026-04-20) korrigerade PER till PRS,
vilket visar att etikettsemantiken granskades, men att `LOC` betyder *alla*
platser ifrågasattes inte.

**Akt 2, medveten symtomlindring (2026-05-04).** En formell rotorsaksanalys i
[docs/iteration_2_utvardering.md](docs/iteration_2_utvardering.md) Del 7
identifierade problemet exakt som "Rotorsak 1, kategori-krock article4.adress /
context.plats", med samma FP+FN-mekanism som denna rapport återupptäckte
oberoende. Beslutet blev att behålla mappningen (Beslut 11) och i stället lägga
ett matcher-alias `{ADRESS, PLATS}` på evaluation-sidan. Skälet var
försvarbart: att ändra runtime-beteendet skulle göra alla baslinjer ojämförbara
och kräver intressentdiskussion enligt arkitektur.md 14.1. Man valde medvetet
den icke-invasiva vägen för att bevara jämförbarheten.

**Akt 3, prioriteringsutträngning (iteration 3).** Analysen ramade in felet som
ett kombinationsdataset-problem och dimensionerade aliaset efter de 17 FP som
syntes där. Det globala fenomenet, att `LOC` blir adress i *alla* texter, är
större: aliaset hjälper bara där det finns en `context.plats`-etikett att
aliasa mot, vilket bara är de 27 kombinationstexterna. De 33 falska positiva i
denna rapport ligger i de 132 övriga texterna där aliaset inte ger någon
lindring. Det öppna problemet loggades korrekt vidare i arkitektur.md 14.3 som
en iteration 3-inriktning, men out-prioriterades av formaliserings- och
rapportarbetet inför inlämningen.

## 12. Hur det åtgärdas, kortfattat (första utkast, reviderat nedan)

> **Reviderat.** Förslaget nedan var ett första utkast. Under granskning visade
> det sig vara fel ansats. Sektion 13 förklarar varför regex-vägen inte håller,
> sektion 14 visar att grundproblemet i själva verket är en inkoherent
> kategoridefinition, och sektion 15 lyfter den arkitektoniska rotorsaken som
> ligger ovanför allt. Texten i avsnitt 12 behålls oförändrad med flit, så att
> resonemangets utveckling är spårbar.

NER-till-artikel 4 är rätt princip och ska behållas. `PRS → NAMN` är en ren
entitet-till-artikel 4-mappning och fungerar. Det enda felet är `LOC → adress`,
eftersom ett ortnamn inte är en persons gatuadress. En gatuadress är dessutom
ett *strukturerat mönster* (gatunamn, husnummer, postnummer, postort), och
enligt projektets egen lagerfilosofi hör strukturerade mönster hemma i Lager 1
(regex), precis som personnummer och IBAN, inte i NER.

Minimal, designkonsistent åtgärd i tre steg:

1. **Lägg en gatuadress-recognizer i Lager 1** (regex: gatunamn + husnummer,
   eventuellt + postnummer + postort), byggd som de befintliga recognizers i
   [gdpr_classifier/layers/pattern/recognizers/](gdpr_classifier/layers/pattern/recognizers/).
   Den fångar de äkta `article4.adress`-fallen med hög precision.
2. **Ändra EntityLayer `LOC → context.plats`** i stället för `article4.adress`
   ([entity_layer.py:21](gdpr_classifier/layers/entity/entity_layer.py#L21)).
   Ett ortnamn är en kontextsignal, inte en direkt artikel 4-identifierare.
   `PRS → NAMN` och `ORG → ORGANISATION` lämnas oförändrade.
3. **Revidera matcher-aliaset och baslägg om.** När `LOC` inte längre blir
   adress kan `CATEGORY_ALIASES {ADRESS, PLATS}` omprövas. Detta ändrar
   mätinstrumentet och kräver ett Loggbok-beslut plus en omkörning av baslinjen.

Effekten är att de 33 falska positiva flyttas från ett över-genererande NER-fel
till en precis regelbaserad recognizer, utan att den arkitektoniska principen
(NER mappar mot artikel 4) överges. Det missade IBAN-formatet (avsnitt 5.1) är
en separat, isolerad recognizer-fix som inte rör mätinstrumentet.

---

## 13. Varför regex-vägen inte håller

Regex-förslaget i avsnitt 12 granskades och föll på tre invändningar, alla
korrekta. Detta dokumenteras eftersom det är en viktig del av resonemanget, inte
en parentes.

**Gatusuffix är ingen sluten klass.** Idén byggde på att svenska gatunamn slutar
på en uppräknelig mängd ändelser (`-gatan`, `-vägen`, `-gränd`). Men det finns
gott om suffixlösa adresser: "Avenyn", "Slussen", "Stureplan", "Munkbron",
"Sergels torg", landsbygdsadresser som "Backgården 3", postboxar som "Box 1234".
Listan läcker åt båda håll och är inte sluten.

**Postnummer har ingen kontrollsiffra.** Det här rättar ett eget felaktigt
påstående i avsnitt 12. Personnummer, IBAN och betalkort ligger i Lager 1
*för att de har en checksumma* (Luhn, mod97) som ger nära binär säkerhet. Ett
svenskt postnummer är bara fem siffror med ett mellanslag, `NNN NN`, utan
checksumma. Det matchar lika gärna inuti telefonnummer, belopp,
referensnummer och datum. En adress hör därför **inte** hemma i samma
precisionsklass som Lager 1:s befintliga recognizers. Utan checksumma blir det
exakt samma sorts över-träffande mönster som problemet vi försöker lösa.

**Lexikal och numerisk polysemi.** "plats fjorton" eller "jag är fjorton" är
inte adresser. Ordet "plats" är polysemt och utskrivna tal är tvetydiga. Varje
detektor som nycklar på ett enskilt lexem eller på siffror ensamma producerar
brus. Det enda robusta signalet är att flera svaga signaler sammanfaller
(gatliknande ord plus husnummer plus adresskontext som "bor på", "c/o",
signaturblock), och en sådan konjunktionslogik i fri svensk text är ett
genuint svårt problem, inte en recognizer på en eftermiddag.

## 14. Den verkliga rotorsaken: en inkoherent och gles kategoridefinition

Innan man bygger någon detektor måste man veta vad som ska detekteras. En
inspektion av de 15 faktiska `article4.adress`-etiketterna i iteration
1-datasetet avslöjar att målet självt är inkoherent.

| Vad etiketten faktiskt är | Antal | Exempel |
|---|---:|---|
| Riktig gatuadress (gatunamn + husnummer) | **3** | "Sveavägen 44", "Teknikvägen 8", "Vasagatan 12" |
| Bara ortnamn | **12** | "Stockholm" ×3, "Göteborg" ×3, "Malmö" ×2 (inkl. "Malmö C"), "Örebro", "Linköping", "Uppsala", "Rosengård" |
| Innehåller postnummer (`NNN NN`) | **0** | inget alls |

Tolv av femton etiketterade "adresser" är alltså exakt samma sorts nakna ortnamn
som utgör de 33 falska positiva. "Stockholm" är etiketterat `article4.adress`
tre gånger i iteration 1, samtidigt som "Stockholm" i kombinationsdatasetet är
`context.plats` och i article9-texterna helt oetiketterat. Samma ytform, tre
olika facit beroende på vilket deldataset den ligger i.

Det är därför varken regex, NER eller LLM kan lösa det: ingen detektor kan
samtidigt ha rätt mot tre motstridiga facit. Precisionsproblemet för adress är
inte i grunden ett detektorval utan en annoteringsdefinition som aldrig
fastställdes. Konsekvensen för åtgärd:

1. **Definitionsbeslut, inte kod.** Bestäm om `article4.adress` betyder en
   strukturerad gatuadress eller vilken ortreferens som helst. Är det det
   förra ska de tolv nakna städerna om-etiketteras till `context.plats`. Är
   det det senare är kategorin en dubblett av `context.plats` och bör slås
   ihop. Tolv av femton etiketter måste röras oavsett vilket.
2. **Dokumenterad avgränsning.** Precis postadress-detektion i fri svensk text
   utan strukturella ledtrådar är ett öppet problem och bör redovisas som en
   känd avgränsning och ett framtida-arbete-stycke, inte jagas som en kodfix
   före inlämning. Det matchar projektets `recall > precision`-filosofi och är
   ärligt mot spårbarheten.

Detektorfrågan kollapsar alltså så snart man inser att kategorin är inkoherent
och bara innehåller tre äkta fall. Att försöka bygga en robust svensk
adressparser för tre instanser vore att över-ingenjöra fel problem.

## 15. Den arkitektoniska rotorsaken som ligger ovanför allt

Hela analysen kan sammanfattas på arkitekturnivå. Den avsedda arkitekturen är
att lagren körs oberoende och parallellt, att allt samlas i aggregatorn, och att
**aggregatorn korsverifierar lagren mot varandra och fattar känslighetsbeslutet**
(till exempel: en gata som LLM-lagret hittar ska styrkas mot NER-lagret, och
uteblivet stöd ska räknas som hallucinationsrisk). Frågan är om koden uppfyller
det. Svaret är: delvis. Skelettet finns, mönstret är bevisat på ett ställe, men
den generella korsverifieringen är inte byggd.

**Det som uppfylls.** Oberoende parallell bedömning fungerar.
[pipeline.py:24-31](gdpr_classifier/pipeline.py#L24-L31):

```python
for layer in self.layers:
    all_findings.extend(layer.detect(text))
return self.aggregator.aggregate(findings=all_findings, ...)
```

Varje lager får råtexten, inget lager ser ett annat lagers fynd, allt samlas på
ett ställe.

**Det enda stället korsverifiering sker.** Mönstret du beskriver finns
implementerat, men bara för `context.kombination`.
[aggregator.py:306-324](gdpr_classifier/aggregator.py#L306-L324), Mekanism 3:

```python
def _passes_mechanism_3(self, kombination, all_findings):
    evidence = [
        f for f in all_findings
        if (f.source.startswith("pattern.") or f.source.startswith("entity."))
        and f.start < kombination.end and kombination.start < f.end
    ]
    return len(evidence) >= self.min_evidence_count
```

Ett LLM-fynd (kombinationsclaimet) godtas bara om minst två mönster- eller
NER-fynd överlappar det. Saknas stöd valideras det inte. Det är exakt den
korsverifiering arkitekturen tänkte sig, byggd för pusselbitsfallet (Beslut
19/21) och aldrig generaliserad.

**Det som inte uppfylls.** För allt annat gör aggregatorn ingen korsverifiering.
[aggregator.py:73-90](gdpr_classifier/aggregator.py#L73-L90):

```python
filtered = self._apply_containment_rules(findings)            # 2 hårdkodade borttagningsregler
filtered = self._deduplicate_same_category_overlap(filtered)  # slå ihop samma kategori
overlaps = self._find_overlaps(filtered)                       # registrera par, inget beslut
identifiability, data_class = self._determine_dimensions(filtered)
```

Article9Layers LLM-fynd korsverifieras mot ingenting. Det finns ingen regel
"LLM hittade en gata, kolla mot NER, flagga annars hallucinationsrisk".
Aggregatorn nedviktar eller flaggar aldrig ett fynd för uteblivet stöd i ett
annat lager. Och känslighetsbeslutet är en ren existenskoll, inte en
evidensvägning. [aggregator.py:262-281](gdpr_classifier/aggregator.py#L262-L281):

```python
has_article4 = any(f.category.value.startswith("article4.") for f in findings)
has_article9 = any(f.category.value.startswith("article9.") for f in findings)
if has_article4:
    identifiability = Identifiability.DIRECT
if has_article9:
    data_class = DataClass.SPECIAL
```

Ett enda ostött LLM-fynd räcker för att vippa hela klassningen till SPECIAL utan
att något annat lager behöver hålla med. Det är motsatsen till korsverifiering.

**Varför detta är hela poängen.** De 33 LOC-adress-falskpositiva och LLM:ens
över-genereringar överlever ända fram till siffrorna just för att aggregatorn
inte gör den korsverifiering arkitekturen tänkte sig. Vore designen fullt
realiserad, alltså "ett `article4.adress` från NER måste styrkas av ett
mönsterlager-fynd med adresstruktur, annars nedrankas det", skulle de nakna
städerna filtrerats bort av aggregatorn på samma sätt som ostödda kombinationer
filtreras idag. **Gapet mellan tänkt arkitektur och byggd aggregator är
precisionsproblemet, uttryckt på arkitekturnivå.** Allt i avsnitt 1 till 14 är
yttringar av samma sak: korsverifieringsmönstret finns och fungerar för
kombination via Mekanism 3, men det generaliserades aldrig till de övriga
lagren, av samma scope- och prioriteringsskäl som proveniensspårningen i avsnitt
11 beskriver.

Det är inte ett kodfel. Det är en delvis realiserad arkitektur, fullt spårbar i
projektets egen dokumentation, och den riktiga åtgärden ligger på designnivå:
generalisera Mekanism 3:s korsverifieringsmönster från enbart `context.kombination`
till en evidensvägande aggregator, eller dokumentera medvetet att den
generaliseringen är framtida arbete. Bägge är legitima. Att låtsas att det är en
isolerad bugg vore det inte.
