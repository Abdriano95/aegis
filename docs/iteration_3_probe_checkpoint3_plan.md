# Plan — Checkpoint 3 av Issue #107 (parkerad, inte påbörjad)

> **Status 2026-05-15 (sent på kvällen):** Plan godkänd av arkitekten via Plan Mode. Körning 1 påbörjades men avbröts innan datapunkter samlades in (sömnpaus). Inga snapshots har persisterats. Återupptas nästa session från **Steg 1 (förflygskontroll)**.
>
> Källa: `.claude/plans/detta-r-utf-rande-av-crispy-lightning.md` (godkänd plan från Plan Mode).
>
> **Detta är inte en sessionspost.** Sessionsposter skrivs först när checkpoint 3 är genomförd. Denna fil är endast en parkering av den godkända planen.

---

## Context

Issue #107 (I-7) frågar om iteration 2:s prestandatak i Lager 3 (Article9Layer) och Lager 4 (CombinationLayer) är modellbundet eller uppgiftsbundet. Checkpoint 1 (smoke-test qwen3:14b, 2026-05-15) och checkpoint 2 (`--subset`-flagga + `AEGIS_MODEL`-env-var, commit `2815093`) är klara. Checkpoint 3 producerar den första jämförande datapunkten: båda modellerna körs mot samma article9-subset (52 texter) så att skillnader i utfall är attributerbara till modellen, inte till data eller pipeline-version.

Den befintliga snapshoten `demo/snapshots/iteration_3_post_num_ctx_fix.json` är en fullkörning över 159 texter och kan inte användas som apples-to-apples-jämförelse mot en subset-körning. Därför krävs två nya snapshots.

Arkitekten har explicit avgränsat scope: ingen sessionspost, ingen commit, ingen statustabell-uppdatering, ingen tolkning av siffrorna. Endast körning plus datarapport.

## Förutsättningar (verifierade i förflygskontroll 2026-05-15)

- [scripts/build_demo_snapshot.py:62](../scripts/build_demo_snapshot.py#L62) läser `AEGIS_MODEL` med default `qwen2.5:7b-instruct`.
- [scripts/build_demo_snapshot.py:70-75](../scripts/build_demo_snapshot.py#L70-L75) definierar `--subset article9` som kör `tests/data/iteration_2/article9_dataset.json`.
- [scripts/build_demo_snapshot.py:279-298](../scripts/build_demo_snapshot.py#L279-L298) skriver alla metadata-fält som verifieringen kräver, plus `report.total`, `report.per_category`, `report.per_layer`.
- [scripts/build_demo_snapshot.py:81-92](../scripts/build_demo_snapshot.py#L81-L92) (`check_ollama`) avbryter med tydligt fel om Ollama inte svarar på `http://localhost:11434`.
- `ollama list`: båda modellerna är lokala (`qwen3:14b` 9.3 GB, `qwen2.5:7b-instruct` 4.7 GB). Bekräftat denna session.
- `demo/snapshots/iteration_3_probe_qwen25_7b_article9.json` och `iteration_3_probe_qwen3_14b_article9.json` existerar inte. Bekräftat denna session.
- Article9-datasetet innehåller 52 texter (bekräftat via stdout från avbruten körning).
- Venv finns på `.venv/Scripts/python.exe`. PATH:ens `python` är Microsoft Store-stub och fungerar inte; använd venv-pythonen direkt.

## Tekniska upptäckter att hantera nästa session

1. **Bash-/PowerShell-tool-timeout är 10 min max** (`timeout: 600000`). En 15-25 min synkron körning träffar timeouten. Måste köras med `run_in_background: true`.
2. **Buffring i bakgrundsprocess:** PowerShell-tool i bakgrund flushade inte python-stdout under den korta avbrutna körningen. Använd `python -u` (unbuffered) så progress syns live i output-filen.
3. **Exit-kod 255** rapporterades från den första bakgrundsförsöket. Output-filen innehöll bara `START`-tidsstämpeln. Den synkrona testkörningen visade att skriptet faktiskt fungerar (Dataset loaded, pipeline created, processing texts) — så exit 255 kommer troligen från en buffer-/lifecycle-interaktion mellan PowerShell-bakgrund och python, inte från ett fel i skriptet. **Hypotes att testa nästa session:** kör med `python -u` så stdout flushas per rad. Om buggen kvarstår, fallback till en `Start-Process`-baserad approach eller använd Monitor-tool på output-filen.

## Steg

### Steg 1 — Förflygskontroll (snabb, lokal, läs-bara)

- `Invoke-RestMethod http://localhost:11434/api/tags` → båda modellerna närvarande.
- `Glob demo/snapshots/iteration_3_probe_*.json` → tomt. Om filerna finns, stoppa och be om instruktioner.
- `.\.venv\Scripts\python.exe -c "import requests, evaluation.report, gdpr_classifier; print('Imports OK')"` → bekräftar venv.

### Steg 2 — Körning 1: baslinjen qwen2.5:7b-instruct

```powershell
$env:AEGIS_MODEL = "qwen2.5:7b-instruct"
$t0 = Get-Date
".\.venv\Scripts\python.exe" -u scripts/build_demo_snapshot.py --subset article9 --output iteration_3_probe_qwen25_7b_article9.json
$t1 = Get-Date
"ELAPSED_SECONDS: $(($t1 - $t0).TotalSeconds)"
```

- Kör via PowerShell-tool med `run_in_background: true`.
- `python -u` är kritisk för progress-synlighet.
- Förväntad körtid 15-25 min.
- Output: `demo/snapshots/iteration_3_probe_qwen25_7b_article9.json` plus elapsed-sekunder.

### Steg 3 — Verifiering av körning 1

Läs snapshoten och kontrollera följande sju kriterier från arkitektens instruktion:

| Fält | Förväntat värde |
|---|---|
| `metadata.model` | `"qwen2.5:7b-instruct"` |
| `metadata.subset` | `"article9"` |
| `metadata.dataset.total_texts` | `52` |
| `metadata.dataset.article9_texts` | `52` |
| `metadata.dataset.iteration_1_texts` | `0` |
| `metadata.dataset.combination_texts` | `0` |
| `report.total` | innehåller fälten `tp`, `fp`, `fn`, `recall`, `precision`, `f1` |

Om något kriterium failar: STOPPA. Ingen körning 2. Rapportera felet och invänta instruktioner.

### Steg 4 — Körning 2: probe-kandidaten qwen3:14b

```powershell
$env:AEGIS_MODEL = "qwen3:14b"
$t0 = Get-Date
".\.venv\Scripts\python.exe" -u scripts/build_demo_snapshot.py --subset article9 --output iteration_3_probe_qwen3_14b_article9.json
$t1 = Get-Date
"ELAPSED_SECONDS: $(($t1 - $t0).TotalSeconds)"
```

- Förväntad körtid 20-35 min (14b är större).
- Notera om Ollama loggar CPU-fallback, OOM eller annat avvikande.

### Steg 5 — Verifiering av körning 2

Samma sju kriterier som steg 3, men med `metadata.model == "qwen3:14b"`.

### Steg 6 — Producera datarapport (text till konversationen, ingen fil)

Fem sektioner:

1. **Totalsiffror per modell** — jämförelsetabell över `report.total` (TP/FP/FN, Recall, Precision, F1 för båda modellerna).
2. **Per-kategori-jämförelse** för `article9.*`-kategorier (unionen av nycklar i båda `report.per_category`). Markera tydligt rader där `|F1_qwen3 − F1_qwen25| ≥ 10 procentenheter`.
3. **Per-lager-jämförelse** — `report.per_layer`-aggregat. Notera explicit om `pattern` eller `entity` skiljer sig mellan körningarna (de bör inte göra det — Lager 1 och 2 är LLM-fria).
4. **Latensobservation** — total körtid per snapshot.
5. **Varningar eller fel under körning** — kort sektion.

**Inga tolkningar.** Bara data.

## Kritiska filer

- [scripts/build_demo_snapshot.py](../scripts/build_demo_snapshot.py) — oförändrat.
- [tests/data/iteration_2/article9_dataset.json](../tests/data/iteration_2/article9_dataset.json) — oförändrat.
- `demo/snapshots/iteration_3_probe_qwen25_7b_article9.json` — produceras av körning 1.
- `demo/snapshots/iteration_3_probe_qwen3_14b_article9.json` — produceras av körning 2.

## Out of scope (explicit, från arkitektens prompt)

- Ingen sessionspost i `docs/iteration_3_implementation.md`.
- Ingen `git add` eller `git commit`.
- Ingen statustabell-uppdatering.
- Inga slutsatser eller tolkningar i rapporten — arkitekten gör det.
- Ingen ny kod, inga ändringar i `scripts/build_demo_snapshot.py` eller andra filer i repot.
- Ingen pipeline-parameter-justering (prompt-versioner, `num_ctx`, etc. — default från checkpoint 2 används oförändrade).

## Verifiering att uppdraget är klart

1. Båda snapshots finns under `demo/snapshots/` och passerar verifieringskriterierna.
2. Datarapporten (de fem sektionerna) är returnerad till användaren som text i konversationen.
3. Inga commits gjorda. Inga doc-filer ändrade (förutom denna parkerings-fil som kan raderas efter att checkpoint 3 är genomförd).

## Återupptag nästa session

När arbetet återupptas: läs denna fil för full kontext, börja med **Steg 1 (förflygskontroll)**. Använd **`python -u`** för bakgrundskörningar. Denna fil kan raderas när checkpoint 3 är genomförd och datarapporten är levererad till arkitekten.
