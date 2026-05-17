#!/usr/bin/env python3
"""I-7d: dubbel baslinjemätning legacy mot cross_validating.

Detect-once, aggregate-twice. De fyra lagren körs EN gång per text; den
identiska fyndlistan matas genom två Aggregator-instanser (legacy och
cross_validating). Säkert eftersom aggregate() aldrig muterar sin input
(Finding är frozen, evidence-weighting använder dataclasses.replace,
containment/dedup returnerar nya listor) — mode-jämförelsen blir därmed
exakt kontrollerad och LLM-tiden halveras (159 texter, inte 318).

Producerar två snapshots i demo/snapshots/ (build_demo_snapshot-schemat,
utökat med cross_validation_mode, baseline_iteration_2, instrument_fn,
sanity_check; cross_validating-snapshotten även evidence_basis_breakdown).

Ingen ändring i gdpr_classifier/ eller evaluation/ — allt importeras
read-only. Endast cross_validation_mode varieras mellan de två
aggregeringarna.

Krav:
    - Ollama på http://localhost:11434, modell qwen3:14b pullad
    - pip install -e ".[all]"

Användning:
    python scripts/run_i7d_baseline.py             # full korpus (159)
    python scripts/run_i7d_baseline.py --degerfors # isolerad Fas 2
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Svenska tecken + pilar ("→") i utskrifter kraschar annars på Windows
# cp1252-konsoler (UnicodeEncodeError). JSON skrivs alltid med explicit
# encoding="utf-8" och påverkas inte; detta gäller endast stdout/stderr.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

import requests  # noqa: E402 (import after sys.path manipulation)

from evaluation.confusion_matrix import ConfusionMatrix  # noqa: E402
from evaluation.dataset.loader import load_dataset  # noqa: E402
from evaluation.matcher import match  # noqa: E402
from evaluation.metrics import f1, precision, recall  # noqa: E402
from evaluation.report import (  # noqa: E402
    DimensionStats,
    Report,
    RunMetrics,
    SampleResult,
)
from gdpr_classifier import Aggregator  # noqa: E402
from gdpr_classifier.config import get_llm_provider  # noqa: E402
from gdpr_classifier.core.category import Category  # noqa: E402
from gdpr_classifier.core.classification import (  # noqa: E402
    DataClass,
    Identifiability,
)
from gdpr_classifier.layers.article9 import (  # noqa: E402
    Article9Layer,
    Article9LayerError,
)
from gdpr_classifier.layers.combination import (  # noqa: E402
    CombinationLayer,
    CombinationLayerError,
)
from gdpr_classifier.layers.entity import EntityLayer  # noqa: E402
from gdpr_classifier.layers.llm.provider import LLMProviderError  # noqa: E402
from gdpr_classifier.layers.pattern import PatternLayer  # noqa: E402

_MODEL = os.getenv("AEGIS_MODEL", "qwen3:14b")
# Probe-checkpoint 7 (#107): suffix the snapshot filenames so an Anthropic run
# does not overwrite the qwen3:14b baseline (i7d_legacy.json / i7d_cross_*).
_SNAPSHOT_SUFFIX = os.getenv("AEGIS_SNAPSHOT_SUFFIX", "")
_SNAPSHOTS_DIR = _PROJECT_ROOT / "demo" / "snapshots"
_DATASET_PATHS = {
    "iteration_1": _PROJECT_ROOT / "tests" / "data" / "iteration_1" / "test_dataset.json",
    "article9": _PROJECT_ROOT / "tests" / "data" / "iteration_2" / "article9_dataset.json",
    "combination": _PROJECT_ROOT / "tests" / "data" / "iteration_2" / "combination_dataset.json",
}
_SUBSET_KEYS = ("iteration_1", "article9", "combination")
_ARTICLE9_VERSION = "v5"
_COMBINATION_VERSION = "v5"
# Iteration-2-baslinjen (demo/snapshots/iteration_2_report.json,
# iteration_2_utvardering.md Del 6 reproduktionskörning #80).
_BASELINE_IT2 = {"precision": 0.64, "recall": 0.8927, "f1": 0.7455}
_EVIDENCE_BASES = (
    "structural_support",
    "high_confidence_no_support",
    "no_support_required",
)
_DEGERFORS_TEXTS = {
    "text_stockholm": "En 25-åring med blått hår bor i Stockholm.",
    "text_degerfors": "En 25-åring med blått hår bor i Degerfors.",
}


def check_ollama() -> None:
    """Exit with a clean error message if Ollama is not reachable."""
    try:
        requests.get("http://localhost:11434/api/tags", timeout=5).raise_for_status()
    except Exception as exc:
        print(
            f"ERROR: Ollama inte tillgänglig på http://localhost:11434 - {exc}\n"
            "Starta Ollama (ollama serve) och säkerställ att modellen "
            f"{_MODEL} är pullad.",
            file=sys.stderr,
        )
        sys.exit(1)


def get_git_commit() -> str:
    """Return the current HEAD commit hash, or 'unknown' on failure."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def truncate(text: str, max_len: int = 60) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def _calc_metrics(tp: int, fp: int, fn: int) -> RunMetrics:
    return RunMetrics(
        tp=tp,
        fp=fp,
        fn=fn,
        recall=recall(tp=tp, fn=fn),
        precision=precision(tp=tp, fp=fp),
        f1=f1(tp=tp, fp=fp, fn=fn),
    )


def _build_layers() -> list:
    """Instantiate the four layers (build_demo_snapshot-defaults)."""
    provider = get_llm_provider(_MODEL)
    return [
        PatternLayer(),
        EntityLayer(),
        Article9Layer(provider, prompt_version=_ARTICLE9_VERSION),
        CombinationLayer(provider, prompt_version=_COMBINATION_VERSION),
    ]


def _detect_once(layers: list, text: str) -> list:
    """Replicate Pipeline.classify's detection half: collect once."""
    all_findings: list = []
    for layer in layers:
        all_findings.extend(layer.detect(text))
    return all_findings


def _bump_dimensions(id_counts: dict, dc_counts: dict, cls) -> None:
    """Increment id/dc distribution counters (build_demo_snapshot pattern)."""
    id_value = getattr(cls, "identifiability", Identifiability.NONE)
    id_key = id_value.value if id_value is not None else "none"
    id_counts[id_key if id_key in id_counts else "none"] += 1
    dc_value = getattr(cls, "data_class", DataClass.NONE)
    dc_key = dc_value.value if dc_value is not None else "none"
    dc_counts[dc_key if dc_key in dc_counts else "none"] += 1


def _build_report(cm: ConfusionMatrix, samples: list, id_counts: dict,
                   dc_counts: dict) -> Report:
    """Construct a Report exactly as evaluation/runner.py does."""
    t_tp, t_fp, t_fn = cm.get_total_stats()
    total_metrics = _calc_metrics(t_tp, t_fp, t_fn)

    categories = set(
        list(cm.category_tp.keys())
        + list(cm.category_fp.keys())
        + list(cm.category_fn.keys())
    )
    per_category = {
        cat: _calc_metrics(*cm.get_category_stats(cat)) for cat in categories
    }
    layers = set(list(cm.layer_tp.keys()) + list(cm.layer_fp.keys()))
    per_layer = {
        layer: _calc_metrics(*cm.get_layer_stats(layer)) for layer in layers
    }
    return Report(
        total=total_metrics,
        per_category=per_category,
        per_layer=per_layer,
        samples=samples,
        per_dimension=DimensionStats(
            identifiability_none=id_counts["none"],
            identifiability_indirect=id_counts["indirect"],
            identifiability_direct=id_counts["direct"],
            data_class_none=dc_counts["none"],
            data_class_special=dc_counts["special"],
            data_class_criminal=dc_counts["criminal"],
        ),
    )


def _write_snapshot(
    path: Path,
    report: Report,
    *,
    mode: str,
    n: int,
    subset_counts: dict,
    commit: str,
    metadata_extra: dict | None = None,
    top_level_extra: dict | None = None,
) -> None:
    """Serialise a snapshot in the build_demo_snapshot schema."""
    out: dict = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model": _MODEL,
            "subset": "all",
            "cross_validation_mode": mode,
            "prompt_versions": {
                "article9": _ARTICLE9_VERSION,
                "combination": _COMBINATION_VERSION,
            },
            "dataset": {
                "total_texts": n,
                "iteration_1_texts": subset_counts["iteration_1"],
                "article9_texts": subset_counts["article9"],
                "combination_texts": subset_counts["combination"],
            },
            "git_commit": commit,
            "pipeline_layers": ["pattern", "entity", "article9", "combination"],
            "baseline_iteration_2": _BASELINE_IT2,
        },
        "report": dataclasses.asdict(report),
    }
    if metadata_extra:
        out["metadata"].update(metadata_extra)
    if top_level_extra:
        out.update(top_level_extra)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Snapshot skrivet till {path.relative_to(_PROJECT_ROOT)}")


def run_full() -> None:
    """Fas 1: full-corpus detect-once aggregate-twice measurement."""
    # Ollama-reachability is only a precondition when Ollama is the backend.
    # For LLM_PROVIDER=anthropic/gemini this check is irrelevant (#107 probe).
    if os.environ.get("LLM_PROVIDER", "ollama").lower() == "ollama":
        check_ollama()

    print(f"Laddar dataset (subset=all, modell={_MODEL})...")
    subset_counts = {key: 0 for key in _DATASET_PATHS}
    dataset: list = []
    for key in _SUBSET_KEYS:
        loaded = load_dataset(str(_DATASET_PATHS[key]))
        subset_counts[key] = len(loaded)
        dataset.extend(loaded)
    n = len(dataset)
    print(
        f"Dataset: {n} texter "
        f"({subset_counts['iteration_1']} iteration-1 + "
        f"{subset_counts['article9']} artikel-9 + "
        f"{subset_counts['combination']} kombination)"
    )

    print("Skapar lager + två aggregatorer (legacy / cross_validating)...")
    layers = _build_layers()
    active_layers = [layer.name for layer in layers]
    agg_legacy = Aggregator(cross_validation_mode="legacy")
    agg_xval = Aggregator(cross_validation_mode="cross_validating")

    cm_legacy, cm_xval = ConfusionMatrix(), ConfusionMatrix()
    samples_legacy: list[SampleResult] = []
    samples_xval: list[SampleResult] = []
    id_legacy = dict.fromkeys(["none", "indirect", "direct"], 0)
    dc_legacy = dict.fromkeys(["none", "special", "criminal"], 0)
    id_xval = dict.fromkeys(["none", "indirect", "direct"], 0)
    dc_xval = dict.fromkeys(["none", "special", "criminal"], 0)

    # Per-evidence_basis (cross_validating): total + context.kombination-only.
    eb_total = {b: {"tp": 0, "fp": 0} for b in _EVIDENCE_BASES}
    eb_komb = {b: {"tp": 0, "fp": 0} for b in _EVIDENCE_BASES}

    instrument_fn_cases: list[dict] = []
    sanity_failures: list[dict] = []
    # Probe-checkpoint 7 (#107): the v5 prompts were tuned for qwen, not Claude,
    # and AnthropicProvider does a bare json.loads. A single fenced/preamble
    # response would otherwise abort mid-run and waste every prior paid Opus
    # call. Record per-text failures and continue instead.
    llm_failures: list[dict] = []

    print(f"\nKör utvärdering ({n} texter, detect-once aggregate-twice)...\n")
    for i, item in enumerate(dataset, 1):
        print(f"  [{i:3d}/{n}] {truncate(item.text)}")
        try:
            all_findings = _detect_once(layers, item.text)
            cls_legacy = agg_legacy.aggregate(all_findings, active_layers)
            cls_xval = agg_xval.aggregate(all_findings, active_layers)
        except (LLMProviderError, Article9LayerError,
                CombinationLayerError) as exc:
            llm_failures.append({
                "index": i,
                "text": truncate(item.text, 80),
                "error": str(exc),
            })
            print(f"        ! LLM/parse-fel, hoppar text {i}: {exc}")
            continue

        # Sanity-assert (Justering 1): identifiability/data_class/sensitivity
        # MÅSTE vara identiska (per arkitektur). findings/weakest_evidence_basis
        # skiljer sig avsiktligt och jämförs INTE.
        if not (
            cls_legacy.identifiability == cls_xval.identifiability
            and cls_legacy.data_class == cls_xval.data_class
            and cls_legacy.sensitivity == cls_xval.sensitivity
        ):
            sanity_failures.append({
                "index": i,
                "text": item.text,
                "legacy": {
                    "identifiability": cls_legacy.identifiability.value,
                    "data_class": cls_legacy.data_class.value,
                    "sensitivity": cls_legacy.sensitivity.value,
                },
                "cross_validating": {
                    "identifiability": cls_xval.identifiability.value,
                    "data_class": cls_xval.data_class.value,
                    "sensitivity": cls_xval.sensitivity.value,
                },
            })

        _bump_dimensions(id_legacy, dc_legacy, cls_legacy)
        _bump_dimensions(id_xval, dc_xval, cls_xval)

        mr_legacy = match(cls_legacy.findings, item.expected_findings)
        mr_xval = match(cls_xval.findings, item.expected_findings)
        cm_legacy.add_match_result(mr_legacy)
        cm_xval.add_match_result(mr_xval)
        samples_legacy.append(SampleResult(
            text=item.text,
            false_positives=list(mr_legacy.false_positives),
            false_negatives=list(mr_legacy.false_negatives),
        ))
        samples_xval.append(SampleResult(
            text=item.text,
            false_positives=list(mr_xval.false_positives),
            false_negatives=list(mr_xval.false_negatives),
        ))

        # Step 7: per-evidence_basis (cross_validating). true_positives is
        # list[tuple[Finding, LabeledFinding]]; false_positives is list[Finding].
        for finding, _expected in mr_xval.true_positives:
            eb_total[finding.evidence_basis]["tp"] += 1
            if finding.source == "context.kombination":
                eb_komb[finding.evidence_basis]["tp"] += 1
        for finding in mr_xval.false_positives:
            eb_total[finding.evidence_basis]["fp"] += 1
            if finding.source == "context.kombination":
                eb_komb[finding.evidence_basis]["fp"] += 1

        # Step 7b: mätinstrument-FN. legacy och xval har identiska FN; en
        # förväntad article4.adress som blev FN och vars span överlappas av
        # ett predikterat entity.spacy_LOC-fynd = facit-adress som EntityLayer
        # nu mappar till context.plats (mätinstrumentskiftet, I-7c).
        loc_findings = [
            f for f in cls_legacy.findings if f.source == "entity.spacy_LOC"
        ]
        for expected in mr_legacy.false_negatives:
            if expected.category != Category.ADRESS:
                continue
            if any(
                lf.start < expected.end and expected.start < lf.end
                for lf in loc_findings
            ):
                instrument_fn_cases.append({
                    "index": i,
                    "text_span": expected.text_span,
                    "start": expected.start,
                    "end": expected.end,
                    "text": truncate(item.text, 80),
                })

    # Graderat sanity-utfall (Justering 1).
    nfail = len(sanity_failures)
    print(f"\nSanity-avvikelser "
          f"(identifiability/data_class/sensitivity): {nfail}")
    if nfail > 2:
        print("\n" + "=" * 70)
        print("ARKITEKTONISK AVVIKELSE UPPTÄCKT — KÖRNINGEN STANNAR.")
        print(f"{nfail} texter gav olika klassifikationsutfall mellan legacy")
        print("och cross_validating. Detta invaliderar I-7b:s")
        print("test_legacy_mode_unchanged och kräver användarbeslut.")
        print("Inga snapshots skrivna, ingen Del 8, I-7d-raden kvarstår "
              "🔄 Pågår.")
        print("=" * 70)
        for sf in sanity_failures:
            print(f"\n[{sf['index']}] {truncate(sf['text'], 100)}")
            print(f"  legacy:           {sf['legacy']}")
            print(f"  cross_validating: {sf['cross_validating']}")
        print("\nMöjliga orsaker att utreda i gdpr_classifier/aggregator.py:")
        print("  - _apply_evidence_weighting muterar fynd utöver evidence_basis")
        print("  - _determine_dimensions/_has_validated_kombination mode-gatad")
        print("  - _derive_weakest_evidence_basis sidoeffekt på findings")
        sys.exit(2)

    commit = get_git_commit()
    report_legacy = _build_report(
        cm_legacy, samples_legacy, id_legacy, dc_legacy
    )
    report_xval = _build_report(cm_xval, samples_xval, id_xval, dc_xval)

    instrument_block = {
        "count": len(instrument_fn_cases),
        "definition": (
            "Förväntad article4.adress som blev FN och vars span överlappas "
            "av ett predikterat entity.spacy_LOC-fynd (I-7c-mätinstrumentskifte)."
        ),
        "cases": instrument_fn_cases,
    }
    sanity_block = {"failure_count": nfail, "failures": sanity_failures}
    llm_failures_block = {
        "count": len(llm_failures),
        "definition": (
            "Texter som hoppades pga LLMProviderError/Article9LayerError/"
            "CombinationLayerError (#107 probe-resiliens). Effektiv N för "
            "mätvärden = total_texts - count."
        ),
        "cases": llm_failures,
    }

    _write_snapshot(
        _SNAPSHOTS_DIR / f"i7d_legacy{_SNAPSHOT_SUFFIX}.json",
        report_legacy,
        mode="legacy",
        n=n,
        subset_counts=subset_counts,
        commit=commit,
        metadata_extra={
            "instrument_fn": instrument_block,
            "sanity_check": sanity_block,
            "llm_failures": llm_failures_block,
        },
    )
    eb_breakdown = {
        "total": eb_total,
        "context_kombination_only": eb_komb,
        "note": (
            "Endast context.kombination kan bära icke-default evidence_basis "
            "(se Aggregator._apply_evidence_weighting). 'total' räknar alla "
            "predikterade fynd; 'context_kombination_only' är H3:s nämnare."
        ),
    }
    _write_snapshot(
        _SNAPSHOTS_DIR / f"i7d_cross_validating{_SNAPSHOT_SUFFIX}.json",
        report_xval,
        mode="cross_validating",
        n=n,
        subset_counts=subset_counts,
        commit=commit,
        metadata_extra={
            "instrument_fn": instrument_block,
            "sanity_check": sanity_block,
            "llm_failures": llm_failures_block,
        },
        top_level_extra={"evidence_basis_breakdown": eb_breakdown},
    )

    print("\n" + "=" * 60)
    for name, rep in (("legacy", report_legacy),
                      ("cross_validating", report_xval)):
        t = rep.total
        print(f"[{name:17s}] TP={t.tp} FP={t.fp} FN={t.fn} | "
              f"P={t.precision:.2%} R={t.recall:.2%} F1={t.f1:.2%}")
    print(f"Iteration-2-baslinje: P=64.00% R=89.27% F1=74.55%")
    print(f"Mätinstrument-FN (article4.adress → entity.spacy_LOC): "
          f"{len(instrument_fn_cases)}")
    print("evidence_basis (cross_validating, total predikterade):")
    for b in _EVIDENCE_BASES:
        print(f"  {b:28s} tp={eb_total[b]['tp']:3d} fp={eb_total[b]['fp']:3d}")
    print("evidence_basis (cross_validating, endast context.kombination):")
    for b in _EVIDENCE_BASES:
        print(f"  {b:28s} tp={eb_komb[b]['tp']:3d} fp={eb_komb[b]['fp']:3d}")
    if nfail:
        print(f"\nVARNING: {nfail} sanity-avvikelse(r) — dokumenteras i "
              f"Del 8.7 (för litet för att påverka 8.4).")
    if llm_failures:
        print(f"\nVARNING: {len(llm_failures)} text(er) hoppades pga "
              f"LLM-/parse-fel (effektiv N = {n - len(llm_failures)}):")
        for lf in llm_failures:
            print(f"  [{lf['index']}] {lf['error']}")
    print("=" * 60)


def run_degerfors() -> None:
    """Fas 2: isolerad Stockholm/Degerfors-verifikation (4 körningar)."""
    if os.environ.get("LLM_PROVIDER", "ollama").lower() == "ollama":
        check_ollama()
    print(f"Isolerad Degerfors-verifikation (modell={_MODEL})\n")
    layers = _build_layers()
    active_layers = [layer.name for layer in layers]
    aggregators = {
        "legacy": Aggregator(cross_validation_mode="legacy"),
        "cross_validating": Aggregator(
            cross_validation_mode="cross_validating"
        ),
    }
    for tname, text in _DEGERFORS_TEXTS.items():
        all_findings = _detect_once(layers, text)
        for mode, agg in aggregators.items():
            cls = agg.aggregate(all_findings, active_layers)
            print("=" * 70)
            print(f"{tname} | mode={mode}")
            print(f'  text: "{text}"')
            print(
                f"  Classification: "
                f"identifiability={cls.identifiability.value} "
                f"data_class={cls.data_class.value} "
                f"sensitivity={cls.sensitivity.value} "
                f"weakest_evidence_basis={cls.weakest_evidence_basis}"
            )
            print(f"  findings ({len(cls.findings)}):")
            for f in cls.findings:
                print(
                    f"    - {f.category.value} [{f.start}:{f.end}] "
                    f'"{f.text_span}" conf={f.confidence:.2f} '
                    f"source={f.source} evidence_basis={f.evidence_basis}"
                )
    print("=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "I-7d dubbel baslinjemätning legacy mot cross_validating "
            "(detect-once, aggregate-twice)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--degerfors",
        action="store_true",
        help=(
            "Kör endast den isolerade Stockholm/Degerfors-verifikationen "
            "(Fas 2, 2 texter × 2 modes). Default: full korpus (159)."
        ),
    )
    args = parser.parse_args()
    if args.degerfors:
        run_degerfors()
    else:
        run_full()


if __name__ == "__main__":
    main()
