# I-6 token-mätning av Article9- och CombinationLayer-prompter

## Bakgrund

I-6 (Issue #106) är pausad efter 14/16 fas 1-körningar. Ett av två pausfynd var att `OllamaProvider.generate_json` inte sätter `num_ctx` explicit i payloaden, vilket innebär att Ollama defaultar till 4096 tokens totalt för prompt + output. Hypotesen är att CombinationLayer v5-prompten plus långa testtexter plus modellens reasoning/JSON-output kan ha trunkerats tyst under iteration 2 och iteration 3:s LLM-baserade utvärdering. Se `docs/iteration_3_threshold_calibration.md` § "Pausorsak: num_ctx-flagga (parallell analys)" för fullständig kontext.

Detta dokument rapporterar empirisk token-mätning av de prompter som pipelinen faktiskt skickar till modellen.

## Metod

Mätningen återanvänder pipelinens prompt-laddning (`gdpr_classifier.prompts.loader.load_prompt`) och pipelinens användarprompt-konstruktion verbatim (`{prompt.assembled_prompt}\n\nText att analysera:\n<<<\n{text}\n>>>\n`, exakt som `Article9Layer.detect` och `CombinationLayer.detect`).

- **Tokenizer:** tiktoken `cl100k_base` (primär). Token-mätning per text räknar `system_prompt` + `user_prompt` separat och summerar (motsvarar vad som konsumerar Ollamas kontextfönster).
- **Output-buffer:** 800 tokens (`effective_tokens = prompt_tokens + 800`).
- **Prompt-versioner:** Article9 `latest` (matchar `Article9Layer` default), Combination `v5` (matchar `CombinationLayer` iteration 3-pin).
- **Dataset:** se per-layer-sektion nedan. Text-index = position i JSON-array (0-indexerad), bevarad eftersom `load_dataset` itererar över `json.load`-listan i fil-ordning.
- **Utfallströsklar (uppgift 2 spec):** A = 0 över 4096 effective; B = 1-5% över ELLER kategori-max i [3800, 4096]; C = >5% över ELLER någon kategori har max > 4096.

## Resultat: Article9Layer

### Dataset: `tests/data/iteration_2/article9_dataset.json` (prompt latest)

Antal texter mätta: **52**.

| Statistik | Prompt tokens | Effective (prompt + buffer) |
|---|---|---|
| min | 5215 | 6015 |
| median | 5249 | 6049 |
| p75 | 5261 | 6061 |
| p90 | 5279 | 6079 |
| max | 5317 | 6117 |

Texter med effective > 4096: **52 (100.00%)**. Texter med effective > 3500 (varning): 52 (100.00%).

**Per-kategori-statistik:**

| Kategori | Antal texter | Max effective tokens | Antal > 4096 |
|---|---|---|---|
| `(no_category)` | 12 | 6055 | 12 |
| `article9.biometrisk_data` | 6 | 6087 | 6 |
| `article9.fackmedlemskap` | 6 | 6080 | 6 |
| `article9.genetisk_data` | 5 | 6117 | 5 |
| `article9.halsodata` | 5 | 6072 | 5 |
| `article9.politisk_asikt` | 6 | 6074 | 6 |
| `article9.religios_overtygelse` | 6 | 6075 | 6 |
| `article9.sexuell_laggning` | 6 | 6052 | 6 |

**Topp 5 längsta prompts (text-index i JSON-array):**

| Rang | Text-index | Prompt tokens | Effective tokens | Kategorier |
|---|---|---|---|---|
| 1 | 19 | 5317 | 6117 | article9.genetisk_data |
| 2 | 21 | 5307 | 6107 | article9.genetisk_data |
| 3 | 20 | 5295 | 6095 | article9.genetisk_data |
| 4 | 14 | 5287 | 6087 | article9.biometrisk_data |
| 5 | 17 | 5286 | 6086 | article9.genetisk_data |

### Dataset: `tests/data/iteration_3/article9_dataset.json` (prompt latest)

_Skippad: file does not exist: tests/data/iteration_3/article9_dataset.json_

### Dataset: `tests/data/iteration_1/test_dataset.json` (prompt latest)

_Skippad: no article9.* records in test_dataset.json (iteration_1 contains article4/context only)_

## Resultat: CombinationLayer

### Dataset: `tests/data/iteration_2/combination_dataset.json` (prompt v5)

Antal texter mätta: **27**.

| Statistik | Prompt tokens | Effective (prompt + buffer) |
|---|---|---|
| min | 3597 | 4397 |
| median | 3618 | 4418 |
| p75 | 3631 | 4431 |
| p90 | 3641 | 4441 |
| max | 3654 | 4454 |

Texter med effective > 4096: **27 (100.00%)**. Texter med effective > 3500 (varning): 27 (100.00%).

**Per-kategori-statistik:**

| Kategori | Antal texter | Max effective tokens | Antal > 4096 |
|---|---|---|---|
| `(no_category)` | 6 | 4443 | 6 |
| `context.kombination` | 9 | 4433 | 9 |
| `context.organisation` | 10 | 4433 | 10 |
| `context.plats` | 14 | 4454 | 14 |
| `context.yrke` | 20 | 4454 | 20 |

**Topp 5 längsta prompts (text-index i JSON-array):**

| Rang | Text-index | Prompt tokens | Effective tokens | Kategorier |
|---|---|---|---|---|
| 1 | 9 | 3654 | 4454 | context.plats, context.yrke |
| 2 | 13 | 3654 | 4454 | context.yrke |
| 3 | 16 | 3643 | 4443 | — |
| 4 | 14 | 3641 | 4441 | — |
| 5 | 12 | 3637 | 4437 | context.plats, context.yrke |

### Dataset: `tests/data/iteration_3/combination_dataset.json` (prompt v5)

_Skippad: file does not exist: tests/data/iteration_3/combination_dataset.json_

## Validering: tiktoken cl100k_base vs Qwen2.5-tokenizer

_Validering hoppades över: transformers not available: No module named 'transformers'_

## Slutsats

**Utfall C** — Trunkering bekräftad: 79/79 texter (100.00%) har effective_tokens > 4096; max kategorivärde 6117. num_ctx-fix krävs och iteration 2/3:s LLM-baserade utvärdering behöver köras om mot fixad provider.

Klassificeringen är automatiskt beräknad av `tools/measure_prompt_tokens.py` enligt spec'ens uppgift 2-trösklar och inte tolkad i efterhand.

Nästa beslut (num_ctx-fix och eventuell omkörning) tas av arkitekt-instans baserat på denna rapport.
