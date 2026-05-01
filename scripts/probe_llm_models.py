#!/usr/bin/env python3
"""Probe script for Ollama model evaluation (Issue #84).

Evaluates local Ollama models on JSON output validity and Swedish language
comprehension for GDPR Article 9-like classification tasks.  Produces a
markdown results file with a summary table and per-prompt details.

Usage:
    python scripts/probe_llm_models.py --models llama3.1:8b qwen2.5:7b-instruct

Optional flags:
    --output-dir DIR       Directory for the results file (default: scripts/)
    --temperature FLOAT    Sampling temperature (default: 0.0)
    --runs-per-prompt INT  Runs per prompt for latency averaging (default: 1)

Requirements:
    - Ollama running locally on http://localhost:11434
    - pip install -e ".[llm]"  (requests, pyyaml already in [llm] group)
"""

from __future__ import annotations

import argparse
import json
import unicodedata
import logging
import statistics
import subprocess
import sys
import time
import math
from datetime import date
from pathlib import Path

import requests

# Ensure project root is on sys.path so we can import gdpr_classifier
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from gdpr_classifier.layers.llm.ollama_provider import OllamaProvider
from gdpr_classifier.layers.llm.provider import LLMProviderError
from scripts.probe_prompts import (
    PROMPTS_CATEGORY_A,
    PROMPTS_CATEGORY_B,
    ProbePrompt,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OLLAMA_BASE_URL = "http://localhost:11434"
JSON_VALIDITY_THRESHOLD = 0.9  # 90% — disqualification rule


# ---------------------------------------------------------------------------
# Data structures for results
# ---------------------------------------------------------------------------


class PromptResult:
    """Result of running a single probe prompt against a model."""

    __slots__ = (
        "prompt_id",
        "category",
        "success",
        "latency_s",
        "error_message",
        "raw_response",
    )

    def __init__(
        self,
        prompt_id: str,
        category: str,
        success: bool,
        latency_s: float,
        error_message: str = "",
        raw_response: dict | None = None,
    ) -> None:
        self.prompt_id = prompt_id
        self.category = category
        self.success = success
        self.latency_s = latency_s
        self.error_message = error_message
        self.raw_response = raw_response


class ModelResult:
    """Aggregated results for a single model."""

    __slots__ = (
        "model_name",
        "model_size",
        "prompt_results",
        "json_valid",
        "json_total",
        "swedish_correct",
        "swedish_total",
    )

    def __init__(self, model_name: str, model_size: str) -> None:
        self.model_name = model_name
        self.model_size = model_size
        self.prompt_results: list[PromptResult] = []
        self.json_valid = 0
        self.json_total = 0
        self.swedish_correct = 0
        self.swedish_total = 0

    @property
    def all_latencies(self) -> list[float]:
        return [r.latency_s for r in self.prompt_results]

    @property
    def mean_latency(self) -> float:
        lats = self.all_latencies
        return statistics.mean(lats) if lats else 0.0

    @property
    def p95_latency(self) -> float:
        lats = sorted(self.all_latencies)
        if not lats:
            return 0.0
        idx = int(len(lats) * 0.95)
        # Clamp to last element if index is at the boundary
        return lats[min(idx, len(lats) - 1)]


# ---------------------------------------------------------------------------
# Ollama connectivity & model checks
# ---------------------------------------------------------------------------


def check_ollama_connection() -> list[str]:
    """Check that Ollama is running and return list of available model names.

    Raises SystemExit if Ollama is not reachable.
    """
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return [m["name"] for m in data.get("models", [])]
    except requests.exceptions.RequestException as exc:
        print(
            f"\n❌ Kan inte ansluta till Ollama på {OLLAMA_BASE_URL}: {exc}\n"
            "   Se till att Ollama körs (ollama serve) och försök igen.",
            file=sys.stderr,
        )
        sys.exit(1)


def get_model_size(model_name: str) -> str:
    """Get model size string via 'ollama show'.

    Returns 'okänd' if the command fails.
    """
    try:
        result = subprocess.run(
            ["ollama", "show", model_name],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return "okänd"
        # Parse output for parameter size / file size info
        for line in result.stdout.splitlines():
            lower = line.lower()
            if "size" in lower or "parameter" in lower:
                # Typical line: "  parameters    8.0B" or "  size    4.7 GB"
                parts = line.split()
                if len(parts) >= 2:
                    return " ".join(parts[1:])
        return "okänd"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "okänd"


# ---------------------------------------------------------------------------
# Category normalization
# ---------------------------------------------------------------------------


def _normalize_category(value: str | None) -> str | None:
    """Normalize a category string for comparison.

    Applied to both expected and actual category values before comparison,
    so that semantically correct answers in variant format are accepted.

    Normalization steps:
      1. Return None if input is None
      2. Strip whitespace
      3. Lowercase
      4. NFKD-normalize and filter to ASCII (removes diacritics:
         å→a, ä→a, ö→o, é→e, etc.)
      5. Replace spaces and hyphens with underscores
      6. Return empty string as None

    This handles observed format variations from the first probe run
    (Issue #84, 2026-05-01):
      - "hälsodata"  → "halsodata"  (diacritics)
      - "Hälsodata"  → "halsodata"  (casing + diacritics)
      - "etniskt ursprung" → "etniskt_ursprung"  (space → underscore)
      - "politisk åsikt" → "politisk_asikt"  (diacritics + space)

    It does NOT translate between languages, so "religious_belief"
    remains "religious_belief" and correctly fails against
    "religios_overtygelse".
    """
    if value is None:
        return None

    value = value.strip().lower()

    # NFKD decomposition splits characters into base + combining marks,
    # then we filter out the combining marks to get ASCII approximation.
    nfkd = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(c for c in nfkd if not unicodedata.combining(c))

    # Normalize separators: spaces and hyphens become underscores
    ascii_value = ascii_value.replace(" ", "_").replace("-", "_")

    if ascii_value == "" or ascii_value == "null":
        return None

    return ascii_value


# ---------------------------------------------------------------------------
# Prompt evaluation
# ---------------------------------------------------------------------------


def evaluate_prompt(
    provider: OllamaProvider,
    prompt: ProbePrompt,
    runs: int,
) -> PromptResult:
    """Run a single probe prompt against the provider and evaluate the result."""

    combined_prompt = f"{prompt.task_prompt}\n\nText: {prompt.text}"
    latencies: list[float] = []
    last_error = ""
    last_response: dict | None = None

    for _ in range(runs):
        t0 = time.perf_counter()
        try:
            response = provider.generate_json(
                prompt=combined_prompt,
                system_prompt=prompt.system_prompt,
            )
            elapsed = time.perf_counter() - t0
            latencies.append(elapsed)
            last_response = response
        except LLMProviderError as exc:
            elapsed = time.perf_counter() - t0
            latencies.append(elapsed)
            last_error = str(exc)
            return PromptResult(
                prompt_id=prompt.id,
                category=prompt.category,
                success=False,
                latency_s=statistics.mean(latencies),
                error_message=f"LLMProviderError: {exc}",
            )

    latency = statistics.mean(latencies)

    # Evaluate correctness based on category
    if prompt.category == "A":
        return _evaluate_json_validity(prompt, last_response, latency)
    else:
        return _evaluate_swedish_correctness(prompt, last_response, latency)


def _evaluate_json_validity(
    prompt: ProbePrompt,
    response: dict | None,
    latency: float,
) -> PromptResult:
    """Check that all expected JSON keys are present in the response."""
    if response is None:
        return PromptResult(
            prompt_id=prompt.id,
            category=prompt.category,
            success=False,
            latency_s=latency,
            error_message="Inget svar",
        )

    missing = prompt.expected_json_keys - set(response.keys())
    if missing:
        return PromptResult(
            prompt_id=prompt.id,
            category=prompt.category,
            success=False,
            latency_s=latency,
            error_message=f"Saknade nycklar: {missing}",
            raw_response=response,
        )

    return PromptResult(
        prompt_id=prompt.id,
        category=prompt.category,
        success=True,
        latency_s=latency,
        raw_response=response,
    )


def _evaluate_swedish_correctness(
    prompt: ProbePrompt,
    response: dict | None,
    latency: float,
) -> PromptResult:
    """Key-matching against expected_classification with category normalization.

    contains_sensitive is compared strictly (boolean).
    category is compared after _normalize_category (handles diacritics,
    casing, and space/underscore variation).
    """
    if response is None or prompt.expected_classification is None:
        return PromptResult(
            prompt_id=prompt.id,
            category=prompt.category,
            success=False,
            latency_s=latency,
            error_message="Inget svar eller inget förväntat resultat",
        )

    expected = prompt.expected_classification

    # Check contains_sensitive (strict boolean comparison)
    got_sensitive = response.get("contains_sensitive")
    exp_sensitive = expected["contains_sensitive"]
    if got_sensitive != exp_sensitive:
        return PromptResult(
            prompt_id=prompt.id,
            category=prompt.category,
            success=False,
            latency_s=latency,
            error_message=(
                f"contains_sensitive: förväntat {exp_sensitive}, fick {got_sensitive}"
            ),
            raw_response=response,
        )

    # Check category — normalize both sides before comparison
    got_category_raw = response.get("category")
    exp_category_raw = expected["category"]
    got_category = _normalize_category(got_category_raw)
    exp_category = _normalize_category(exp_category_raw)

    if got_category != exp_category:
        return PromptResult(
            prompt_id=prompt.id,
            category=prompt.category,
            success=False,
            latency_s=latency,
            error_message=(
                f'category: förväntat "{exp_category_raw}" '
                f'(→"{exp_category}"), fick "{got_category_raw}" '
                f'(→"{got_category}")'
            ),
            raw_response=response,
        )

    return PromptResult(
        prompt_id=prompt.id,
        category=prompt.category,
        success=True,
        latency_s=latency,
        raw_response=response,
    )


# ---------------------------------------------------------------------------
# Model evaluation orchestration
# ---------------------------------------------------------------------------


def evaluate_model(
    model_name: str,
    temperature: float,
    runs_per_prompt: int,
) -> ModelResult:
    """Evaluate a single model against all probe prompts."""

    size = get_model_size(model_name)
    result = ModelResult(model_name=model_name, model_size=size)

    provider = OllamaProvider(
        model_name=model_name,
        temperature=temperature,
    )

    all_prompts = PROMPTS_CATEGORY_A + PROMPTS_CATEGORY_B

    for prompt in all_prompts:
        pr = evaluate_prompt(provider, prompt, runs=runs_per_prompt)
        result.prompt_results.append(pr)

        # Tally per-category scores
        if prompt.category == "A":
            result.json_total += 1
            if pr.success:
                result.json_valid += 1
        else:
            result.swedish_total += 1
            if pr.success:
                result.swedish_correct += 1

        # Live stdout output
        icon = "✅" if pr.success else "❌"
        label = (
            "JSON OK"
            if prompt.category == "A"
            else ("Korrekt" if pr.success else f"Fel — {pr.error_message}")
        )
        print(f"  [{model_name}] {prompt.id}: {icon} {label}  ({pr.latency_s:.2f}s)")

    return result


# ---------------------------------------------------------------------------
# Results file generation
# ---------------------------------------------------------------------------


def generate_results_markdown(
    results: list[ModelResult],
    temperature: float,
    runs_per_prompt: int,
) -> str:
    """Generate a markdown results report."""
    today = date.today().isoformat()
    lines: list[str] = []

    lines.append("# Probe-resultat: Ollama-modellval\n")
    lines.append(f"**Datum:** {today}  ")
    lines.append(f"**Temperatur:** {temperature}  ")
    lines.append(f"**Körningar per prompt:** {runs_per_prompt}  ")
    lines.append(
        "**Kontext:** Spike för att empiriskt motivera val av lokal Ollama-modell "
        "inför Article9Layer (#70) och CombinationLayer (#72).\n"
    )
    lines.append(
        "> **Normalisering:** Kategori-fältet normaliseras före jämförelse: "
        "lowercase, diakritik borttagen (å→a, ä→a, ö→o), mellanslag/bindestreck→underscore. "
        'Semantiskt korrekta svar i annat format (t.ex. "hälsodata" vs "halsodata", '
        '"etniskt ursprung" vs "etniskt_ursprung") godkänns. Svar på fel språk '
        '(t.ex. "religious_belief") räknas fortfarande som felaktiga.\n'
    )

    # Summary table
    lines.append("## Sammanfattning\n")
    lines.append(
        "| Modell | JSON-validitet | Svensk-korrekt | "
        "Snitt-latens | P95-latens | Storlek |"
    )
    lines.append(
        "|--------|---------------|----------------|"
        "-------------|-----------|---------|"
    )

    for r in results:
        json_pct = f"{r.json_valid}/{r.json_total}" if r.json_total > 0 else "N/A"
        swe_pct = (
            f"{r.swedish_correct}/{r.swedish_total}" if r.swedish_total > 0 else "N/A"
        )
        lines.append(
            f"| {r.model_name} | {json_pct} | {swe_pct} | "
            f"{r.mean_latency:.2f}s | {r.p95_latency:.2f}s | {r.model_size} |"
        )

    # Disqualification rule
    lines.append("\n## Diskvalificeringsregel\n")
    required_json = math.ceil(len(PROMPTS_CATEGORY_A) * JSON_VALIDITY_THRESHOLD)
    lines.append(
        f"Modeller under {JSON_VALIDITY_THRESHOLD:.0%} JSON-validitet "
        f"(< {required_json}/{len(PROMPTS_CATEGORY_A)} "
        "på Kategori A) är inte aktuella oavsett språk-prestanda.\n"
    )

    # Per-prompt details
    lines.append("## Per-prompt-detaljer\n")
    for r in results:
        lines.append(f"<details>")
        lines.append(f"<summary>{r.model_name} — detaljer</summary>\n")
        lines.append("| Prompt | Resultat | Latens | Kommentar |")
        lines.append("|--------|---------|-------|-----------|")

        for pr in r.prompt_results:
            icon = "✅" if pr.success else "❌"
            comment = pr.error_message if pr.error_message else ""
            lines.append(
                f"| {pr.prompt_id} | {icon} | {pr.latency_s:.2f}s | {comment} |"
            )

        lines.append("\n</details>\n")

    # Recommendation
    lines.append("## Rekommendation\n")
    lines.append(_generate_recommendation(results))

    return "\n".join(lines)


def _generate_recommendation(results: list[ModelResult]) -> str:
    """Generate a prose recommendation based on the results."""
    if not results:
        return "Inga modeller utvärderades.\n"

    qualified = [
        r
        for r in results
        if r.json_total > 0 and (r.json_valid / r.json_total) >= JSON_VALIDITY_THRESHOLD
    ]
    disqualified = [r for r in results if r not in qualified]

    parts: list[str] = []

    if disqualified:
        names = ", ".join(r.model_name for r in disqualified)
        parts.append(
            f"Diskvalificerade modeller (under {JSON_VALIDITY_THRESHOLD:.0%} "
            f"JSON-validitet): {names}."
        )

    if not qualified:
        parts.append(
            "Ingen modell uppnådde tillräcklig JSON-validitet. "
            "Överväg att testa andra modeller eller justera prompterna."
        )
        return "\n".join(parts) + "\n"

    # Sort qualified by: swedish_correct (desc), then mean_latency (asc)
    qualified.sort(
        key=lambda r: (-r.swedish_correct, r.mean_latency),
    )

    best = qualified[0]
    parts.append(
        f"Av kvalificerade modeller presterar **{best.model_name}** bäst "
        f"med {best.swedish_correct}/{best.swedish_total} korrekt "
        f"svensk-klassificering och {best.json_valid}/{best.json_total} "
        f"JSON-validitet."
    )
    parts.append(
        f"Snittlatens: {best.mean_latency:.2f}s, "
        f"P95-latens: {best.p95_latency:.2f}s, "
        f"storlek: {best.model_size}."
    )

    if len(qualified) > 1:
        runner_up = qualified[1]
        parts.append(
            f"Näst bästa alternativ: **{runner_up.model_name}** med "
            f"{runner_up.swedish_correct}/{runner_up.swedish_total} "
            f"svensk-korrekt och snittlatens {runner_up.mean_latency:.2f}s."
        )

    parts.append(
        f"\nRekommendation: **{best.model_name}** som primär modell "
        f"för Article9Layer och CombinationLayer. Modellen uppfyller "
        f"JSON-validitetskravet (≥ {JSON_VALIDITY_THRESHOLD:.0%}) och "
        f"visar bäst prestanda på svensk språkförståelse bland testade "
        f"alternativ."
    )
    parts.append(
        "OBS: Denna rekommendation baseras på ett begränsat probe-set "
        "(14 prompts) och bör valideras vidare vid implementation av "
        "#70 och #72. Skriptet kan köras igen i iteration 3 om "
        "modellvalet behöver omprövas."
    )

    return "\n".join(parts) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Probe Ollama models for JSON validity and Swedish language "
            "comprehension on GDPR Article 9-like tasks."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/probe_llm_models.py "
            "--models llama3.1:8b qwen2.5:7b-instruct\n"
            "  python scripts/probe_llm_models.py "
            "--models mistral:7b --temperature 0.1 --output-dir results/"
        ),
    )
    parser.add_argument(
        "--models",
        nargs="+",
        required=True,
        help="Ollama model names to evaluate (e.g. llama3.1:8b qwen2.5:7b-instruct)",
    )
    parser.add_argument(
        "--output-dir",
        default="scripts/",
        help="Directory for the results markdown file (default: scripts/)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature (default: 0.0, deterministic)",
    )
    parser.add_argument(
        "--runs-per-prompt",
        type=int,
        default=1,
        help="Number of runs per prompt for latency averaging (default: 1)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.runs_per_prompt < 1:
        print("--runs-per-prompt must be at least 1.", file=sys.stderr)
        sys.exit(2)

    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    print("=" * 60)
    print("  Probe: Ollama-modellval (Issue #84)")
    print("=" * 60)
    print(f"  Modeller:  {', '.join(args.models)}")
    print(f"  Temperatur: {args.temperature}")
    print(f"  Körningar/prompt: {args.runs_per_prompt}")
    print(
        f"  Antal prompts: {len(PROMPTS_CATEGORY_A)} (A) + "
        f"{len(PROMPTS_CATEGORY_B)} (B) = "
        f"{len(PROMPTS_CATEGORY_A) + len(PROMPTS_CATEGORY_B)}"
    )
    print("=" * 60)

    # Check Ollama connectivity and get available models
    available_models = check_ollama_connection()
    available_names = set(available_models)
    print(f"\n✅ Ollama ansluten. {len(available_models)} modell(er) tillgängliga.")

    # Evaluate each model
    all_results: list[ModelResult] = []

    for model_name in args.models:
        # Check if model is available (handle both exact and fuzzy matching)
        if model_name in available_names:
            resolved_model = model_name
        else:
            matches = [m for m in available_names if m.startswith(model_name)]
            if len(matches) == 1:
                resolved_model = matches[0]
            else:
                resolved_model = None

        if resolved_model is None:
            print(
                f"\n Modell '{model_name}' finns inte lokalt. "
                f"Hoppar över. (Tillgängliga: {', '.join(sorted(available_names))})",
                file=sys.stderr,
            )
            continue

        print(f"\n{'─' * 50}")
        print(f"  Utvärderar: {resolved_model}")
        print(f"{'─' * 50}")

        result = evaluate_model(
            model_name=resolved_model,
            temperature=args.temperature,
            runs_per_prompt=args.runs_per_prompt,
        )
        all_results.append(result)

        # Print model summary
        print(
            f"\n  Resultat {resolved_model}: "
            f"JSON {result.json_valid}/{result.json_total}, "
            f"Svensk {result.swedish_correct}/{result.swedish_total}, "
            f"Latens snitt {result.mean_latency:.2f}s"
        )

    if not all_results:
        print(
            "\n❌ Inga modeller utvärderades. Kontrollera att modellnamnen "
            "är korrekta och att modellerna finns lokalt.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Generate and write results file
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    output_path = output_dir / f"probe_results_{today}.md"

    markdown = generate_results_markdown(
        results=all_results,
        temperature=args.temperature,
        runs_per_prompt=args.runs_per_prompt,
    )
    output_path.write_text(markdown, encoding="utf-8")

    print(f"\n{'=' * 60}")
    print(f"  Resultatfil sparad: {output_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
