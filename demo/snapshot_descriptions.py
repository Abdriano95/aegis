"""Curated one-line Swedish descriptions per snapshot filename.

Kept in a dedicated module so the description catalogue can be maintained
independently of loading/rendering logic. Filenames not present in the dict
fall back to ``"<filnamn> (ingen beskrivning)"`` — never raises.
"""

from __future__ import annotations

SNAPSHOT_DESCRIPTIONS: dict[str, str] = {
    "i7d_cross_validating.json":
        "Iteration 3 — post-I-7g produktionsmätning (qwen3:14b, cross-validating, F1 86.94%); rapportflikens nya källa",
    "i7d_cross_validating_opus47.json":
        "Iteration 3 — post-I-7g med Claude Opus 4.7 som molnprovider, cross-validating (F1 87.85%, providerjämförelse)",
    "i7d_cross_validating_pre_i7e.json":
        "Iteration 3 — cross-validating före I-7e:s deduplicated_sources (qwen2.5:7b, F1 82.33%)",
    "i7d_cross_validating_qwen25_baseline.json":
        "Iteration 3 — post-I-7g cross-validating med qwen2.5:7b som modelljämförelse mot qwen3:14b (F1 82.33%)",
    "i7d_legacy.json":
        "Iteration 3 — post-I-7g i legacy-läge (qwen3:14b, F1 86.94%); baslinjejämförelse mot cross-validating",
    "i7d_legacy_opus47.json":
        "Iteration 3 — post-I-7g legacy-läge med Claude Opus 4.7 (F1 87.85%, providerjämförelse)",
    "i7d_legacy_pre_i7e.json":
        "Iteration 3 — legacy-läge före I-7e:s deduplicated_sources (qwen2.5:7b, F1 82.33%)",
    "i7d_legacy_qwen25_baseline.json":
        "Iteration 3 — post-I-7g legacy-läge med qwen2.5:7b som modelljämförelse (F1 82.33%)",
    "iteration_2_report.json":
        "Iteration 2 — slutmätning (qwen2.5:7b, combination v4, F1 74.55%); historisk baslinje",
    "iteration_3_baseline_post_I1.json":
        "Iteration 3 — efter I-1 (prompt-skärpning context.yrke/organisation, F1 79.33%)",
    "iteration_3_baseline_post_I2.json":
        "Iteration 3 — efter I-2 (matcher-aliasing article4.adress ↔ context.plats, F1 75.99%)",
    "iteration_3_baseline_post_I3.json":
        "Iteration 3 — efter I-3 (aggregator-deduplicering inom samma kategori, F1 78.23%)",
    "iteration_3_baseline_post_I4.json":
        "Iteration 3 — efter I-4 med experimentell article9 v6 (regression, rollback per Beslut 48, F1 78.17%)",
    "iteration_3_baseline_post_I5.json":
        "Iteration 3 — efter I-5 (tvådimensionell operationalisering identifierbarhet × dataklass, F1 79.48%)",
    "iteration_3_baseline_v4_reproduction.json":
        "Iteration 3 — reproduktionstest av combination v4 (qwen2.5:7b, F1 77.49%)",
    "iteration_3_baseline_v5_reproduction.json":
        "Iteration 3 — reproduktionstest av combination v5 (qwen2.5:7b, F1 79.26%)",
    "iteration_3_post_I5_fixup.json":
        "Iteration 3 — post-I-5-fixup (qwen2.5:7b, F1 79.48%); rapportflikens tidigare källa, ersätts av i7d",
    "iteration_3_post_num_ctx_fix.json":
        "Iteration 3 — efter num_ctx-parameterfix (qwen2.5:7b, F1 79.33%)",
    "iteration_3_probe_qwen25_7b_article9.json":
        "Iteration 3 — I-7-modellprob: qwen2.5:7b enbart article9-delmängd (52 texter, F1 63.72%)",
    "iteration_3_probe_qwen25_7b_combination.json":
        "Iteration 3 — I-7-modellprob: qwen2.5:7b enbart combination-delmängd (27 texter, F1 71.76%)",
    "iteration_3_probe_qwen3_14b_article9.json":
        "Iteration 3 — I-7-modellprob: qwen3:14b enbart article9-delmängd (52 texter, F1 73.79%)",
    "iteration_3_probe_qwen3_14b_combination.json":
        "Iteration 3 — I-7-modellprob: qwen3:14b enbart combination-delmängd (27 texter, F1 72.59%)",
    "iteration_3_probe_qwen3_14b_full_pipeline.json":
        "Iteration 3 — I-7-modellprob: qwen3:14b full pipeline (159 texter, F1 82.31%); motiverade modellbytet",
}


def get_description(filename: str) -> str:
    """Return the curated description for ``filename`` or a safe fallback."""
    return SNAPSHOT_DESCRIPTIONS.get(filename, f"{filename} (ingen beskrivning)")
