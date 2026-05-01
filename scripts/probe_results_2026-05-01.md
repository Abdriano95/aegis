# Probe-resultat: Ollama-modellval

**Datum:** 2026-05-01  
**Temperatur:** 0.0  
**Körningar per prompt:** 1  
**Kontext:** Spike för att empiriskt motivera val av lokal Ollama-modell inför Article9Layer (#70) och CombinationLayer (#72).

> **Normalisering:** Kategori-fältet normaliseras före jämförelse: lowercase, diakritik borttagen (å→a, ä→a, ö→o), mellanslag/bindestreck→underscore. Semantiskt korrekta svar i annat format (t.ex. "hälsodata" vs "halsodata", "etniskt ursprung" vs "etniskt_ursprung") godkänns. Svar på fel språk (t.ex. "religious_belief") räknas fortfarande som felaktiga.

## Sammanfattning

| Modell | JSON-validitet | Svensk-korrekt | Snitt-latens | P95-latens | Storlek |
|--------|---------------|----------------|-------------|-----------|---------|
| llama3.1:8b | 5/5 | 6/9 | 1.11s | 7.75s | 8.0B |
| qwen2.5:7b-instruct | 5/5 | 8/9 | 1.72s | 15.37s | 7.6B |
| mistral-nemo:12b | 5/5 | 5/9 | 2.41s | 13.28s | 12.2B |

## Diskvalificeringsregel

Modeller under 90% JSON-validitet (< 5/5 på Kategori A) är inte aktuella oavsett språk-prestanda.

## Per-prompt-detaljer

<details>
<summary>llama3.1:8b — detaljer</summary>

| Prompt | Resultat | Latens | Kommentar |
|--------|---------|-------|-----------|
| a1_extract_name | ✅ | 7.75s |  |
| a2_list_places | ✅ | 0.98s |  |
| a3_give_category | ✅ | 0.37s |  |
| a4_count_words | ✅ | 0.46s |  |
| a5_extract_date | ✅ | 0.58s |  |
| b1_health_positive | ❌ | 0.70s | contains_sensitive: förväntat True, fick False |
| b2_health_positive2 | ✅ | 0.60s |  |
| b3_religion_positive | ❌ | 0.46s | contains_sensitive: förväntat True, fick False |
| b4_ethnicity_positive | ✅ | 0.69s |  |
| b5_politics_positive | ❌ | 0.59s | contains_sensitive: förväntat True, fick False |
| b6_negative_profession | ✅ | 0.59s |  |
| b7_negative_meeting | ✅ | 0.61s |  |
| b8_negative_orgname | ✅ | 0.60s |  |
| b9_negative_food | ✅ | 0.60s |  |

</details>

<details>
<summary>qwen2.5:7b-instruct — detaljer</summary>

| Prompt | Resultat | Latens | Kommentar |
|--------|---------|-------|-----------|
| a1_extract_name | ✅ | 15.37s |  |
| a2_list_places | ✅ | 0.81s |  |
| a3_give_category | ✅ | 0.52s |  |
| a4_count_words | ✅ | 0.36s |  |
| a5_extract_date | ✅ | 0.55s |  |
| b1_health_positive | ✅ | 0.83s |  |
| b2_health_positive2 | ✅ | 0.80s |  |
| b3_religion_positive | ❌ | 0.67s | contains_sensitive: förväntat True, fick False |
| b4_ethnicity_positive | ✅ | 0.88s |  |
| b5_politics_positive | ✅ | 0.79s |  |
| b6_negative_profession | ✅ | 0.63s |  |
| b7_negative_meeting | ✅ | 0.66s |  |
| b8_negative_orgname | ✅ | 0.63s |  |
| b9_negative_food | ✅ | 0.61s |  |

</details>

<details>
<summary>mistral-nemo:12b — detaljer</summary>

| Prompt | Resultat | Latens | Kommentar |
|--------|---------|-------|-----------|
| a1_extract_name | ✅ | 13.28s |  |
| a2_list_places | ✅ | 1.64s |  |
| a3_give_category | ✅ | 0.77s |  |
| a4_count_words | ✅ | 0.75s |  |
| a5_extract_date | ✅ | 1.42s |  |
| b1_health_positive | ❌ | 1.64s | contains_sensitive: förväntat True, fick False |
| b2_health_positive2 | ✅ | 1.97s |  |
| b3_religion_positive | ❌ | 1.92s | category: förväntat "religios_overtygelse" (→"religios_overtygelse"), fick "religious_belief" (→"religious_belief") |
| b4_ethnicity_positive | ✅ | 1.92s |  |
| b5_politics_positive | ❌ | 1.85s | category: förväntat "politisk_asikt" (→"politisk_asikt"), fick "political_views" (→"political_views") |
| b6_negative_profession | ✅ | 1.58s |  |
| b7_negative_meeting | ✅ | 1.57s |  |
| b8_negative_orgname | ✅ | 1.53s |  |
| b9_negative_food | ❌ | 1.89s | contains_sensitive: förväntat False, fick True |

</details>

