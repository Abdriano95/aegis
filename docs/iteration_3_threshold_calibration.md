# Iteration 3: Empirisk tröskelkalibrering (I-6 / Issue #106)

**Status**: Fas 1 pausad efter 14 av 16 körningar (2026-05-14). Pausen motiveras av två oberoende fynd: (1) invariansfyndet att aggregator-trösklar inte påverkar finding-listan, (2) num_ctx-flagga i OllamaProvider som kräver verifiering innan vidare empirisk kalibrering.

## Baslinje (dokumenterad referens)

`demo/snapshots/iteration_3_post_I5_fixup.json`, commit 00e1e66, 2026-05-14 06:27 UTC

| Metric | Värde |
|---|---|
| TP / FP / FN | 213 / 90 / 20 |
| Precision | 70.30% |
| Recall | 91.42% |
| F1 | 79.48% |

## Lokal baslinje (sanity check innan fas 1)

Kördes med defaults (M=0.7, H=0.85, E=2), identisk kod, 2026-05-14.

| Metric | Värde |
|---|---|
| TP / FP / FN | 211 / 98 / 22 |
| Precision | 68.28% |
| Recall | 90.56% |
| F1 | 77.86% |

Avvikelse från dokumenterad baslinje: TP −2, FP +8, FN +2. Klassificeras som LLM-stochasticitet (Ollama greedy decoding ej fullständigt deterministisk över model-load-tillfällen trots temperature=0.0). Notering: efter pausens orsaksanalys är även stochasticiteten potentiellt påverkad av num_ctx-frågan. Måste omvärderas efter token-mätning.

## Metod (planerad)

Tröskelrutnät enligt I-6-prompten:
- `medium_threshold` ∈ {0.5, 0.65, 0.8}
- `high_confidence_bypass` ∈ {0.75, 0.85, 0.95}
- `min_evidence_count` ∈ {1, 2}

Cartesisk produkt: 18 konfigurationer. Två kombinationer ogiltiga eftersom de bryter konstruktor-constraint `high_confidence_bypass >= medium_threshold` (M=0.8/H=0.75 med E=1 eller E=2). Effektivt 16 giltiga konfigurationer.

Sekventiella körningar mot iteration 1, 2 och 3-dataset via `run_evaluation.py` med TEMP CLI-argument som överrider Aggregator-defaults.

## Fas 1: Resultat (14 av 16 körningar)

| # | M | H | E | TP | FP | FN | Prec | Rec | F1 | Mek3 | INDIRECT | NONE |
|---|---|---|---|----|----|----|------|-----|-----|------|----------|------|
| 1 | 0.5 | 0.75 | 1 | 212 | 100 | 21 | 67.95% | 90.99% | 77.80% | 0 | 6 | 71 |
| 2 | 0.5 | 0.75 | 2 | 212 | 100 | 21 | 67.95% | 90.99% | 77.80% | 0 | 6 | 71 |
| 3 | 0.5 | 0.85 | 1 | 212 | 100 | 21 | 67.95% | 90.99% | 77.80% | 0 | 6 | 71 |
| 4 | 0.5 | 0.85 | 2 | 212 | 100 | 21 | 67.95% | 90.99% | 77.80% | 0 | 6 | 71 |
| 5 | 0.5 | 0.95 | 1 | 212 | 100 | 21 | 67.95% | 90.99% | 77.80% | 1 | 1 | 76 |
| 6 | 0.5 | 0.95 | 2 | 212 | 100 | 21 | 67.95% | 90.99% | 77.80% | 0 | 0 | 77 |
| 7 | 0.65 | 0.75 | 1 | 212 | 100 | 21 | 67.95% | 90.99% | 77.80% | 0 | 6 | 71 |
| 8 | 0.65 | 0.75 | 2 | 212 | 100 | 21 | 67.95% | 90.99% | 77.80% | 0 | 6 | 71 |
| 9 | 0.65 | 0.85 | 1 | 212 | 100 | 21 | 67.95% | 90.99% | 77.80% | 0 | 6 | 71 |
| 10 | 0.65 | 0.85 | 2 | 212 | 100 | 21 | 67.95% | 90.99% | 77.80% | 0 | 6 | 71 |
| 11 | 0.65 | 0.95 | 1 | 212 | 100 | 21 | 67.95% | 90.99% | 77.80% | 1 | 1 | 76 |
| 12 | 0.65 | 0.95 | 2 | 212 | 100 | 21 | 67.95% | 90.99% | 77.80% | 0 | 0 | 77 |
| 13 | 0.8 | 0.85 | 1 | 212 | 100 | 21 | 67.95% | 90.99% | 77.80% | 0 | 6 | 71 |
| 14 | 0.8 | 0.85 | 2 | 212 | 100 | 21 | 67.95% | 90.99% | 77.80% | 0 | 6 | 71 |
| 15 | 0.8 | 0.95 | 1 | EJ KÖRD (paus) | | | | | | | | |
| 16 | 0.8 | 0.95 | 2 | EJ KÖRD (paus) | | | | | | | | |

## Fas 1: Empiriska observationer

### Observation 1: TP/FP/FN invariant över alla körningar

Samtliga 14 körningar gav identiska TP/FP/FN = 212/100/21. Precision (67.95%), Recall (90.99%) och F1 (77.80%) är därmed också konstanta över hela tröskelrutnätet.

### Observation 2: medium_threshold har ingen mätbar effekt

Värdena 0.5, 0.65 och 0.8 för `medium_threshold` ger identiska utfall. Alla context.kombination-fynd i det aktuella datasetet har confidence ≥ 0.8 vilket gör att M-tröskeln aldrig binder.

### Observation 3: Effekten ligger i kombinationen (H, E)

Tre observerade regimer i hur Classification.identifiability fördelas:

| Regim | H | E | Mek3 | INDIRECT | NONE | Tolkning |
|---|---|---|------|----------|------|----------|
| A (default-liknande) | 0.75 eller 0.85 | 1 eller 2 | 0 | 6 | 71 | Bypass-vägen tar alla 6 kandidater; Mek3 testas aldrig |
| B (Mek3 aktiv) | 0.95 | 1 | 1 | 1 | 76 | Bypass deaktiverad, Mek3 testas och fångar 1 av 6 |
| C (kollaps) | 0.95 | 2 | 0 | 0 | 77 | Bypass deaktiverad, Mek3 för strikt, 0 INDIRECT |

### Observation 4: Mekanism 3 är aktiv funktionalitet

Regim B (H=0.95, E=1) ger Mek3-count=1. Detta verifierar empiriskt att Mekanism 3 är aktiv kod, inte död kod, vilket är vad Beslut 41:s designintegritetsargument kräver.

### Observation 5: Recall-tröskeln 89.27% uppfylls genomgående

Recall 90.99% ligger 1.72 procentenheter över iteration 2:s baslinje (89.27%) i samtliga 14 körningar. Recall-säkerhet är därmed inte ett bekymmer för någon tröskelkombination i det testade rutnätet.

## Fas 1: Arkitekturell designinsikt

Aggregator-trösklarna styr Classification.identifiability-klassning, inte finding-listan. Matcher beräknar TP/FP/FN på finding-nivå (spans + kategorier) innan aggregator kör. Trösklarna kommer in efter att matcher bestämt vad som är ett fynd och kan därför per arkitektur inte påverka Precision/Recall/F1.

Detta är konsistent med Single Responsibility Principle (Martin 2003) som ligger bakom Beslut 18 (split mellan Article9Layer och CombinationLayer). Aggregatorns ansvar är klassificeringsbeslut, inte fynd-detektering.

I-6:s ursprungliga prognos om "Precision lyfts till 71-73% via trösklar" var arkitekturellt felaktig. Precision-förbättring kräver lager-konfidensjustering (out of scope per issue body) eller prompt-förbättringar (out of scope per Beslut 41).

## Pausorsak: num_ctx-flagga (parallell analys)

Annan arkitekt-instans har identifierat 2026-05-14 att OllamaProvider inte sätter `num_ctx` explicit i sin payload:

```python
"options": {"temperature": self._temperature},
```

`ollama ps` under pågående fas 1-körning visar CONTEXT=4096 tokens. CombinationLayer v5-prompten (system_prompt + task_instruction + examples + reasoning_instructions + output_format) plus långa testtexter (vissa kombinationstexter 200-300 ord) plus modellens output (reasoning + JSON) kan ligga nära eller över 4096 tokens.

Hypotesen att tyst trunkering kan ha påverkat iteration 2:s och iteration 3:s LLM-baserade utvärdering måste verifieras genom empirisk token-mätning innan I-6 fortsätter.

Pattern-lagret och Entity-lagret är opåverkade eftersom de inte kör LLM.

## Nästa steg

1. Empirisk token-mätning av Article9Layer- och CombinationLayer-prompter mot alla testtexter i de tre evalueringsdatasetten
2. Om mätningen visar trunkering: num_ctx-fix i OllamaProvider, omkörning av iteration 2:s LLM-baserade utvärdering, ny baslinje för I-6
3. Om mätningen visar ingen trunkering: num_ctx-sättning som arkitekturhärdning (utan omkörning), fortsätt I-6 med reformulerad spec
4. I-6 reformuleras: ursprungligt mål "Precision via trösklar" ersätts med "dokumentera invariansfyndet, välj defaults som maximerar Mek3-aktivering enligt Beslut 41, formalisera designinsikten som bidrag till kapitel 5"

## Cell 2-cirkularitet

Trösklar är kalibrerade mot artefaktens egen testdomän. Detta är cirkulärt i den meningen att testdatat används både för att utvärdera artefakten och för att kalibrera dess parametrar. Resultaten generaliserar därför inte automatiskt till andra textdomäner och bör tolkas som intern konsistens snarare än extern validitet. Full diskussion i `tests/data/iteration_2/data_statement.md` och rapportens resultatkapitel.

## Slutkonfiguration

Lämnas tom tills paus är upplöst och reformulerad I-6 har körts.
