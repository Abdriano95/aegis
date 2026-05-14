# Iteration 3: num_ctx-fix och omkörning av iteration 2:s LLM-baserade utvärdering

**Datum:** 2026-05-14
**Issue:** [#106](https://github.com/Abdriano95/aegis/issues/106) (I-6)
**Beslut:** Beslut 50 (Loggbok iteration 3, Google Docs)
**Status:** Genomförd. Ny baslinje etablerad.

## Bakgrund

Token-mätningen i [iteration_3_token_measurement.md](iteration_3_token_measurement.md) (commit `3473192`) bekräftade utfall C: 100 % av iteration 2:s LLM-prompter ligger över Ollamas implicita `num_ctx=4096`-default. Article9Layer-prompter mätte 6015–6117 effective tokens (47–49 % över), CombinationLayer 4397–4454 effective tokens (7–9 % över). Beslut 50 fastställde explicit `num_ctx=16384` i `OllamaProvider` och omkörning av iteration 2:s LLM-baserade utvärdering mot fixad provider.

## Implementation

Två kodändringar i [gdpr_classifier/layers/llm/ollama_provider.py](../gdpr_classifier/layers/llm/ollama_provider.py):

1. Ny konstruktor-parameter `num_ctx: int = 16384` med dokumentation i Args-docstring.
2. `num_ctx`-värdet propageras till payload-`options`-dict tillsammans med `temperature`.

Diff-utdrag:

```python
def __init__(
    self,
    model_name: str,
    endpoint: str = "http://localhost:11434",
    temperature: float = 0.0,
    timeout: int = 300,
    num_ctx: int = 16384,  # nytt
) -> None:
    ...
    self._num_ctx = num_ctx
```

```python
"options": {
    "temperature": self._temperature,
    "num_ctx": self._num_ctx,  # nytt
},
```

Två nya unit-tester i [tests/unit/test_ollama_provider.py](../tests/unit/test_ollama_provider.py):

- `test_num_ctx_default_sent_in_options` — verifierar att default 16384 hamnar i payload när inget anges.
- `test_custom_num_ctx_forwarded` — verifierar att custom-värde propageras.

## Verifiering av fix

Payload-inspektion via mockad `requests.post` är den auktoritativa verifieringen. Båda nya unit-tester passerar (totalt 16/16 i suiten):

```
tests/unit/test_ollama_provider.py::test_num_ctx_default_sent_in_options PASSED
tests/unit/test_ollama_provider.py::test_custom_num_ctx_forwarded       PASSED
```

Ad-hoc REPL-bekräftelse:

```
OK: payload[options] = {'temperature': 0.0, 'num_ctx': 16384}
```

**Notering om `ollama ps`:** Användaren ändrade Ollama Desktops globala `num_ctx`-default från 4096 till 16384 manuellt samma datum. Det betyder att `ollama ps`-kolumnen `CONTEXT` skulle visa 16384 oavsett om provider-fixen är på plats — Desktop-defaulten överrider när inget program explicit sätter `num_ctx`. Därför är `ollama ps` inte längre en diskriminerande check; payload-inspektionen är beviset på att provider sätter värdet själv.

## Omkörningsresultat

Snapshot genererad via `python scripts/build_demo_snapshot.py --output iteration_3_post_num_ctx_fix.json` (defaults: `--article9-version v5`, `--combination-version v5`). Apples-to-apples mot pre-fix-baslinjen som har samma prompt-versioner i sin metadata.

**Pre-fix-snapshot:** [demo/snapshots/pre_num_ctx_fix/iteration_3_post_I5_fixup_TRUNCATED.json](../demo/snapshots/pre_num_ctx_fix/iteration_3_post_I5_fixup_TRUNCATED.json) (kopia av `iteration_3_post_I5_fixup.json` från commit `00e1e666`, 2026-05-14T06:27).

**Post-fix-snapshot:** [demo/snapshots/iteration_3_post_num_ctx_fix.json](../demo/snapshots/iteration_3_post_num_ctx_fix.json) (genererad 2026-05-14T19:36, commit `2f067ee9`).

### Full pipeline-baslinje (totalt)

| Metric | Pre-fix (trunkerad) | Post-fix | Delta |
|---|---|---|---|
| TP | 213 | 213 | +0 |
| FP | 90 | 91 | +1 |
| FN | 20 | 20 | +0 |
| Precision | 70.30 % | 70.07 % | −0.23 pp |
| Recall | 91.42 % | 91.42 % | ±0 |
| F1 | 79.48 % | 79.33 % | −0.15 pp |

Aggregat-nivå nästan oförändrad. Skillnaden är 1 extra FP totalt.

### Per layer

| Layer | Pre TP/FP/FN | Post TP/FP/FN | ΔTP | ΔFP | ΔFN | Δ F1 |
|---|---|---|---|---|---|---|
| pattern | 68/0/0 | 68/0/0 | +0 | +0 | +0 | ±0 |
| entity | 45/36/0 | 46/35/0 | +1 | −1 | +0 | +0.0101 |
| article9 | 37/7/0 | 36/7/0 | −1 | +0 | +0 | −0.0022 |
| context | 63/47/0 | 63/49/0 | +0 | +2 | +0 | −0.0083 |

Pattern noll-delta som förväntat (ingen LLM). Entity-deltat (+1 TP, −1 FP) är oväntat eftersom Entity-lagret inte använder LLM — sannolikt en konsekvens av matcher-attribuering där överlappande fynd från olika lager kan rapporteras under olika `Finding.source`-prefix mellan körningar. Inte ett bug i num_ctx-fixen, men värt att notera för framtida diagnostik.

### Article9Layer (artikel 9-kategorier)

| Kategori | Pre TP/FP/FN | Post TP/FP/FN | ΔTP | ΔFP | ΔFN | Δ F1 |
|---|---|---|---|---|---|---|
| article9.halsodata | 6/4/1 | 5/4/2 | −1 | +0 | +1 | −0.0809 |
| article9.biometrisk_data | 6/1/0 | 6/1/0 | +0 | +0 | +0 | ±0 |
| article9.etniskt_ursprung | 0/1/0 | 0/1/0 | +0 | +0 | +0 | ±0 |
| article9.fackmedlemskap | 5/0/1 | 5/0/1 | +0 | +0 | +0 | ±0 |
| article9.genetisk_data | 5/0/2 | 5/0/2 | +0 | +0 | +0 | ±0 |
| article9.politisk_asikt | 6/0/0 | 6/0/0 | +0 | +0 | +0 | ±0 |
| article9.religios_overtygelse | 5/1/1 | 5/1/1 | +0 | +0 | +0 | ±0 |
| article9.sexuell_laggning | 4/0/2 | 4/0/2 | +0 | +0 | +0 | ±0 |

Endast `article9.halsodata` ändrades: −1 TP → +1 FN, F1 sjönk från 0.706 till 0.625. 7 av 8 article9-kategorier är oförändrade.

### CombinationLayer (context-kategorier)

| Kategori | Pre TP/FP/FN | Post TP/FP/FN | ΔTP | ΔFP | ΔFN | Δ F1 |
|---|---|---|---|---|---|---|
| context.kombination | 9/11/0 | 9/11/0 | +0 | +0 | +0 | ±0 |
| context.organisation | 23/19/4 | 23/19/4 | +0 | +0 | +0 | ±0 |
| context.plats | 14/3/0 | 14/4/0 | +0 | +1 | +0 | −0.0282 |
| context.yrke | 16/19/6 | 16/20/6 | +0 | +1 | +0 | −0.0097 |

Kombination och organisation oförändrade. Plats och yrke fick +1 FP vardera; F1 sjönk marginellt.

### Article4-kategorier (entity/pattern-baserade)

Tagg en kategori med icke-noll-delta för fullständighet:

| Kategori | Pre TP/FP/FN | Post TP/FP/FN | ΔTP | ΔFP | ΔFN | Δ F1 |
|---|---|---|---|---|---|---|
| article4.adress | 14/28/1 | 15/27/0 | +1 | −1 | −1 | +0.0351 |

Övriga article4.*-kategorier (betalkort, email, iban, namn, personnummer, telefonnummer) är oförändrade. `article4.adress` förbättring är troligen samma matcher-attribuering som drev entity-lagret-deltat.

## Tolkning

Den enklaste honest tolkningen: **trunkeringen visade sig ha minimal empirisk påverkan på iteration 2:s utvärdering** trots att 100 % av prompter var teoretiskt över 4096-gränsen.

Aggregat-precision sjönk med 0.23 pp, F1 med 0.15 pp. Det enskilt största kategori-deltat (`article9.halsodata` med F1 −0.08) representerar 1 av 7 testtexter i den kategorin — på den nivån är skillnaden inom rimligt brus från greedy-decode-stokastik (samma fenomen som dokumenterades i [iteration_3_threshold_calibration.md](iteration_3_threshold_calibration.md) sektion "lokal sanity-check"). De övriga ändringarna (context.plats, context.yrke, article4.adress) är ±1-räkningar.

Möjliga förklaringar till den lilla effekten:

1. **Trunkeringens placering** — Ollama trunkerar antagligen från prompt-början (system_prompt + few-shot examples). Den centrala instruktionen och input-texten ligger sist i prompten och överlever sannolikt även i en 4096-token-fönster. Token-mätningen kvantifierade hur mycket som låg över gränsen, inte vilken del som föll bort.
2. **Redundans i prompt** — Few-shot-exemplen i Article9Layer-prompten v5 kan vara informationsmässigt redundanta nog att förlust av några inte ändrar modellens beteende mätbart.
3. **Stokastik dominerar signalen** — Med temperature=0.0 är greedy decoding deterministisk per modell-laddning men inte över olika laddningscykler. Den lokala sanity-check 2026-05-14 visade Δ=±2/±8/±2 mellan körningar på samma kod, vilket är samma magnitud som num_ctx-fixens delta.

Inget av detta gör Beslut 50 felaktigt. Provider får inte vara beroende av Ollama Desktops globala client-default — det är ett DP3-symmetrikrav (utbytbar provider med konsistent effektivt kontextfönster). Empiriskt visade sig dock att den specifika manifestationen av trunkering i v0.3.0-iteration inte var märkbar i kategorierna vi mäter.

## Konsekvens för I-6

Den nya post-fix-baslinjen (213/91/20, F1=79.33 %) är **essentiellt samma** som pre-fix-baslinjen (213/90/20, F1=79.48 %). Fas 1-kalibreringen kan återupptas mot post-fix-baslinjen utan att tidigare delresultat blir meningslösa — variationen är inom samma magnitud som greedy-stokastiken som redan dokumenterats i threshold_calibration.md.

**Framtida arbete (ej fix-värt nu):** GeminiProvider konfigurerar inte explicit ett context-fönster i sin konstruktor. Detta är konsistent med Geminis transparent context-hantering (Google-API hanterar kontext automatiskt), men bryter formellt mot DP3-principen om symmetrisk provider-abstraktion. Om/när molnprovider-vägen blir primär bör Gemini-equivalenten utvärderas — för närvarande är det en accepterad asymmetri.

## Referenser

- [docs/iteration_3_token_measurement.md](iteration_3_token_measurement.md) — föregående sessions mätrapport (commit `3473192`)
- [docs/iteration_3_threshold_calibration.md](iteration_3_threshold_calibration.md) — fas 1-data och pausdokumentation
- [demo/snapshots/pre_num_ctx_fix/iteration_3_post_I5_fixup_TRUNCATED.json](../demo/snapshots/pre_num_ctx_fix/iteration_3_post_I5_fixup_TRUNCATED.json) — pre-fix-snapshot
- [demo/snapshots/iteration_3_post_num_ctx_fix.json](../demo/snapshots/iteration_3_post_num_ctx_fix.json) — post-fix-snapshot
- Beslut 50, Loggbok iteration 3 (Google Docs) — full motivering med alternativ och avvägningar
- [docs/arkitektur.md](arkitektur.md) § 6.1 — inline Beslut 50-sammanfattning för repo-spårbarhet
