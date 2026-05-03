#!/usr/bin/env python3
"""Stub-substitution demonstration for Issue #79.

Loads combination_dataset.json and runs two pipeline configurations:

  Run A: Full pipeline with CombinationLayer (requires Ollama + qwen2.5:7b-instruct).
  Run B: Full pipeline with StubCombinationLayer (deterministic, no LLM for Layer 4).

Both runs include Article9Layer which requires Ollama. The script exits with a
clear error message if Ollama is not reachable.

The comparison table is written to stdout and also replaces the placeholder in
docs/iteration_2_layer_substitutability.md (section 2).

Usage:
    python scripts/demonstrations/stub_substitution.py

Requirements:
    - Ollama running locally on http://localhost:11434
    - Model qwen2.5:7b-instruct pulled in Ollama
    - pip install -e ".[all]"
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import requests

from gdpr_classifier import Aggregator, Pipeline
from gdpr_classifier.config import get_llm_provider
from gdpr_classifier.layers.article9 import Article9Layer
from gdpr_classifier.layers.combination import CombinationLayer
from gdpr_classifier.layers.entity import EntityLayer
from gdpr_classifier.layers.llm.provider import LLMProviderError
from gdpr_classifier.layers.pattern import PatternLayer
from tests.fixtures.stub_combination_layer import StubCombinationLayer

_DATASET_PATH = _PROJECT_ROOT / "tests" / "data" / "iteration_2" / "combination_dataset.json"
_DOCS_PATH = _PROJECT_ROOT / "docs" / "iteration_2_layer_substitutability.md"
_PLACEHOLDER = "<!-- TABLE_PLACEHOLDER -->"
_MODEL = "qwen2.5:7b-instruct"
_TEXT_TRUNCATE = 80


def check_ollama() -> None:
    """Exit with a clean error message if Ollama is not reachable."""
    try:
        requests.get("http://localhost:11434/api/tags", timeout=5).raise_for_status()
    except Exception as exc:
        print(
            f"ERROR: Ollama inte tillgänglig på http://localhost:11434 - {exc}\n"
            "Starta Ollama (ollama serve) och försök igen.",
            file=sys.stderr,
        )
        sys.exit(1)


def classify_text(pipeline: Pipeline, text: str) -> tuple[str, str, int] | None:
    """Classify a single text; returns (sensitivity, mechanism_used, findings_count) or None on error."""
    try:
        result = pipeline.classify(text)
        return (
            result.sensitivity.value,
            result.mechanism_used,
            len(result.findings),
        )
    except LLMProviderError as exc:
        print(f"  VARNING: LLMProviderError - {exc}", file=sys.stderr)
        return None


def truncate(text: str, max_len: int = _TEXT_TRUNCATE) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def build_table(texts: list[str], results_a: list, results_b: list) -> str:
    """Build a markdown comparison table from classification results."""
    header = (
        "| Text (<=80 tecken) | Sens A | Mek A | Fynd A | Sens B | Mek B | Fynd B |\n"
        "|---|---|---|---|---|---|---|\n"
    )
    rows = []
    for text, res_a, res_b in zip(texts, results_a, results_b):
        cell_text = truncate(text).replace("|", "\\|")
        if res_a is None:
            sa, ma, fa = "FEL", "-", "-"
        else:
            sa, ma, fa = res_a[0], res_a[1], str(res_a[2])
        if res_b is None:
            sb, mb, fb = "FEL", "-", "-"
        else:
            sb, mb, fb = res_b[0], res_b[1], str(res_b[2])
        rows.append(f"| {cell_text} | {sa} | {ma} | {fa} | {sb} | {mb} | {fb} |")

    return header + "\n".join(rows)


def update_docs(table_md: str) -> None:
    """Replace the TABLE_PLACEHOLDER in the docs file with the comparison table."""
    if not _DOCS_PATH.exists():
        print(
            f"VARNING: {_DOCS_PATH} hittades inte - tabellen skrivs inte till fil.",
            file=sys.stderr,
        )
        return
    content = _DOCS_PATH.read_text(encoding="utf-8")
    if _PLACEHOLDER not in content:
        print(
            f"VARNING: Placeholder '{_PLACEHOLDER}' saknas i {_DOCS_PATH.name} - "
            "tabellen skrivs inte till fil.",
            file=sys.stderr,
        )
        return
    updated = content.replace(_PLACEHOLDER, table_md)
    _DOCS_PATH.write_text(updated, encoding="utf-8")
    print(f"Tabell skriven till {_DOCS_PATH.relative_to(_PROJECT_ROOT)}")


def main() -> None:
    check_ollama()

    dataset = json.loads(_DATASET_PATH.read_text(encoding="utf-8"))
    texts = [entry["text"] for entry in dataset]

    print(f"Dataset: {len(texts)} texter från {_DATASET_PATH.name}")
    print("Skapar pipelines...")

    provider = get_llm_provider(_MODEL)
    pipeline_a = Pipeline(
        layers=[PatternLayer(), EntityLayer(), Article9Layer(provider), CombinationLayer(provider)],
        aggregator=Aggregator(),
    )
    pipeline_b = Pipeline(
        layers=[PatternLayer(), EntityLayer(), Article9Layer(provider), StubCombinationLayer()],
        aggregator=Aggregator(),
    )

    print(f"\nKörning A: CombinationLayer ({_MODEL})...")
    results_a = []
    for i, text in enumerate(texts, 1):
        print(f"  [{i:2d}/{len(texts)}] {truncate(text, 60)}")
        results_a.append(classify_text(pipeline_a, text))

    print(f"\nKörning B: StubCombinationLayer...")
    results_b = []
    for i, text in enumerate(texts, 1):
        print(f"  [{i:2d}/{len(texts)}] {truncate(text, 60)}")
        results_b.append(classify_text(pipeline_b, text))

    table_md = build_table(texts, results_a, results_b)

    print("\n\n## Jämförelsetabell: CombinationLayer (A) vs StubCombinationLayer (B)\n")
    print(table_md)

    update_docs(table_md)


if __name__ == "__main__":
    main()
