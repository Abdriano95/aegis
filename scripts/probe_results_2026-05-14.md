# Probe-resultat: Ollama-modellval

**Datum:** 2026-05-14  
**Temperatur:** 0.0  
**Körningar per prompt:** 1  
**Kontext:** Spike för att empiriskt motivera val av lokal Ollama-modell inför Article9Layer (#70) och CombinationLayer (#72).

> **Normalisering:** Kategori-fältet normaliseras före jämförelse: lowercase, diakritik borttagen (å→a, ä→a, ö→o), mellanslag/bindestreck→underscore. Semantiskt korrekta svar i annat format (t.ex. "hälsodata" vs "halsodata", "etniskt ursprung" vs "etniskt_ursprung") godkänns. Svar på fel språk (t.ex. "religious_belief") räknas fortfarande som felaktiga.

## Sammanfattning

| Modell | JSON-validitet | Svensk-korrekt | Snitt-latens | P95-latens | Storlek |
|--------|---------------|----------------|-------------|-----------|---------|
| qwen3:14b | 5/5 | 8/9 | 2.81s | 6.17s | 14.8B |

## Diskvalificeringsregel

Modeller under 90% JSON-validitet (< 5/5 på Kategori A) är inte aktuella oavsett språk-prestanda.

## Per-prompt-detaljer

<details>
<summary>qwen3:14b — detaljer</summary>

| Prompt | Resultat | Latens | Kommentar |
|--------|---------|-------|-----------|
| a1_extract_name | ✅ | 6.17s |  |
| a2_list_places | ✅ | 2.63s |  |
| a3_give_category | ✅ | 2.37s |  |
| a4_count_words | ✅ | 2.35s |  |
| a5_extract_date | ✅ | 2.46s |  |
| b1_health_positive | ✅ | 2.72s |  |
| b2_health_positive2 | ✅ | 2.62s |  |
| b3_religion_positive | ✅ | 2.64s |  |
| b4_ethnicity_positive | ✅ | 2.66s |  |
| b5_politics_positive | ❌ | 2.58s | category: förväntat "politisk_asikt" (→"politisk_asikt"), fick "fackmedlemskap" (→"fackmedlemskap") |
| b6_negative_profession | ✅ | 2.54s |  |
| b7_negative_meeting | ✅ | 2.53s |  |
| b8_negative_orgname | ✅ | 2.50s |  |
| b9_negative_food | ✅ | 2.53s |  |

</details>

## Rekommendation

Av kvalificerade modeller presterar **qwen3:14b** bäst med 8/9 korrekt svensk-klassificering och 5/5 JSON-validitet.
Snittlatens: 2.81s, P95-latens: 6.17s, storlek: 14.8B.

Rekommendation: **qwen3:14b** som primär modell för Article9Layer och CombinationLayer. Modellen uppfyller JSON-validitetskravet (≥ 90%) och visar bäst prestanda på svensk språkförståelse bland testade alternativ.
OBS: Denna rekommendation baseras på ett begränsat probe-set (14 prompts) och bör valideras vidare vid implementation av #70 och #72. Skriptet kan köras igen i iteration 3 om modellvalet behöver omprövas.
