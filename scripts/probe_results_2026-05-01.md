# Probe-resultat: Ollama-modellval

**Datum:** 2026-05-01  
**Temperatur:** 0.0  
**Körningar per prompt:** 1  
**Kontext:** Spike för att empiriskt motivera val av lokal Ollama-modell inför Article9Layer (#70) och CombinationLayer (#72).

> **Normalisering:** Kategori-fältet normaliseras före jämförelse: lowercase, diakritik borttagen (å→a, ä→a, ö→o), mellanslag/bindestreck→underscore. Semantiskt korrekta svar i annat format (t.ex. "hälsodata" vs "halsodata", "etniskt ursprung" vs "etniskt_ursprung") godkänns. Svar på fel språk (t.ex. "religious_belief") räknas fortfarande som felaktiga.

## Sammanfattning

| Modell | JSON-validitet | Svensk-korrekt | Snitt-latens | P95-latens | Storlek |
|--------|---------------|----------------|-------------|-----------|---------|
| llama3.1:8b | 5/5 | 6/9 | 1.38s | 11.28s | 8.0B |
| qwen2.5:7b-instruct | 5/5 | 8/9 | 1.27s | 8.90s | 7.6B |
| mistral-nemo:12b | 5/5 | 5/9 | 2.63s | 15.61s | 12.2B |

## Diskvalificeringsregel

Modeller under 90% JSON-validitet (< 4/5 på Kategori A) är inte aktuella oavsett språk-prestanda.

## Per-prompt-detaljer

<details>
<summary>llama3.1:8b — detaljer</summary>

| Prompt | Resultat | Latens | Kommentar |
|--------|---------|-------|-----------|
| a1_extract_name | ✅ | 11.28s |  |
| a2_list_places | ✅ | 0.99s |  |
| a3_give_category | ✅ | 0.35s |  |
| a4_count_words | ✅ | 0.44s |  |
| a5_extract_date | ✅ | 0.60s |  |
| b1_health_positive | ❌ | 0.70s | contains_sensitive: förväntat True, fick False |
| b2_health_positive2 | ✅ | 0.64s |  |
| b3_religion_positive | ❌ | 0.48s | contains_sensitive: förväntat True, fick False |
| b4_ethnicity_positive | ✅ | 0.72s |  |
| b5_politics_positive | ❌ | 0.65s | contains_sensitive: förväntat True, fick False |
| b6_negative_profession | ✅ | 0.61s |  |
| b7_negative_meeting | ✅ | 0.63s |  |
| b8_negative_orgname | ✅ | 0.63s |  |
| b9_negative_food | ✅ | 0.60s |  |

</details>

<details>
<summary>qwen2.5:7b-instruct — detaljer</summary>

| Prompt | Resultat | Latens | Kommentar |
|--------|---------|-------|-----------|
| a1_extract_name | ✅ | 8.90s |  |
| a2_list_places | ✅ | 0.87s |  |
| a3_give_category | ✅ | 0.53s |  |
| a4_count_words | ✅ | 0.36s |  |
| a5_extract_date | ✅ | 0.55s |  |
| b1_health_positive | ✅ | 0.84s |  |
| b2_health_positive2 | ✅ | 0.76s |  |
| b3_religion_positive | ❌ | 0.61s | contains_sensitive: förväntat True, fick False |
| b4_ethnicity_positive | ✅ | 0.89s |  |
| b5_politics_positive | ✅ | 0.76s |  |
| b6_negative_profession | ✅ | 0.62s |  |
| b7_negative_meeting | ✅ | 0.70s |  |
| b8_negative_orgname | ✅ | 0.67s |  |
| b9_negative_food | ✅ | 0.70s |  |

</details>

<details>
<summary>mistral-nemo:12b — detaljer</summary>

| Prompt | Resultat | Latens | Kommentar |
|--------|---------|-------|-----------|
| a1_extract_name | ✅ | 15.61s |  |
| a2_list_places | ✅ | 1.73s |  |
| a3_give_category | ✅ | 0.80s |  |
| a4_count_words | ✅ | 0.79s |  |
| a5_extract_date | ✅ | 1.47s |  |
| b1_health_positive | ❌ | 1.69s | contains_sensitive: förväntat True, fick False |
| b2_health_positive2 | ✅ | 1.97s |  |
| b3_religion_positive | ❌ | 2.02s | category: förväntat "religios_overtygelse" (→"religios_overtygelse"), fick "religious_belief" (→"religious_belief") |
| b4_ethnicity_positive | ✅ | 1.99s |  |
| b5_politics_positive | ❌ | 1.91s | category: förväntat "politisk_asikt" (→"politisk_asikt"), fick "political_views" (→"political_views") |
| b6_negative_profession | ✅ | 1.58s |  |
| b7_negative_meeting | ✅ | 1.63s |  |
| b8_negative_orgname | ✅ | 1.64s |  |
| b9_negative_food | ❌ | 1.98s | contains_sensitive: förväntat False, fick True |

</details>

## Rekommendation

Av kvalificerade modeller presterar **qwen2.5:7b-instruct** bäst med 8/9 korrekt svensk-klassificering och 5/5 JSON-validitet.
Snittlatens: 1.27s, P95-latens: 8.90s, storlek: 7.6B.
Näst bästa alternativ: **llama3.1:8b** med 6/9 svensk-korrekt och snittlatens 1.38s.

Rekommendation: **qwen2.5:7b-instruct** som primär modell för Article9Layer och CombinationLayer. Modellen uppfyller JSON-validitetskravet (≥ 90%) och visar bäst prestanda på svensk språkförståelse bland testade alternativ.
OBS: Denna rekommendation baseras på ett begränsat probe-set (14 prompts) och bör valideras vidare vid implementation av #70 och #72. Skriptet kan köras igen i iteration 3 om modellvalet behöver omprövas.
