# Iteration 2: Implementationsplanering

**Projekt:** gdpr-classifier  
**Iteration:** 2 (v0.2.0-dev)  
**Period:** v17-v19  
**Metodik:** Scrumban (kanban-board i GitHub Projects)

> **[UNDER UPPBYGGNAD]** Denna fil är under aktiv uppbyggnad. Iterationsförberedelse pågår och specifik teknisk planering — inklusive issue-specifikationer, beroendekarta och förväntade resultat — fylls i löpande i takt med att arkitekturplaneringen för Lager 3 genomförs tillsammans med arkitekt-agenten. En framtida läsare (handledare, examinator eller annan agent) bör beakta att innehållet reflekterar ett pågående arbete och att tomma sektioner är avsiktliga platshållare.

---

## Mål och scope

Iteration 2 har Lager 3 (kontextuell analys) som huvudfokus. Lager 3 bedömer om texten som helhet är känslig trots avsaknad av explicita identifierare — exempelvis en mening som indirekt pekar ut en person genom kombination av arbetsplats, ort och yrkesroll. Detta svarar mot GDPR artikel 4:s breda definition av personuppgift och kompletterar Lager 1 (mönsterigenkänning) och Lager 2 (NER).

Kombinationslogiken för pusselbitseffekten integreras med Lager 3-implementationen: fynd av typen `context.*` i kombination med `article4.*` eller `article9.*` ska höja `SensitivityLevel` till `MEDIUM` i aggregatorn. Logiken är redan förberedd i `gdpr_classifier/aggregator.py` men lämnad utan aktivering i iteration 1.

Teknikvalet — zero-shot-klassificering, lokal LLM (t.ex. via Ollama), SLM, RAG eller annan ansats — är öppet och fastställs iterativt under designcykel 2 baserat på prestanda, resurskrav och intressentfeedback. Lokal LLM introduceras enbart om zero-shot-klassificering visar sig otillräcklig, i enlighet med principen om att undvika onödig teknisk skuld (arkitektur.md, avsnitt 6).

Förbättringar baserade på iteration 1-feedback — exempelvis containment-regel för NER och reducering av falska positiva i entitetslager — kan ingå i iteration 2, men prioriteras lägre än Lager 3-implementationen och utvärderas under iterationens gång.

Specifik scope-avgränsning och prioritering fastställs i samband med arkitekturplanering tillsammans med arkitekt-agenten.

Detta avsnitt revideras när arkitekturplaneringen för Lager 3 är genomförd.

---

## Beroendekarta

Beroendekartan visar vilka issues som beror på varandra och i vilken ordning de bör implementeras, inklusive parallella spår och konvergenspunkter.

```
Kluster 1
               #68 → #69, #78, #84
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
Kluster 5      Kluster 2      Kluster 3
#76, #77       #70, #71       #72, #73
    │              │              │
    │              └──────┬───────┘
    │                     │
    │                     ▼
    │                 Kluster 4
    │                  #74, #75
    │                     │
    └─────────────────────┤
                          │
                          ▼
                      Kluster 6
                      #79, #80
```

Kluster 1 är blockerande för Kluster 2, 3 och 5. #84 beror på #69 och är beroende från #70 och #72 (modellvalet motiveras av probe-resultaten). Kluster 4 beror på Kluster 2 och 3. Kluster 6 är slutskede efter Kluster 4. Detaljerade beroenden per issue dokumenteras i issuesarna själva (GitHub) samt i Issue-specifikationer-tabellen nedan.

---

## Förväntade resultat

Förväntade resultat — kvantitativa mätvärden och kvalitativa mål för designcykel 2 — specificeras efter att issues har formulerats och testdatauppsättningen för kontextuellt känsliga texter har definierats.

---

## Issue-specifikationer

Status-legenda: ✅ Klar | 🔄 Pågår | ⏸️ Blockerad | ⬜ Ej startad

### Kluster 1: Infrastruktur & SSOT

| Issue | Titel | Status | Blockeras av | Sessionspost |
|---|---|---|---|---|
| #68 (I-1) | SSOT-revidering för iteration 2 | ✅ Klar | - | 2026-04-30 |
| #69 (I-2) | LLMProvider-abstraktion | ✅ Klar | #68 | 2026-04-30 |
| #78 (I-11) | Prompt-konstruktion enligt etablerad metod | ✅ Klar | #68 | 2026-04-30 |
| #84 (I-14) | Modellutvärdering — probe-skript för Ollama-modellval | ✅ Klar | #69 | 2026-05-01 |

### Kluster 2: Article9Layer

| Issue | Titel | Status | Blockeras av | Sessionspost |
|---|---|---|---|---|
| #70 (I-3) | Article9Layer | ✅ Klar | #69, #78 | 2026-05-01 |
| #71 (I-4) | Testdataset, artikel 9-texter | ⬜ Ej startad | - | - |

### Kluster 3: CombinationLayer

| Issue | Titel | Status | Blockeras av | Sessionspost |
|---|---|---|---|---|
| #72 (I-5) | CombinationLayer | ✅ Klar | #69, #78 | 2026-05-01 |
| #73 (I-6) | Testdataset, pusselbitseffekt-texter | ⬜ Ej startad | - | - |

### Kluster 4: Aggregator & Evaluation

| Issue | Titel | Status | Blockeras av | Sessionspost |
|---|---|---|---|---|
| #74 (I-7) | Aggregator med kombinationslogik och D5-korrigering | ⬜ Ej startad | #70, #72 | - |
| #75 (I-8) | Utvärderingsmodul-utökning för Lager 3 och 4 | ⬜ Ej startad | #74 | - |

### Kluster 5: Edge cases & Testdata

| Issue | Titel | Status | Blockeras av | Sessionspost |
|---|---|---|---|---|
| #76 (I-9) | Containment-regel för IBAN-telefon-överlapp | ⬜ Ej startad | #68 | - |
| #77 (I-10) | Testdataset-utökning, längre texter med pattern och NER | ⬜ Ej startad | - | - |

### Kluster 6: Utbytbarhet & Demo

| Issue | Titel | Status | Blockeras av | Sessionspost |
|---|---|---|---|---|
| #79 (I-12) | Layer-protokollets utbytbarhet med stub-Layer | ⬜ Ej startad | #72 | - |
| #80 (I-13) | Demo-uppdatering för Lager 3 och 4 | ⬜ Ej startad | #70, #72, #74 | - |

---

## Loggbok

Designbeslut för iteration 2 dokumenteras i Loggboken (Google Docs) under fliken **"Loggbok - iteration 2"**. Format: beslut, alternativ som övervägdes, motivering, koppling till GDPR-krav eller empiriskt stöd.

Denna fil listar inga beslut. Alla arkitektoniska och metodologiska avgöranden under iteration 2 förs in direkt i Loggboken med full motivering. Om ett beslut genereras under en agent-session ska det även noteras i sessionens post under "Beslut fattade" nedan, med hänvisning till Loggboken för längre motivering.

---

## Arbetsflöde

Iteration 2 följer samma åtta-stegs-loop som iteration 1, beskriven i [`arbetsflode.md`](arbetsflode.md). Skillnaden mot iteration 1 är att Claude Code används som implementations-agent istället för Cursor: Claude Code tar emot issue-specifikationer, genererar plan i Plan Mode, och implementerar i Agent Mode efter användarens godkännande.

---

## Agent-sessionslogg

### Regel

**Varje agent (AI eller människa) som arbetar i en session ska logga sin session här efter avslutad iteration.** Loggen är komplement till Loggboken ovan: Loggboken dokumenterar *beslut och motiveringar*, medan sessionsloggen dokumenterar *vad som faktiskt gjordes, i vilken ordning, och av vem*. Syftet är spårbarhet och att nästa agent (eller granskare) snabbt ska kunna förstå repots historik utan att läsa hela git-loggen.

### Format

Lägg till en ny post längst ner. Använd följande mall:

```markdown
### Session YYYY-MM-DD - [Agent/Person]

**Iteration:** [t.ex. 2 / v0.2.0]
**Mål:** [en mening om vad sessionen skulle åstadkomma]

**Ändrade filer:**
- `path/till/fil.py` - [kort beskrivning]

**Gjort:**
- [punkt per konkret åtgärd]

**Beslut fattade:** [kort; länka till Loggboken om längre motivering behövs]
**Öppet/Nästa steg:** [vad som återstår eller blockerar]
```

### Regler för loggning

1. Logga **efter varje iteration** (eller efter en sammanhållen arbetssession om iterationen sträcker sig över flera dagar).
2. En post per session, inte per commit.
3. Håll det kort: punktlistor, inga resonemang (de hör hemma i Loggboken).
4. Ändra aldrig tidigare poster. Lägg till en ny post om något behöver korrigeras.
5. Om sessionen genererade arkitekturbeslut ska dessa även föras in i Loggboken med full motivering.

### Poster

<!-- Kommande sessionsposter läggs till här i kronologisk ordning. -->
### Session 2026-04-30 - Claude Code (Sonnet 4.5) - Issue `#68`

**Iteration:** 2 / v0.2.0-dev
**Mål:** Issue #68 (I-1) — SSOT-revidering för iteration 2.

**Ändrade filer:**
- `docs/arkitektur.md` - 8 sektioner reviderade (3.1, 3.2, 6, 7, 8, 10, 11, 12)
- `CLAUDE.md` - 4 sektioner reviderade (1, 5, 6, 7)
- `docs/iteration_2_utvardering.md` - intressent-tabell anonymiserad

**Gjort:**
- Sektion 6 omstrukturerad till 6.1 (Article9Layer) och 6.2 (CombinationLayer)
- Sektion 8 reviderad med ny pseudokod, tre konfigurerbara trösklar, D5-korrigering, Privacy by Design-motivering
- Sektion 10 utökad med nya lagerkataloger (utanför ursprungligt scope, motiverat av konsistenskrav)
- Beslut 17-21 tillagda i sektion 12
- Notering om saknad GENETISK_DATA-enum-kategori (hanteras i Issue #70)

**Beslut fattade:** Sektion 10 inkluderades utöver acceptanskriterier för att undvika drift mellan filstruktur-dokumentation och nya lagerkataloger.
**Öppet/ Nästa steg:** Commit efter granskning. GENETISK_DATA-tillägg till Category-enum hanteras i Issue #70 (alternativ a, b eller c att bestämma vid issue-öppning).

### Session 2026-04-30 - Claude Code (Sonnet 4.6) - Issue `#69`

**Iteration:** 2 / v0.2.0-dev
**Mål:** Issue #69 (I-2) — LLMProvider-abstraktion: skapa utbytbar provider-abstraktion för Ollama och Gemini.

**Ändrade filer:**
- `gdpr_classifier/layers/llm/__init__.py` - ny fil, re-exporterar LLMProvider, LLMProviderError, OllamaProvider, GeminiProvider
- `gdpr_classifier/layers/llm/provider.py` - ny fil, LLMProvider Protocol (@runtime_checkable) + LLMProviderError
- `gdpr_classifier/layers/llm/ollama_provider.py` - ny fil, OllamaProvider via /api/generate
- `gdpr_classifier/layers/llm/gemini_provider.py` - ny fil, GeminiProvider via google-genai SDK (icke-produktion)
- `gdpr_classifier/config.py` - utökad med get_llm_provider() (LLM_PROVIDER env-var, default ollama)
- `pyproject.toml` - llm-beroenden tillagda (requests>=2.31, google-genai>=1.0) i ny [llm]-grupp och i [all]
- `tests/unit/test_ollama_provider.py` - ny fil, 12 enhetstester med unittest.mock
- `tests/unit/test_gemini_provider.py` - ny fil, 12 enhetstester med sys.modules-patchning
- `docs/iteration_2_implementation.md` - status #69 uppdaterad

**Gjort:**
- LLMProvider definierad som typing.Protocol med @runtime_checkable, konsistent med Layer- och Recognizer-protokollen
- OllamaProvider: requests mot /api/generate, format="json", temperature=0.0 default, system-parameter valfri
- GeminiProvider: google-genai v1.x SDK, response_mime_type="application/json", GDPR-varning vid instansiering, API-nyckel från GEMINI_API_KEY
- LLMProviderError: enkel basklass utan subklasser (konsumerande lager hanterar alla fel uniformt per Beslut 21)
- get_llm_provider() i config.py läser LLM_PROVIDER env-var, default "ollama"
- 48/48 tester gröna, inga regressioner

**Beslut fattade:** Valde typing.Protocol (inte ABC) för konsistens med befintliga Layer/Recognizer-protokoll. Valde google-genai v1.x (inte legacy google-generativeai). Valde unittest.mock (stdlib) för testpatchning. llm-beroenden inkluderades även i [all]-gruppen (användarbeslut). Se Loggboken för full motivering (Beslut 17, 18).
**Öppet/ Nästa steg:** #70 (Article9Layer) och #72 (CombinationLayer) är avblockerade. #78 (Prompt-konstruktion) ingår i Kluster 1 och kan köras parallellt.

### Session 2026-04-30 - Antigravity (Claude Opus 4.6) - Issue `#78`

**Iteration:** 2 / v0.2.0-dev
**Mål:** Issue #78 (I-11) — Prompt-konstruktion enligt etablerad metod: YAML-schema, loader-modul, validering och placeholder-prompts.

**Ändrade filer:**
- `gdpr_classifier/prompts/__init__.py` - ny fil, re-exporterar Prompt, load_prompt, PromptError, PromptLoadError, PromptValidationError. Docstring dokumenterar YAML-schema, assembly-ordning och forskningsreferenser.
- `gdpr_classifier/prompts/loader.py` - ny fil, Prompt dataclass (frozen), load_prompt() med base_dir DI-parameter, PromptError/PromptLoadError/PromptValidationError exception-hierarki, YAML-validering, versionsresolution, deterministisk assembly.
- `gdpr_classifier/prompts/article9/v1.yaml` - ny fil, placeholder-prompt för Article9Layer med alla obligatoriska och valfria fält.
- `gdpr_classifier/prompts/combination/v1.yaml` - ny fil, placeholder-prompt för CombinationLayer, inkluderar Wei et al. (2022) i source_citations.
- `pyproject.toml` - pyyaml>=6.0 tillagd i [llm]-gruppen.
- `tests/unit/test_prompt_loader.py` - ny fil, 17 testfall (5 kärnfall + 12 ytterligare) med tmp_path-fixtures och base_dir dependency injection.
- `docs/iteration_2_implementation.md` - status #78 uppdaterad.

**Gjort:**
- Sammansättningsordning: task_instruction → context → reasoning_instructions → examples → output_format, motiverat av Reynolds & McDonell (2021). system_prompt hålls separat.
- Examples renderas i Brown et al. (2020)-format med Input/Output/Rationale och avgränsare.
- Exception-hierarki: PromptError (bas) → PromptLoadError + PromptValidationError.
- Versionsresolution: regex ^v(\d+)\.yaml$, numerisk sortering (v10 > v9).
- load_prompt() tar base_dir: Path | None = None för testbar dependency injection.
- yaml.safe_load används exklusivt, dokumenterat i docstring.
- 66/66 enhetstester gröna, inga regressioner.

**Beslut fattade:** base_dir-parameter istället för monkeypatch av _PROMPTS_DIR (dependency injection). pyyaml enbart i [llm]-grupp, inte [all]. Se Loggboken för full motivering.
**Öppet/ Nästa steg:** Kluster 1 är komplett (#68 ✅, #69 ✅, #78 ✅). #70 (Article9Layer) och #72 (CombinationLayer) är fullt avblockerade. arkitektur.md sektion 10 behöver uppdateras med prompts/-katalogen (görs separat efter verifiering).

### Session 2026-05-01 - Antigravity (Claude Opus 4.6) - Issue `#84`

**Iteration:** 2 / v0.2.0-dev
**Mål:** Issue #84 (I-14) — Modellutvärdering: probe-skript för Ollama-modellval.

**Ändrade filer:**
- `scripts/probe_prompts.py` - ny fil, 14 probe-prompts (5 Kategori A: JSON-validitet, 9 Kategori B: svensk språkförståelse) som ProbePrompt dataclass
- `scripts/probe_llm_models.py` - ny fil, CLI-skript som kör probes mot OllamaProvider, mäter latens, validerar JSON, bedömer korrekthet, genererar markdown-resultatfil
- `scripts/probe_results_2026-05-01.md` - resultatfil med sammanfattning, per-prompt-detaljer och rekommendation
- `docs/iteration_2_implementation.md` - #84 tillagd i Kluster 1, status uppdaterad

**Gjort:**
- ProbePrompt dataclass (frozen) med id, category, system_prompt, task_prompt, text, expected_json_keys, expected_classification
- 5 Kategori A-prompts (trivial JSON-extraktion) och 9 Kategori B-prompts (5 positiva artikel 9-fall, 4 negativa kontroller)
- CLI med --models (obligatoriskt), --output-dir, --temperature, --runs-per-prompt
- Latensmätning med time.perf_counter(), snitt och P95
- Modellstorlek via subprocess-anrop till "ollama show"
- Robust felhantering: Ollama-anslutningskontroll vid start, modell-existenskontroll, LLMProviderError per prompt
- Normaliseringsfunktion _normalize_category() tillagd efter första körningen: NFKD-normalisering, ASCII-filtrering, lowercase, mellanslag→underscore. Löser formatvariationer ("hälsodata" vs "halsodata", "etniskt ursprung" vs "etniskt_ursprung") utan att acceptera engelska översättningar ("religious_belief")
- Körning mot llama3.1:8b, qwen2.5:7b-instruct, mistral-nemo:12b. Alla 5/5 JSON-validitet. Svensk-korrekt: qwen2.5:7b-instruct 8/9, llama3.1:8b 6/9, mistral-nemo:12b 5/9
- 66/66 enhetstester gröna, inga regressioner

**Beslut fattade:** Kategori-normalisering appliceras på båda sidor (expected + actual) före jämförelse. Strikt boolean-jämförelse för contains_sensitive behålls. Engelska svar räknas som fel (modellen följer inte svensk formatinstruktion).
**Öppet/Nästa steg:** Kluster 1 komplett (#68 ✅, #69 ✅, #78 ✅, #84 ✅). Rekommendation: qwen2.5:7b-instruct som primär modell. #70 (Article9Layer) och #72 (CombinationLayer) kan använda denna modell som utgångspunkt.

### Session 2026-05-01 - Antigravity (Gemini 3.1 Pro) - Issue `#70`

**Iteration:** 2 / v0.2.0-dev
**Mål:** Issue #70 (I-3) — Article9Layer: Implementera lager 3 för direkt detektion av artikel 9-data via LLM.

**Ändrade filer:**
- `gdpr_classifier/core/category.py` - Lade till `GENETISK_DATA = "article9.genetisk_data"`
- `gdpr_classifier/layers/article9/__init__.py` - Ny fil, re-exporterar Article9Layer och Article9LayerError
- `gdpr_classifier/layers/article9/article9_layer.py` - Ny fil, Article9Layer som uppfyller Layer-protokollet, använder LLMProvider och text.find()-validering
- `gdpr_classifier/prompts/article9/v2.yaml` - Ny fil, prompt v2 med 4 examples och avgränsningsinstruktioner
- `tests/unit/test_article9_layer.py` - Ny fil, 10 enhetstester

**Gjort:**
- Lagt till saknad enum-kategori för genetisk data.
- Byggt `Article9Layer` med dependency injection av `LLMProvider`.
- Implementerat validering av hallucinations-`text_span` via case-sensitive sedan case-insensitive `text.find()`.
- Skapat en robust prompt i YAML-format (`v2.yaml`) som specificerar uppgiften och avgränsningen från identifierbarhetsbedömning.
- Skrivit omfattande enhetstester (konstruktorkrav, tomt svar, positivt fynd, hallucinerat fynd, fallback casing, schemafel, provider errors).
- Verifierat att testerna går grönt.

**Beslut fattade:** Två designbeslut förs in i Loggboken (iteration 2): hallucinations-skydd via `text.find()` på lagernivå som komplement till aggregatorns Mekanism 1; tillägg av `GENETISK_DATA` som separat artikel 9-kategori med juridisk motivering enligt art. 9.1. Strikt substring-match: vid utebliven träff ignoreras fyndet helt.
**Öppet/Nästa steg:** Kluster 2 fortsätter med #71 (testdataset, artikel 9-texter). Kluster 3 (#72 CombinationLayer, #73 testdataset) kan köras parallellt. Känd begränsning: text.find() matchar första förekomsten — duplicerade text_span på olika positioner i samma text kollapsas till samma span. Hanteras vid behov i iteration 3 baserat på utvärderingsutfall.

### Session 2026-05-01 - Antigravity (Gemini 3.1 Pro) - Issue `#72`

**Iteration:** 2 / v0.2.0-dev
**Mål:** Issue #72 (I-5) — CombinationLayer: Implementera lager 4 för bedömning av pusselbitseffekten enligt GDPR skäl 26 via LLM.

**Ändrade filer:**
- `gdpr_classifier/core/category.py` - Lade till `YRKE`, `PLATS` och `KOMBINATION` under kontextsignaler.
- `gdpr_classifier/layers/combination/__init__.py` - Ny fil, re-exporterar CombinationLayer och CombinationLayerError.
- `gdpr_classifier/layers/combination/combination_layer.py` - Ny fil, CombinationLayer som uppfyller Layer-protokollet, använder LLMProvider och utför differentierad validering av fynd.
- `gdpr_classifier/prompts/combination/v2.yaml` - Ny fil, prompt v2 med 3 examples, systeminstruktioner för svensk kontext, och CoT-resonemang för pusselbitseffekten.
- `tests/unit/test_combination_layer.py` - Ny fil, 7 enhetstester för alla valideringsscenarier och schemafel.
- `docs/arkitektur.md` - Uppdaterat SSOT 3.3 med de tre nya enum-posterna i Category-blocket.

**Gjort:**
- Lagt till nya enum-kategorier för yrke, plats och kombination (skäl 26).
- Byggt `CombinationLayer` med dependency injection av `LLMProvider`.
- Implementerat validering i tre steg: schemavalidering, individuella signaler (case-sensitive/insensitive fallback), och aggregatfynd (differentierad validering med exact, insensitive, normalized, och reconstructed fallbacks).
- Skapat robust prompt i YAML-format (`v2.yaml`) som specificerar uppgiften och avgränsningen från direkt Artikel 9/4-detektion, med betoning på svensk språkhantering.
- Skrivit omfattande enhetstester och lagt in mock-förväntningar.

**Beslut fattade:** Val av differentierad validering för att skydda mot LLM-hallucinationer (Beslut 21) implementeras genom fallback till whitespace-normalisering eller min/max-positionering av de individuella signalerna vid aggregat-fel. Reasoning-fältet i combination-output görs obligatoriskt vid is_identifiable=true (Beslut 22, Loggbok iteration 2) för att operationalisera Wei et al. (2022) chain-of-thought-spårbarhet.

**Öppet/Nästa steg:** Kluster 4 (#74 Aggregator med kombinationslogik och #75 Utvärderingsmodul-utökning) avblockeras av detta samt #70 som är klara. #73 (testdataset) kvar i Kluster 3.
