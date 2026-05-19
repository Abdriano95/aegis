# Teknisk stack-inventering — underlag för kapitel 4 (Genomförande)

> **Status:** Underlagsdokument, inte rapporttext. Detta är ett strukturerat
> inventeringsunderlag som Abdulla och Johanna formulerar om till rapportprosa i
> avsnitt 4.1.x "Teknisk stack". Ingen text här är avsedd att kopieras ordagrant
> in i uppsatsen.

---

## 0. Inledning och metodnotering

### Syfte

Tech-stacken i `gdpr-classifier` växte fram **under genomförandet**, inte vid
metodvalet. Detta dokument inventerar artefaktens fullständiga tekniska stack
organiserad per komponent, med introduktionstidpunkt (commit-hash + datum) och
motiveringsspårning per verktyg, så att kapitel 4 kan beskriva *när* och *varför*
varje verktyg kom in.

### Hur dokumentet är organiserat

- **Sektion 1** — sammanfattningstabell över alla verktyg.
- **Sektion 2** — detaljerad beskrivning per kategori.
- **Sektion 3** — faktaruta per verktyg.
- **Sektion 4** — motiveringsbehov i rapporten.
- **Sektion 5** — död/kvarvarande kod och dependency-anomalier.
- **Sektion 6** — kronologisk tidslinje iteration 1 → 3.

### Källor och verifieringsmetod

Underlaget bygger på direkt läsning av repot på `main` (HEAD `21b9417`,
2026-05-18): `pyproject.toml`, alla `import`/`from`-rader i `*.py` (helrepo-grep
med `.venv` exkluderad), LLM-providerfiler, `entity_layer.py`, Lager 1-
recognizers, `.env.example`, `README.md`, `.claude/settings.json`,
`tools/measure_prompt_tokens.py`, samt `git log --diff-filter=A` per komponentfil
och `git log -p -- pyproject.toml` för introduktionsdatum. Sessionsposter i
`docs/iteration_1_demoforberedelse.md` och `docs/iteration_3_implementation.md`
användes för verktygstidpunkter.

### Två metodnoteringar att läsa innan tabellerna

**(A) Versionskolumnen har dubbel källa.** `pyproject.toml` använder enbart
nedre-gräns-pins (`>=`) och repot har **ingen lock-fil** (ingen
`requirements*.txt`, `poetry.lock`, `uv.lock`, `.python-version`). Exakt
installerad version är därför inte fixerad av repot. Versionskolumnen anger
därför **pyproject-specifier som auktoritativ repo-källa** plus den **lokalt
observerade exakta versionen** från `.venv`-katalogens dist-info, uttryckligen
märkt "lokalt observerad, ej pinnad i repo". De lokala siffrorna är inte
auktoritativa — `.venv` är inte incheckad — men ger teamet de faktiska
versionerna för reproducerbarhetsavsnittet.

**(B) Två betydelser av "motivering".** Spec skiljer på två saker som hålls isär
här:
- Kolumnen **"Motivering finns (ja/nej)"** i sektion 1 = *finns det redan ett
  formellt Loggboks-beslut/dokumenterad motivering?* (ja = Beslut finns,
  nej = implementationsval utan formellt beslut).
- Sektion 4 **"Motiveringsbehov"** = *behöver verktyget motiveras i
  rapporttexten, eller är det ett default-/standardval som inte behöver
  försvaras?*

Dessa två är inte samma sak: ett verktyg kan sakna formellt beslut (kolumn =
nej) men ändå inte behöva motiveras i rapporten (default-val).

### Avvikelsenot mot uppgiftsspecifikationen (spec-regel 7)

Spec-regel 7 bad om att verifiera att Probe-branchens `AnthropicProvider` och
`GeminiProvider` "noteras som existerande i koden men inte mergat till main, om
de inte är mergat ännu". **Verifiering visar att antagandet inte stämmer: båda
är redan mergade till `main`.**

- `GeminiProvider` — commit `5312490`, 2026-04-30 (samma commit som
  `OllamaProvider` och `LLMProvider`-abstraktionen).
- `AnthropicProvider` — commit `91a573d`, 2026-05-17 (Beslut 60).
- Verifierat med `git merge-base --is-ancestor <hash> HEAD` → bägge är förfäder
  till `main`-HEAD. Probe-arbetet (I-7 + #107) mergades till `main` via PR #141.

Båda providers listas i inventeringen med status **"implementerad,
icke-produktion, behållen för framtida bruk eller reproducerbarhet av
probe-resultat"** (se faktarutor i sektion 3 för härkomst och beslutskoppling).

---

## 1. Sammanfattning

Kolumner enligt spec. "Lokalt" = observerad i `.venv` dist-info, ej pinnad i
repo. "Motivering finns" = formellt Loggboks-beslut existerar (ja/nej); separat
från rapportens motiveringsbehov (sektion 4).

| Verktyg | Version | Kategori | Lager/Komponent | Introducerat (commit + datum) | Motivering finns |
|---|---|---|---|---|---|
| Python | `requires-python >=3.11` (pyproject); runtime ej pinnad till patch | Språk/runtime | Hela artefakten | `d977b37` 2026-04-17 (Initial commit); pyproject `b4738ec` 2026-04-17 | nej (default) |
| `venv` (stdlib) | Medföljer Python | Virtuell miljö | Utvecklings-/körmiljö | Setup-steg (README), ej kodartefakt | nej (default) |
| `re` (stdlib) | Medföljer Python | Regex | Lager 1 (alla recognizers), `CombinationLayer` | `b4738ec` 2026-04-17 | nej (default) |
| Luhn (handskriven, stdlib) | Egen implementation, n/a | Checksummavalidering | Lager 1 — `betalkort.py`, `personnummer.py` | `b4738ec` 2026-04-17 | nej (algoritm trivial; detektionsbeslutet ligger i arkitektur-SSOT) |
| spaCy | `>=3.7` (pyproject) · 3.8.14 (lokalt) | NLP/NER-bibliotek | Lager 2 — `EntityLayer` | import `b4738ec` 2026-04-17; `nlp`-extra `3fe6db5` 2026-04-18 | nej (biblioteksval) / **ja för modellvalet** |
| `sv_core_news_lg` | Ej i pyproject; 3.8.0 (lokalt, laddas separat) | spaCy svensk NER-modell | Lager 2 — `EntityLayer` | `b4738ec` 2026-04-17 (default i `entity_layer.py`) | **ja** (modellval) |
| Ollama | Extern binär/tjänst, ej pinnad (HTTP `localhost:11434`) | Lokal LLM-runtime | Lager 3/4 — `OllamaProvider` | `5312490` 2026-04-30 | **ja** (Beslut 17) |
| `requests` | `>=2.31` (pyproject) · 2.33.1 (lokalt) | HTTP-klient | `OllamaProvider` + flera `scripts/` | `5312490` 2026-04-30 | nej (default HTTP-bibliotek) |
| `google-genai` | `>=1.0` (pyproject) · 1.74.0 (lokalt) | Moln-LLM SDK | `GeminiProvider` | `5312490` 2026-04-30 | **ja** (Beslut 17) |
| `anthropic` | `>=0.40` (pyproject) · 0.102.0 (lokalt) | Moln-LLM SDK | `AnthropicProvider` | `91a573d` 2026-05-17 | **ja** (Beslut 60, jfr Beslut 17) |
| PyYAML (`yaml`) | `>=6.0` (pyproject) · 6.0.3 (lokalt) | YAML-parsning | `gdpr_classifier/prompts/loader.py` | `141aba1` 2026-04-30 | nej (default) |
| Dash | `>=2.0` (pyproject) · 4.1.0 (lokalt) | Webb-UI-ramverk | `demo/` | `3fe6db5` 2026-04-18 | nej (implementationsval utan formellt beslut) |
| Plotly | Ej direkt dep; transitiv via Dash, **ej direktimporterad** | Visualisering | `demo/` (indirekt via Dash) | Transitiv (med Dash `3fe6db5` 2026-04-18) | nej |
| `pytest` | `>=8.0` (pyproject `dev`) · 9.0.3 (lokalt) | Testramverk | `tests/` | dep `b4738ec` 2026-04-17; första test `5e8aa39` 2026-04-18 | nej (default) |
| `setuptools` | `>=68` (build-system) · 82.0.1 (lokalt) | Build backend | Paketdefinition | `b4738ec` 2026-04-17 | nej (default) |
| `tiktoken` | **Ej i pyproject** (lokalt om installerad) | Token-mätning | `tools/measure_prompt_tokens.py` | `34731927` 2026-05-14 | **upptäckt vid full repo-skanning, ej tidigare diskuterat** |
| `transformers` | **Ej i pyproject**; lat/valfri import | Token-mätning (validering) | `tools/measure_prompt_tokens.py` | `34731927` 2026-05-14 | **upptäckt vid full repo-skanning, ej tidigare diskuterat** |
| Ruff | **Ej i pyproject, ej konfigurerad, ej installerad i venv** | Linter | Avsedd konvention (`noqa`-koder i koden) | n/a (aldrig införd som dependency) | nej (implementationsval utan formellt beslut) |
| mypy | **Ej i pyproject, ej konfigurerad, ej installerad i venv** | Statisk typkontroll | Avsedd konvention (SSOT nämner mypy-verifierbarhet) | n/a (aldrig införd som dependency) | nej (implementationsval utan formellt beslut) |
| Git | Extern, ej pinnad | Versionshantering | Hela projektet | `d977b37` 2026-04-17 | nej (default) |
| GitHub | Tjänst | Remote, PR, kodvärd | Hela projektet | Remote `origin` (projektstart) | nej (default) |
| GitHub Projects | Tjänst | Issue-/projektstyrning | Arbetsflöde (nio-stegs-loop) | Projektstart (process, ej kod) | nej (default) |
| Claude Code | AI-agent (Opus 4.7) | AI-utvecklingsverktyg | Implementation iteration 2→3 | Sessioner fr.o.m. 2026-05-11 (iter 3) | n/a (dokumenteras i metodens AI-avsnitt) |
| Claude Web | AI (arkitekt-agent) | AI-utvecklingsverktyg | Planering/arkitektur/akademisk text | Hela projektet | n/a (metodens AI-avsnitt) |
| NotebookLM | AI | AI-utvecklingsverktyg | Källextraktion ur litteratur | Ej kodspårbart | n/a (metodens AI-avsnitt) |
| Cursor | AI-agent (Opus) | AI-utvecklingsverktyg | Implementation iteration 1 | Sessioner 2026-04-18 → 2026-04-21 | n/a (metodens AI-avsnitt) |
| Antigravity / Gemini | AI-agent | AI-utvecklingsverktyg | Johannas iteration 1-spår | Session 2026-04-18 | n/a (metodens AI-avsnitt) |

---

## 2. Per kategori — detaljerad beskrivning

### 2.1 Språk och runtime

- **Python** — `pyproject.toml` anger `requires-python = ">=3.11"`. Ingen
  patch-version är pinnad och det finns ingen `.python-version`. Pattern
  matching (Python 3.10+) används i aggregatorn för uttömmande täckning
  (`docs/iteration_3_implementation.md` Session I-5); projektkravet `>=3.11`
  täcker detta.
- **Virtuell miljö** — Pythons inbyggda `venv` (`.venv/` i repo-roten,
  git-ignorerad). README beskriver setup på bash, PowerShell och CMD. Ingen
  Conda, Poetry, uv eller Pipenv. Ingen lock-fil.

### 2.2 Lager 1 — mönsterigenkänning

- **Regex-bibliotek:** Inget externt. Endast Pythons stdlib `re`. Recognizers:
  `email.py`, `iban.py`, `personnummer.py`, `betalkort.py`, `telefon.py`
  (alla i `gdpr_classifier/layers/pattern/recognizers/`), kontraktsbundna via
  `Recognizer`-protokollet (`recognizer.py`).
- **Checksummavalidering:** Inget externt bibliotek. **Luhn-algoritmen är
  handskriven** i ren Python i två filer:
  - `betalkort.py` → `_luhn_valid()` (regex `(?<!\d)(?:\d[\s\-]*){12,15}\d(?!\d)`
    + Luhn).
  - `personnummer.py` → `_luhn_valid()` + `_is_valid_date()` (regex för
    10/12-siffriga former med `-`/`+` + Luhn + datumkontroll).

### 2.3 Lager 2 — entitetsigenkänning (NER)

- **spaCy** — `pyproject.toml` extra `nlp = ["spacy>=3.7"]`. Lokalt observerad:
  3.8.14. Importeras direkt i `gdpr_classifier/layers/entity/entity_layer.py`
  (`import spacy`).
- **Modell:** `sv_core_news_lg` — spaCy:s stora svenska pipeline. Default-argument
  i `EntityLayer.__init__` (`model_name: str = "sv_core_news_lg"`). **Inte
  pip-paketerad och inte i pyproject** — laddas i ett separat steg
  (`python -m spacy download sv_core_news_lg`, README rad 24). Lokalt observerad
  version: **3.8.0** (`.venv` dist-info `sv_core_news_lg-3.8.0`). SUC3-etiketter
  `PRS/LOC/ORG` mappas till GDPR-kategorier `NAMN/PLATS/ORGANISATION`.

### 2.4 Lager 3 och 4 — LLM

- **Ollama** — primär, lokal LLM-runtime (Beslut 17). Extern tjänst, anropas
  över HTTP (`http://localhost:11434/api/generate`, `format="json"`,
  `temperature=0.0`, `num_ctx=16384`). Ingen versionspin (extern binär).
  `num_ctx`-defaulten 16384 är **Beslut 50** (förhindrar tyst trunkering;
  dokumenterat i `OllamaProvider`-docstring).
- **Provider-abstraktion** — `LLMProvider`-protokoll (`provider.py`,
  `LLMProviderError`). Tre implementationer: `OllamaProvider` (produktion),
  `GeminiProvider` (icke-produktion), `AnthropicProvider` (icke-produktion).
  Backend väljs runtime via miljövariabeln `LLM_PROVIDER`
  (`ollama` | `gemini` | `anthropic`, default `ollama`) i
  `gdpr_classifier/config.py:get_llm_provider`.
- **Modeller (Ollama):**
  - `qwen3:14b` — **nuvarande** produktions-/utvärderingsmodell. Default i
    `run_evaluation.py` (`AEGIS_MODEL`-env, default `qwen3:14b`), hårdkodad i
    `demo/callbacks.py` (`get_llm_provider("qwen3:14b")`). **Beslut 59.**
  - `qwen2.5:7b` — iteration 2:s slutmodell och tidig iteration 3 (många
    snapshots i `demo/snapshots/` och `demo/snapshot_descriptions.py`).
    Modellbytet `qwen2.5:7b` → `qwen3:14b` är **Beslut 59** (I-7-proben).
- **Molnmodell (probe):** `claude-opus-4-7` — default i `AnthropicProvider`.
  Använd endast för en intressentönskad jämförelse mot en större molnmodell
  (Beslut 60). Gemini har ingen default-modell (anroparen måste välja explicit).
- **Miljökonfiguration:** `.env.example` dokumenterar `LLM_PROVIDER`,
  `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, valfri `OLLAMA_ENDPOINT`. En andra
  modellväljare `AEGIS_MODEL` finns i `run_evaluation.py` och
  `scripts/build_demo_snapshot.py`.

### 2.5 Aggregator och core

Inga tredjepartsberoenden. Endast Python-stdlib: `dataclasses` (+ `replace`),
`enum`, `itertools` (`combinations`), `collections` (`defaultdict`, `Counter`),
`math`, `re`, `typing` (`Protocol`, `runtime_checkable`, `Literal`,
`TYPE_CHECKING`), `logging`. `Layer`- och `Recognizer`-protokollen ger
utbytbarhet utan stdlib-externa beroenden.

### 2.6 Evaluation

Inga ML-bibliotek. Mätvärden (precision/recall/F1, confusion matrix,
dimension-stats) är handimplementerade i ren Python (`evaluation/metrics.py`,
`evaluation/confusion_matrix.py`, `evaluation/runner.py`, `evaluation/report.py`).
Datamodell via `dataclasses`; dataset läses som JSON via stdlib `json`
(`evaluation/dataset/loader.py`). `scripts/export_candidates_to_csv.py` använder
stdlib `csv`. Test via `pytest`. **Ingen NumPy/pandas/scikit-learn** importeras i
projektkoden (NumPy finns endast transitivt under `.venv` som spaCy-beroende).

### 2.7 Demo

- **Dash** — `pyproject.toml` extra `demo = ["dash>=2.0"]`. Lokalt observerad:
  4.1.0. Importeras i `demo/app.py`, `demo/layout.py`, `demo/callbacks.py`
  (`from dash import Dash, Input, Output, State, callback, ctx, dash_table,
  dcc, html`).
- **Plotly** — Dash drar in Plotly transitivt, men **ingen projektkod
  importerar `plotly` direkt** (helrepo-grep: endast `from dash import …`).
  Visualisering sker via Dashs egna komponenter; Plotly är därmed en transitiv,
  ej direkt använd, dependency.
- Snapshot-arkitektur: demon läser förgenererade JSON-snapshots
  (`demo/snapshots/`, byggda av `scripts/build_demo_snapshot.py`), inte live
  pipeline-körning vid uppstart.

### 2.8 Utvecklingsverktyg

- **pytest** — `pyproject.toml` extra `dev = ["pytest>=8.0"]`. Lokalt
  observerad: 9.0.3. Ingen `pytest.ini`/`conftest`-konfiguration utöver paketets
  egen struktur; ingen `tox`.
- **Ruff** — används som konvention (kod innehåller Ruff-specifika
  `# noqa: PLC0415` och `# noqa: E402`), men finns **inte** i `pyproject.toml`,
  har **ingen** `[tool.ruff]`-sektion eller `ruff.toml`, och var **inte
  installerad** i venv på utvecklingsmaskinen
  (`docs/iteration_3_implementation.md:586`).
- **mypy** — `docs/arkitektur.md`/SSOT och I-5-sessionen nämner
  "mypy-verifierbarhet" som motiv för pattern matching, men mypy finns **inte**
  i `pyproject.toml`, har **ingen** `[tool.mypy]`/`mypy.ini`, och var **inte
  installerad** i venv (`iteration_3_implementation.md:586`). Ingen
  `pyrightconfig.json`.
- **Ingen pre-commit, ingen tox, ingen black/flake8/isort** (helrepo-sökning
  utanför `.venv`).

### 2.9 Infrastruktur

- **Git** — versionshantering. `main` är default- och PR-bas. Initial commit
  `d977b37` 2026-04-17.
- **GitHub** — kodvärd (`origin`), pull requests (t.ex. PR #141, #143).
- **GitHub Projects** — issue- och projektstyrning i nio-stegs-loopen
  (`CLAUDE.md` §4, `docs/arbetsflode.md`). Process, inte kod.
- **Ingen CI/CD** — ingen `.github/workflows/`. **Ingen containerisering** —
  ingen `Dockerfile`. **Ingen `Makefile`.**
- `.claude/settings.json` finns men innehåller endast Claude Code-permissions
  och `additionalDirectories` — inga hooks, ingen automation.

### 2.10 AI-utvecklingsverktyg

Egen kategori per spec-regel 3. Dessa dokumenteras även i metodens
AI-användningsavsnitt (`CLAUDE.md` §9) men hör tekniskt hemma här som verktyg.
Listan är inte uttömmande och förändras under projektets gång.

- **Claude Code (Opus 4.7)** — implementations-agent från iteration 2 och framåt
  (`CLAUDE.md` §9). Iteration 3:s sessionsposter är genomgående märkta
  "Claude Code (Opus 4.7)" fr.o.m. 2026-05-11.
- **Claude Web** — arkitekt-agent i separat chattsession: arkitektur, planering,
  akademisk text (`CLAUDE.md` §9).
- **NotebookLM** — källextraktion ur litteratur.
- **Cursor (Opus)** — implementations-agent under **iteration 1** (sessioner
  2026-04-18 → 2026-04-21 i `docs/iteration_1_demoforberedelse.md`). Ersatt av
  Claude Code (`docs/iteration_3_implementation.md:178`).
- **Antigravity / Gemini** — Johannas iteration 1-spår (Session 2026-04-18,
  `docs/iteration_1_demoforberedelse.md:470`).

> Terminologinotering åt teamet: `CLAUDE.md` §9 säger Claude Code från iteration
> 2; `iteration_3_implementation.md:178` formulerar det som skillnaden mot
> iteration 1. Verifiera själva exakt iteration-2-gränsen i Loggboken innan ni
> formulerar detta i rapporten — sessionsposter i iteration 1 visar Cursor, och
> iteration 3 visar Claude Code; iteration 2:s agent är inte entydigt spårbar i
> sessionsposterna.

---

## 3. Faktarutor per verktyg

> Format: namn · version (pyproject + lokalt observerad) · var det används ·
> introducerat (commit + datum) · källa till val · konkurrenter (om
> dokumenterade).

### Python
- **Version:** `requires-python >=3.11` (pyproject). Runtime ej pinnad till
  patch; ingen `.python-version`.
- **Används:** hela artefakten.
- **Introducerat:** Initial commit `d977b37` 2026-04-17; `requires-python` i
  pyproject `b4738ec` 2026-04-17.
- **Källa till val:** implementationsval utan formellt beslut (default-språk för
  projektet).
- **Konkurrenter:** inga dokumenterade.

### `venv` (virtuell miljö)
- **Version:** stdlib, följer Python.
- **Används:** utvecklings-/körmiljö (`.venv/`, git-ignorerad).
- **Introducerat:** setup-steg (README), ej kodspårbart.
- **Källa till val:** implementationsval utan formellt beslut.
- **Konkurrenter:** Conda/Poetry/uv/Pipenv — inga använda, inga dokumenterade.

### `re` (stdlib regex)
- **Version:** stdlib, följer Python.
- **Används:** alla Lager 1-recognizers; `CombinationLayer`; `prompts/loader.py`;
  flera scripts.
- **Introducerat:** `b4738ec` 2026-04-17.
- **Källa till val:** implementationsval utan formellt beslut (default).
- **Konkurrenter:** externt `regex`-paket — ej använt.

### Luhn (handskriven checksumma)
- **Version:** egen implementation, ingen version.
- **Används:** `gdpr_classifier/layers/pattern/recognizers/betalkort.py`,
  `personnummer.py`.
- **Introducerat:** `b4738ec` 2026-04-17 (med Lager 1).
- **Källa till val:** implementationsval utan formellt beslut. Algoritmvalet är
  trivialt; det motiveringsvärda är *att* personnummer/betalkort detekteras med
  checksumma — det ligger i arkitektur-SSOT, inte i biblioteksvalet.
- **Konkurrenter:** tredjeparts `python-stdnum` e.d. — ej använt, ej dokumenterat.

### spaCy
- **Version:** `>=3.7` (pyproject `nlp`) · 3.8.14 (lokalt observerad).
- **Används:** `gdpr_classifier/layers/entity/entity_layer.py` (`import spacy`,
  `spacy.load`).
- **Introducerat:** import `b4738ec` 2026-04-17; `nlp`-extra `3fe6db5`
  2026-04-18.
- **Källa till val:** biblioteksvalet är implementationsval utan formellt
  beslut; **modellvalet** (`sv_core_news_lg`) är motiveringsvärt (svensk NER).
- **Konkurrenter:** inga dokumenterade i repo (Stanza, KB-BERT m.fl. ej nämnda).

### `sv_core_news_lg` (spaCy-modell)
- **Version:** ej i pyproject; **3.8.0** lokalt observerad
  (`.venv/.../sv_core_news_lg-3.8.0`). Laddas separat via
  `python -m spacy download sv_core_news_lg`.
- **Används:** Lager 2 `EntityLayer` (default `model_name`).
- **Introducerat:** `b4738ec` 2026-04-17 (default i `entity_layer.py`).
- **Källa till val:** **motiveringsvärt** — val av svensk large-modell.
  Formellt Loggboks-beslut: ej entydigt identifierat i kod/sessionsposter;
  verifiera i Loggboken iteration 1.
- **Konkurrenter:** `sv_core_news_sm/md` (mindre spaCy-varianter) — inte
  dokumenterat övervägda i repo.

### Ollama
- **Version:** extern binär/tjänst, ej versionspinnad. HTTP-API
  `localhost:11434`.
- **Används:** Lager 3/4 via `OllamaProvider` (produktionsprovider).
- **Introducerat:** `5312490` 2026-04-30 (med `LLMProvider`-abstraktionen).
- **Källa till val:** **Beslut 17** (lokal LLM som primär provider; GDPR-motiv:
  ingen tredjelandsöverföring enligt kap. V). `num_ctx=16384`-defaulten:
  **Beslut 50**.
- **Konkurrenter:** moln-LLM (Gemini/Anthropic) — implementerade som
  icke-produktionsalternativ via samma abstraktion (Beslut 17).

### `requests`
- **Version:** `>=2.31` (pyproject `llm`) · 2.33.1 (lokalt).
- **Används:** `OllamaProvider` (HTTP POST), `scripts/build_demo_snapshot.py`,
  `scripts/run_i7d_baseline.py`, `scripts/demonstrations/stub_substitution.py`,
  `scripts/probe_llm_models.py`, `tests/unit/test_ollama_provider.py`.
- **Introducerat:** `5312490` 2026-04-30.
- **Källa till val:** implementationsval utan formellt beslut (default
  HTTP-bibliotek).
- **Konkurrenter:** `httpx`/stdlib `urllib` — ej dokumenterat övervägda.

### `google-genai`
- **Version:** `>=1.0` (pyproject `llm`) · 1.74.0 (lokalt).
- **Används:** `gdpr_classifier/layers/llm/gemini_provider.py` (lat import
  `import google.genai as genai`).
- **Introducerat:** `5312490` 2026-04-30.
- **Källa till val:** **Beslut 17** (utbytbar molnprovider; endast dev/test,
  GDPR kap. V-varning i modul-docstring).
- **Konkurrenter:** **dokumenterad** — legacy-paketet `google-generativeai`
  avvisades explicit i `gemini_provider.py` modul-docstring ("Do NOT use the
  legacy google-generativeai package").

### `anthropic`
- **Version:** `>=0.40` (pyproject `llm`) · 0.102.0 (lokalt).
- **Används:** `gdpr_classifier/layers/llm/anthropic_provider.py` (lat import
  `import anthropic`).
- **Introducerat:** `91a573d` 2026-05-17 ("feat(i7h): cloud model probe via
  AnthropicProvider; Beslut 60").
- **Källa till val:** **Beslut 60** (intressentönskad jämförelse mot en större
  molnmodell), under paraplyet **Beslut 17** (icke-produktion, GDPR kap.
  V-varning).
- **Status:** *implementerad, icke-produktion, behållen för framtida bruk eller
  reproducerbarhet av probe-resultat.* Skapad endast för att testa mot en större
  molnmodell efter intressentönskemål (se om det gjorde skillnad).
- **Konkurrenter:** OpenAI/övriga moln-SDK — ej dokumenterat övervägda.

### `GeminiProvider` (status-faktaruta)
- Mergad till `main` (`5312490` 2026-04-30). **Implementerad men ej i nuvarande
  produktionskonfiguration.** Användes under tidigt artefaktkonstruktionsarbete
  för att kunna testa mot en molnmodell när den lokala modellen inte kunde köras
  — fanns enbart av testningsskäl. Status: *implementerad, icke-produktion,
  behållen för framtida bruk eller reproducerbarhet av probe-resultat*
  (Beslut 17).

### PyYAML (`yaml`)
- **Version:** `>=6.0` (pyproject `llm`) · 6.0.3 (lokalt).
- **Används:** `gdpr_classifier/prompts/loader.py` (`import yaml`); prompt-filer
  `gdpr_classifier/prompts/{article9,combination}/v*.yaml`.
- **Introducerat:** `141aba1` 2026-04-30 ("prompt loading system with YAML
  validation").
- **Källa till val:** implementationsval utan formellt beslut (default
  YAML-bibliotek; valet att versionshantera prompter i YAML hör till
  prompt-loader-designen, inte biblioteksvalet).
- **Konkurrenter:** `ruamel.yaml`/JSON-prompter — ej dokumenterat övervägda.

### Dash
- **Version:** `>=2.0` (pyproject `demo`) · 4.1.0 (lokalt).
- **Används:** `demo/app.py`, `demo/layout.py`, `demo/callbacks.py`.
- **Introducerat:** `3fe6db5` 2026-04-18 ("Dash web interface for evaluation
  reporting").
- **Källa till val:** implementationsval utan formellt beslut.
- **Konkurrenter:** Streamlit/Flask/Gradio — ej dokumenterat övervägda.

### Plotly
- **Version:** ej direkt dep; transitiv via Dash.
- **Används:** **inte direkt** — ingen `import plotly` i projektkoden;
  visualisering sker via Dashs komponenter.
- **Introducerat:** transitivt med Dash `3fe6db5` 2026-04-18.
- **Källa till val:** n/a (transitiv).
- **Konkurrenter:** n/a.

### `pytest`
- **Version:** `>=8.0` (pyproject `dev`) · 9.0.3 (lokalt).
- **Används:** hela `tests/` (unit, integration, dataset, fixtures).
- **Introducerat:** dependency `b4738ec` 2026-04-17 (ursprungligen även i
  `dependencies`, flyttad till enbart `dev` i `8d2edae` 2026-04-17); första
  faktiska test `5e8aa39` 2026-04-18.
- **Källa till val:** implementationsval utan formellt beslut (default
  testramverk).
- **Konkurrenter:** stdlib `unittest` — används punktvis för mockning
  (`unittest.mock`), inte som ramverk.

### `setuptools`
- **Version:** `>=68` (build-system) · 82.0.1 (lokalt).
- **Används:** paket-build (`build-backend = "setuptools.build_meta"`).
- **Introducerat:** `b4738ec` 2026-04-17.
- **Källa till val:** implementationsval utan formellt beslut (default
  build-backend). **Upptäckt vid full repo-skanning** som explicit
  build-beroende (ej tidigare diskuterat, men trivialt default).
- **Konkurrenter:** Hatch/Flit/PDM — ej dokumenterat övervägda.

### `tiktoken`
- **Version:** **ej i pyproject**; lokalt installerad om närvarande.
- **Används:** `tools/measure_prompt_tokens.py` (`import tiktoken`) — engångs-
  mätverktyg för I-6 (num_ctx-utredning).
- **Introducerat:** `34731927` 2026-05-14 ("tools(i6): empirical token
  measurement for layer prompts").
- **Källa till val:** implementationsval utan formellt beslut.
- **Flagga:** **upptäckt vid full repo-skanning, ej tidigare diskuterat.**
  Odeklarerat beroende — verktyget fungerar bara om `tiktoken` installerats
  manuellt. Se sektion 5.
- **Konkurrenter:** `transformers`-tokenizer (används i samma fil som
  validering).

### `transformers`
- **Version:** **ej i pyproject**; lat/valfri import (`from transformers import
  AutoTokenizer  # type: ignore[import-not-found]`).
- **Används:** `tools/measure_prompt_tokens.py` (valideringsgren
  `validate_with_qwen`).
- **Introducerat:** `34731927` 2026-05-14.
- **Källa till val:** implementationsval utan formellt beslut.
- **Flagga:** **upptäckt vid full repo-skanning, ej tidigare diskuterat.**
  Frivilligt — koden hanterar `ImportError` och hoppar över valideringen. Se
  sektion 5.
- **Konkurrenter:** n/a.

### Ruff
- **Version:** ej i pyproject, ej konfigurerad, ej installerad i venv.
- **Används:** konvention — `# noqa: PLC0415` / `# noqa: E402` i koden indikerar
  avsedd Ruff-användning.
- **Introducerat:** aldrig införd som dependency.
- **Källa till val:** implementationsval utan formellt beslut.
- **Konkurrenter:** flake8/pylint — ej använda.

### mypy
- **Version:** ej i pyproject, ej konfigurerad, ej installerad i venv.
- **Används:** refererad som motiv ("mypy-verifierbarhet") i SSOT/I-5, men ingen
  faktisk konfiguration eller installation.
- **Introducerat:** aldrig införd som dependency.
- **Källa till val:** implementationsval utan formellt beslut.
- **Konkurrenter:** Pyright — ingen `pyrightconfig.json`.

### Git / GitHub / GitHub Projects
- **Version:** externa verktyg/tjänster, ej pinnade.
- **Används:** versionshantering, kodvärd, PR, issue-/projektstyrning
  (nio-stegs-loop).
- **Introducerat:** projektstart (Git initial commit `d977b37` 2026-04-17).
- **Källa till val:** implementationsval utan formellt beslut (default
  infrastruktur).
- **Konkurrenter:** inga dokumenterade.

### AI-utvecklingsverktyg (Claude Code, Claude Web, NotebookLM, Cursor, Antigravity/Gemini)
- **Version:** Claude Code = Opus 4.7; Cursor = Opus; övriga ej versions-spårade.
- **Används:** Claude Code = implementation iter 2→3; Claude Web = arkitekt-
  agent; NotebookLM = källextraktion; Cursor = implementation iter 1;
  Antigravity/Gemini = Johannas iter 1-spår.
- **Introducerat:** Cursor 2026-04-18 (iter 1); Claude Code fr.o.m. 2026-05-11
  i sessionsposterna (iter 3; CLAUDE.md anger iter 2 — verifiera i Loggboken).
- **Källa till val:** dokumenteras i metodens AI-användningsavsnitt med
  handledarens godkännande (`CLAUDE.md` §9); listan ej uttömmande.
- **Konkurrenter:** verktygen är delvis varandras alternativ (Cursor → Claude
  Code; Antigravity/Gemini parallellt i Johannas spår).

---

## 4. Motiveringsbehov i rapporten

"Behöver motiveras" = ett aktivt designval som bör försvaras i kapitel 4.
"Default-val" = standard/trivialt, behöver ingen försvar.

| Verktyg | Behöver motiveras i rapporten? | Kommentar |
|---|---|---|
| Python | Nej | Default-språk. |
| `venv` | Nej | Default. |
| `re` (stdlib) | Nej | Default; "regex" som teknik behöver ingen motivering. |
| Luhn (handskriven) | Nej för algoritmen | *Att* checksummavalidera personnummer/betalkort motiveras i arkitektur-SSOT, inte här. |
| spaCy (bibliotek) | Nej | Standard-NLP-bibliotek. |
| **`sv_core_news_lg`** | **Ja** | Modellval (svensk large-NER) — kärnan i Lager 2:s prestanda. |
| **Ollama (LLM-runtime)** | **Ja** | Lokal LLM-runtime, GDPR-motiverad (Beslut 17). |
| `requests` | Nej | Default HTTP-bibliotek. |
| **`google-genai`** | **Ja** | Molnprovider, GDPR-känsligt (Beslut 17); icke-produktion. |
| **`anthropic`** | **Ja** | Molnprovider, intressentönskad probe (Beslut 60); icke-produktion. |
| PyYAML | Nej | Default; prompt-loader-designen motiveras separat, ej biblioteket. |
| Dash | Svag/valfri | Implementationsval; kan kort nämnas men inget kärnval. |
| Plotly | Nej | Transitiv, ej direkt använd. |
| `pytest` | Nej | Default testramverk. |
| `setuptools` | Nej | Default build-backend. |
| `tiktoken` / `transformers` | Nej (men deklarera) | Engångs-mätverktyg; bör nämnas som odeklarerat verktygsberoende, ej försvaras som val. |
| Ruff / mypy | Nej | Avsedd kvalitetskonvention; notera att de inte formaliserats/installerats. |
| Git/GitHub/Projects | Nej | Default infrastruktur. |
| **Modellbyte qwen2.5:7b → qwen3:14b** | **Ja** | Beslut 59 — central iteration 3-förändring, måste motiveras. |
| AI-utvecklingsverktyg | Hanteras i metodens AI-avsnitt | Här endast som verktygsinventering. |

---

## 5. Död / kvarvarande kod och dependency-anomalier

Per spec-regel 6 — verktyg/kod som finns men inte används normalt, eller
dependency-avvikelser:

1. **`tiktoken` och `transformers` — odeklarerade beroenden.** Används endast i
   `tools/measure_prompt_tokens.py` (I-6 engångs-token-mätning, commit
   `34731927` 2026-05-14). **Står inte i `pyproject.toml`.** Verktyget kraschar
   utan manuell `pip install tiktoken`; `transformers` är lat/valfri (ImportError
   hanteras). **Upptäckt vid full repo-skanning, ej tidigare diskuterat.**
2. **`[all]`-extra är ofullständig.** `pyproject.toml` har
   `all = ["dash>=2.0", "spacy>=3.7"]` — den **utelämnar `llm` och `dev`**.
   `CLAUDE.md` §10 säger `pip install -e ".[all]"` (skulle sakna `llm`/`dev`),
   medan `README.md` rad 23 säger `pip install -e ".[all,llm,demo,nlp,dev]"`
   (komplett). Inkonsekvens mellan CLAUDE.md och README — flaggas för teamet.
3. **`GeminiProvider` / `AnthropicProvider` — implementerade, icke-produktion.**
   Båda mergade till `main` men ej i produktionskonfigurationen
   (`LLM_PROVIDER=ollama` default). Inte död kod — avsiktligt behållna för
   framtida bruk/reproducerbarhet av probe-resultat (Beslut 17, Beslut 60). Se
   sektion 0 och 3.
4. **`Plotly`** — transitiv via Dash men ingen direktimport i projektkoden.
   Inte ett aktivt verktygsval.
5. **`gdpr_classifier/layers/context/context_layer.py`** — `ContextLayer`
   existerar och importeras i `tests/integration/test_end_to_end.py`, men
   SSOT/`CLAUDE.md` beskriver Lager 3/4 som `Article9Layer`/`CombinationLayer`.
   Möjligen övergångs-/legacykod. *Observation, ej verktyg* — verifiera status
   med teamet (utanför ren teknisk-stack-scope, noteras för fullständighet).
6. **`setuptools` som explicit build-krav** — trivialt default, men togs ej upp
   i specifikationen; noteras som upptäckt vid skanning.
7. **pyproject `version = "0.1.0"`** trots iterationsstatus `v0.3.0-dev`
   (`CLAUDE.md` §7). Paketversionen har inte uppdaterats — flaggas (påverkar
   inte stacken men är en versions-anomali värd att nämna).

---

## 6. Tidslinje — när stacken växte

Kronologisk sammanfattning. Datum = commit-datum (`git log`, `%ad`).

### Iteration 1 — v0.1.x (2026-04-17 → ~2026-04-21)

- **2026-04-17** `d977b37` Initial commit. `b4738ec` "mapstructure and
  environment setup": Python `>=3.11`, `pyproject.toml`, `pytest` (dep),
  Lager 1 (stdlib `re` + handskriven Luhn), Lager 2 (`spacy` import +
  `sv_core_news_lg`). `8d2edae` flyttar `pytest` till enbart `dev`-extra.
- **2026-04-18** `3fe6db5` Dash-demo införd (`demo = ["dash>=2.0"]`,
  `nlp = ["spacy>=3.7"]`, `all`). `5e8aa39` första end-to-end-test (pytest i
  faktisk användning). `054c35d` `demo*` läggs till i paketdiscovery.
- **Implementations-agent:** Cursor (Opus). Johannas spår: Antigravity.
  Sessioner 2026-04-18 → 2026-04-21
  (`docs/iteration_1_demoforberedelse.md`).

### Iteration 2 — v0.2.0 (avslutad 2026-05-04)

- **2026-04-30** `5312490` `LLMProvider`-abstraktion + `OllamaProvider` +
  `GeminiProvider`; `llm = ["requests>=2.31", "google-genai>=1.0"]` (Beslut 17).
  `141aba1` prompt-loader med YAML-validering; `pyyaml>=6.0` läggs till `llm`.
- **2026-05-01** `73ca5d4` `Article9Layer` (Lager 3). `0a0aaaa`
  `CombinationLayer` (Lager 4).
- **Modell:** `qwen2.5:7b` (iteration 2:s slutmodell). Slutmätvärden (per
  `CLAUDE.md` §7): Precision 64.00 %, Recall 89.27 %, F1 74.55 %.

### Iteration 3 — v0.3.0-dev (2026-05-11 → nuvarande `main`-tillstånd)

- **2026-05-13/14** I-5 (core/aggregator pattern matching) och I-6: num_ctx-fix
  (`OllamaProvider` `num_ctx=16384`, Beslut 50). `34731927` 2026-05-14
  `tools/measure_prompt_tokens.py` (`tiktoken` + valfri `transformers` —
  odeklarerade beroenden).
- **2026-05-15** I-7-prob: jämförande körningar `qwen2.5:7b` vs `qwen3:14b`
  (snapshots i `demo/snapshots/`).
- **Modellbyte → `qwen3:14b`** som produktions-/utvärderingsmodell (Beslut 59;
  default i `run_evaluation.py` och `demo/callbacks.py`).
- **2026-05-17** `91a573d` `AnthropicProvider` + `anthropic>=0.40` i `llm`-extra
  (Beslut 60 — intressentönskad molnjämförelse, icke-produktion).
- Probe-arbetet (I-7 + #107) mergat till `main` via PR #141.
  `main`-HEAD `21b9417`, 2026-05-18.
- **Implementations-agent:** Claude Code (Opus 4.7).

### Sammanfattande stack-tillväxt

| Iteration | Tillkommande stack |
|---|---|
| Iter 1 | Python ≥3.11, stdlib-pipeline (`re` + Luhn), `pytest`, `setuptools`, spaCy + `sv_core_news_lg`, Dash |
| Iter 2 | `LLMProvider`-abstraktion, Ollama + `requests`, `google-genai` (Gemini), PyYAML, Lager 3/4 (`qwen2.5:7b`) |
| Iter 3 | `tiktoken`/`transformers` (mätverktyg), modellbyte → `qwen3:14b`, `anthropic` (cloud-probe) |

---

*Underlag genererat 2026-05-18 via full repo-skanning på `main` (HEAD
`21b9417`). Versioner märkta "lokalt" är observerade i `.venv` dist-info och är
inte auktoritativa (repot saknar lock-fil). Inga befintliga filer ändrades vid
framtagningen av detta dokument utöver sessionspost i
`docs/iteration_3_implementation.md`.*
