#!/usr/bin/env python3
"""Offline script: generate demo/snapshots/iteration_2_report.json.

Runs the iteration 2 four-layer pipeline against the combined dataset (iteration-1 +
article9 + combination, 159 texts total) and serialises the evaluation report to a
JSON snapshot file that the demo reads at startup.

Requirements:
    - Ollama running locally on http://localhost:11434
    - Model qwen2.5:7b-instruct pulled in Ollama
    - pip install -e ".[all]"

Usage:
    python scripts/build_demo_snapshot.py
"""

from __future__ import annotations

import dataclasses
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import requests  # noqa: E402 (import after sys.path manipulation)

from evaluation.confusion_matrix import ConfusionMatrix  # noqa: E402
from evaluation.dataset.loader import load_dataset  # noqa: E402
from evaluation.matcher import match  # noqa: E402
from evaluation.metrics import f1, precision, recall  # noqa: E402
from evaluation.report import MechanismStats, Report, RunMetrics, SampleResult  # noqa: E402
from gdpr_classifier import Aggregator, Pipeline  # noqa: E402
from gdpr_classifier.config import get_llm_provider  # noqa: E402
from gdpr_classifier.core.category import Category  # noqa: E402
from gdpr_classifier.layers.article9 import Article9Layer  # noqa: E402
from gdpr_classifier.layers.combination import CombinationLayer  # noqa: E402
from gdpr_classifier.layers.entity import EntityLayer  # noqa: E402
from gdpr_classifier.layers.pattern import PatternLayer  # noqa: E402

_MODEL = "qwen2.5:7b-instruct"
_SNAPSHOT_PATH = _PROJECT_ROOT / "demo" / "snapshots" / "iteration_2_report.json"
_DATASET_PATHS = {
    "iteration_1": _PROJECT_ROOT / "tests" / "data" / "iteration_1" / "test_dataset.json",
    "article9": _PROJECT_ROOT / "tests" / "data" / "iteration_2" / "article9_dataset.json",
    "combination": _PROJECT_ROOT / "tests" / "data" / "iteration_2" / "combination_dataset.json",
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


def main() -> None:
    check_ollama()

    print("Laddar dataset...")
    d1 = load_dataset(str(_DATASET_PATHS["iteration_1"]))
    d2 = load_dataset(str(_DATASET_PATHS["article9"]))
    d3 = load_dataset(str(_DATASET_PATHS["combination"]))
    dataset = d1 + d2 + d3
    n = len(dataset)
    print(
        f"Dataset: {n} texter "
        f"({len(d1)} iteration-1 + {len(d2)} artikel-9 + {len(d3)} kombination)"
    )

    print("Skapar pipeline...")
    provider = get_llm_provider(_MODEL)
    pipeline = Pipeline(
        layers=[
            PatternLayer(),
            EntityLayer(),
            Article9Layer(provider),
            CombinationLayer(provider),
        ],
        aggregator=Aggregator(),
    )

    print(f"\nKör utvärdering ({n} texter)...\n")
    cm = ConfusionMatrix()
    samples: list[SampleResult] = []
    mech_counts = dict.fromkeys(["article9", "bypass", "mechanism3", "low", "none"], 0)

    for i, item in enumerate(dataset, 1):
        print(f"  [{i:3d}/{n}] {truncate(item.text)}")
        classification = pipeline.classify(item.text)
        mech = classification.mechanism_used or "none"
        if mech not in mech_counts:
            mech = "none"
        mech_counts[mech] += 1
        mr = match(classification.findings, item.expected_findings)
        cm.add_match_result(mr)
        samples.append(
            SampleResult(
                text=item.text,
                false_positives=list(mr.false_positives),
                false_negatives=list(mr.false_negatives),
            )
        )

    # Compute total metrics
    t_tp, t_fp, t_fn = cm.get_total_stats()
    total_metrics = _calc_metrics(t_tp, t_fp, t_fn)

    # Compute per-category metrics
    categories = set(
        list(cm.category_tp.keys())
        + list(cm.category_fp.keys())
        + list(cm.category_fn.keys())
    )
    per_category: dict[Category, RunMetrics] = {
        cat: _calc_metrics(*cm.get_category_stats(cat)) for cat in categories
    }

    # Compute per-layer metrics
    layers = set(list(cm.layer_tp.keys()) + list(cm.layer_fp.keys()))
    per_layer: dict[str, RunMetrics] = {
        layer: _calc_metrics(*cm.get_layer_stats(layer)) for layer in layers
    }

    report = Report(
        total=total_metrics,
        per_category=per_category,
        per_layer=per_layer,
        samples=samples,
        per_mechanism=MechanismStats(
            high_via_article9=mech_counts["article9"],
            medium_via_bypass=mech_counts["bypass"],
            medium_via_mechanism3=mech_counts["mechanism3"],
            low_count=mech_counts["low"],
            none_count=mech_counts["none"],
        ),
    )

    print(f"\nTotalt: TP={t_tp}, FP={t_fp}, FN={t_fn}")
    print(f"Precision: {total_metrics.precision:.2%}")
    print(f"Recall:    {total_metrics.recall:.2%}")
    print(f"F1:        {total_metrics.f1:.2%}")
    print(
        f"Mekanismer: article9={mech_counts['article9']}, "
        f"bypass={mech_counts['bypass']}, "
        f"mechanism3={mech_counts['mechanism3']}, "
        f"low={mech_counts['low']}, "
        f"none={mech_counts['none']}"
    )

    commit = get_git_commit()
    out = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model": _MODEL,
            "prompt_versions": {"article9": "v5", "combination": "v4"},
            "dataset": {
                "total_texts": n,
                "iteration_1_texts": len(d1),
                "article9_texts": len(d2),
                "combination_texts": len(d3),
            },
            "git_commit": commit,
            "pipeline_layers": ["pattern", "entity", "article9", "combination"],
        },
        "report": dataclasses.asdict(report),
    }

    _SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SNAPSHOT_PATH.write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nSnapshot skrivet till {_SNAPSHOT_PATH.relative_to(_PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
