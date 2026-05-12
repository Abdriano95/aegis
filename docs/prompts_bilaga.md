# Prompts-bilaga

> Versionsspårad katalog över promptartefakter i gdpr_classifier. Varje post
> dokumenterar en YAML-prompt med datum, kommitthash, ändringssammanfattning och
> metodologiska källor. Bilagans syfte är spårbarhet mellan rapportens textkapitel
> och de exakta promptversioner som genererade rapporterade mätvärden.

Konventionen för bilagan är minimal och följer prompt-konstruktionsmetoden i
[`iteration_2_implementation.md`](iteration_2_implementation.md) (I-11): metadata
i YAML-filen är källan; denna bilaga är registret som länkar promptversion till
issue, datum, kommitthash och empiriskt utfall. Retroaktiva poster för historiska
versioner (v1-v4) kan fyllas i av framtida issues om så önskas.

---

## CombinationLayer

### v5 (aktuell)

- **Fil:** [`gdpr_classifier/prompts/combination/v5.yaml`](../gdpr_classifier/prompts/combination/v5.yaml)
- **Datum:** 2026-05-12
- **Kommitthash:** b1d061abc4335ff7c9f084e0bd2ad4d199c59838
- **Iteration:** 3 / v0.3.0-dev
- **Issue:** [#101](https://github.com/Abdriano95/aegis/issues/101) (I-1)
- **Designbeslut:** Beslut 42 (Loggbok iteration 3)
- **Ändring mot v4:**
  - Negativa exempel utökade med verb- och passivkonstruktioner verbatim från
    FP-rotorsaksanalysen 2026-05-04: "leddes av", "protokollfördes av",
    "eskaleras till"
  - ABSOLUT FÖRBUD-stycket om personnamn förstärkt med konkreta empiriska
    fall ("Karin Holm", "Lars Berg") och uttryckligt tillägg att personnamn
    inte får extraheras även när kontexten antyder yrkesroll
  - Två empiriskt identifierade organisationshallucineringsmönster från
    iteration 2:s FP-data tillagda i organisations-definitionen:
    - E-postadresser och e-postdomäner ("ekonomi@foretaget.se",
      "exempel.com", "no-reply@bolaget.se") - dessa hanteras av Lager 1
    - Avdelningar och delarbetsplatser utan eget företagsnamn
      ("Bokningsavdelningen", "IT-avdelningen", "huvudkontoret",
      "vårt kontor", "ett privat företag", "HR-notat", "fabriken i Borås")
  - Två nya negativa exempel tillagda i `examples`-sektionen som täcker
    verb-/passiv-fallet respektive e-post-/avdelnings-fallet (båda visar
    `individual_signals: []` och `is_identifiable: false`)
  - `reasoning_instructions` steg 1 och 2 utökade med pekare till de nya
    anti-mönstren utan duplicering av textmängd
  - `system_prompt`, `context` och `output_format` bevarade ordagrant från v4
- **Källcitat:** Liu et al. (2023), Brown et al. (2020), Wei et al. (2022),
  Karras et al. (2025)
- **Snapshots:**
  - [`demo/snapshots/iteration_3_baseline_v4_reproduction.json`](../demo/snapshots/iteration_3_baseline_v4_reproduction.json) - same-session
    v4-reproduktion på rebasad bas (innehåller I-2 PR #124 och I-3 PR #125)
  - [`demo/snapshots/iteration_3_baseline_post_I1.json`](../demo/snapshots/iteration_3_baseline_post_I1.json) - post-I-1-snapshot
- **Empiriskt utfall (qwen2.5:7b-instruct, 159 texter, 2026-05-12, post-rebase
  på `origin/main` HEAD 47c1f92):** Jämförelse mot v4-reproduktion i samma
  session på samma rebasade kodbas.
  - `context.yrke`: FP 23 → 20 (-3, -13.0 procent), recall bevarad 72.73
    procent, precision 41.03 → 44.44 procent, F1 52.46 → 55.17 procent
  - `context.organisation`: FP 25 → 19 (-6, -24.0 procent), recall bevarad
    85.19 procent, precision 47.92 → 54.76 procent, F1 61.33 → 66.67 procent
  - `context.plats` (sidoeffekt): FP 7 → 4 (-3, -43 procent), recall 100
    procent bevarad
  - `article4.adress` (sidoeffekt): recall förbättrad 93.33 → 100 procent
    (FN 1 → 0); FP 28 → 27 (-1)
  - Total: FP 99 → 91 (-8, -8.1 procent), recall 90.13 → 91.42 procent
    (+1.29 pp), precision 67.96 → 70.07 procent, F1 77.49 → 79.33 procent
  - v4-reproduktionen ligger 18 FP under iteration 2:s baseline (117 FP) och
    inom 2 FP från Johannas committade post-I-3-baseline (97 FP), vilket
    bekräftar att I-2 + I-3 ger den förväntade FP-reduktionen. Full sessions-
    data, inkl. baseline-anomali-flagga för pre-rebase-mätningen, i
    [`docs/iteration_3_implementation.md`](iteration_3_implementation.md).

### v1-v4 (historiska)

Versionerna v1 till v4 är arkiverade som YAML-filer under
[`gdpr_classifier/prompts/combination/`](../gdpr_classifier/prompts/combination/).
Versionsmetadata och `notes`-fält i respektive YAML dokumenterar de inkrementella
ändringarna. Retroaktiva bilagepostar kan tillfogas av framtida issue om
spårbarheten kräver det utöver kodhistoriken.

---

## Article9Layer

### v6 (experimentell, ej aktiv prompt)

- **Fil:** [`gdpr_classifier/prompts/article9/v6.yaml`](../gdpr_classifier/prompts/article9/v6.yaml)
- **Datum:** 2026-05-12
- **Kommitthash:** d500b950b76fc64ac11eef8f52c94ae67ed5ccac
- **Iteration:** 3 / v0.3.0-dev
- **Issue:** [#104](https://github.com/Abdriano95/aegis/issues/104) (I-4)
- **Designbeslut:** Beslut 48 (Loggbok iteration 3) - rollback. Tidigare designintention enligt Beslut 33 (Loggbok iteration 2) och Beslut 44 (Loggbok iteration 3, prompt-konstruktionsmetod).
- **Designintention (vad v6 skulle uppnå):** Per Beslut 33 utpekade iteration 2:s utvärdering tre Article9Layer-kategorier som underpresterande: `halsodata` (vaga formuleringar triggade FP), `etniskt_ursprung` (nordeuropeiska personnamn felklassades som etnisk markör), `religios_overtygelse` (implicit kristet firande missades i recall). v6 förstärkte negativa exempel för halsodata, lade till nordeuropeiska namn som negativa exempel för etniskt_ursprung, och introducerade positiva exempel för implicit kristet firande (julotta, dop, konfirmation) i religios_overtygelse. Reasoning_instructions utökades med kort steg-för-steg-resoning per Wei et al. (2022).
- **Empiriskt utfall (qwen2.5:7b-instruct, 159 texter, 2026-05-12, same-session jämförelse mot v5-reproduktion på commit `164a6fe`):**

  | Kategori | v5-reproduktion TP/FP/FN | v6 TP/FP/FN | ΔFP | ΔRecall pp |
  |---|---|---|---|---|
  | article9.halsodata | 6/4/1 | 7/5/0 | +1 | +14.3 |
  | article9.etniskt_ursprung | 0/1/0 | 0/0/0 | -1 | 0 |
  | article9.religios_overtygelse | 5/1/1 | 6/5/0 | +4 | +16.7 |
  | article9.sexuell_laggning (sidoeffekt) | 4/0/2 | 2/0/4 | 0 | -33.3 |
  | article9.genetisk_data (sidoeffekt) | 5/0/2 | 4/2/3 | +2 | -14.3 |
  | Article9Layer total | 37/7/0 | 36/14/0 | +7 | 0 |

  Article9Layer:s totala FP fördubblades (7 till 14) trots att etniskt_ursprung:s enda FP eliminerades och recall för halsodata och religios_overtygelse förbättrades. Kategorikonfusion mellan religios_overtygelse och sexuell_laggning (utlöst av "kyrklig vigsel"-tillägget) samt mellan halsodata och genetisk_data (utlöst av öppen CoT-resoning) driver regressionen.
- **Snapshots:**
  - [`demo/snapshots/iteration_3_baseline_v5_reproduction.json`](../demo/snapshots/iteration_3_baseline_v5_reproduction.json) - same-session v5-reproduktion
  - [`demo/snapshots/iteration_3_baseline_post_I4.json`](../demo/snapshots/iteration_3_baseline_post_I4.json) - v6-körning
- **Pekare:** Se sessionspost 2026-05-12 i [`docs/iteration_3_implementation.md`](iteration_3_implementation.md) för fullständig rotorsaksanalys och formaliseringskonsekvenser.
- **Status:** Inte aktiv produktionsprompt. Article9Layer använder v5 som default.

### v5 (aktiv)

Article9Layer:s aktiva produktionsprompt är v5, dokumenterad i sin YAML-metadata under
[`gdpr_classifier/prompts/article9/v5.yaml`](../gdpr_classifier/prompts/article9/v5.yaml).
Retroaktiv bilagepost för v5 kan tillfogas av framtida issue om spårbarheten kräver det.
