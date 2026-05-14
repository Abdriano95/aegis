"""Empirical token measurement of Article9Layer and CombinationLayer prompts.

Part of I-6 (Issue #106) pause investigation. Verifies whether OllamaProvider's
implicit num_ctx=4096 default may have silently truncated prompts during
iteration 2 and iteration 3 LLM-based evaluation.

Uses the exact same prompt-loading and prompt-assembly code paths as the
pipeline (gdpr_classifier.prompts.loader.load_prompt and the inline user-prompt
template used by Article9Layer and CombinationLayer). No parallel implementation.

Outputs:
    - Stdout: structured summary per layer, validation, A/B/C verdict.
    - Markdown: docs/iteration_3_token_measurement.md (configurable).

Tokenizer:
    - Primary: tiktoken cl100k_base.
    - Secondary (validation): transformers AutoTokenizer for Qwen2.5-7B-Instruct
      on a deterministic 10-prompt sample, if installed and reachable.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path

import tiktoken

from gdpr_classifier.prompts.loader import load_prompt
from evaluation.dataset.loader import load_dataset


REPO_ROOT = Path(__file__).resolve().parent.parent

ARTICLE9_VERSION = "latest"   # matches Article9Layer default
COMBINATION_VERSION = "v5"    # matches CombinationLayer default (iteration 3 baseline pin)

# Thresholds (spec § Uppgift 2)
OVER_LIMIT = 4096
WARNING_LIMIT = 3500
BORDERLINE_MIN = 3800
BORDERLINE_MAX = 4096
BORDERLINE_PCT = 1.0
TRUNCATION_PCT = 5.0


def build_user_prompt(assembled_prompt: str, text: str) -> str:
    """Replicate Article9Layer/CombinationLayer user-prompt construction verbatim.

    Source: gdpr_classifier/layers/article9/article9_layer.py:58-60
            gdpr_classifier/layers/combination/combination_layer.py:62-64
    """
    return f"{assembled_prompt}\n\nText att analysera:\n<<<\n{text}\n>>>\n"


@dataclass
class PromptMeasurement:
    idx: int
    prompt_tokens: int
    effective_tokens: int
    categories: list[str]


@dataclass
class CategoryStats:
    count: int = 0
    max_effective: int = 0
    over_4096: int = 0


@dataclass
class DatasetReport:
    layer: str
    dataset_path: str
    prompt_version: str
    measurements: list[PromptMeasurement] = field(default_factory=list)
    per_category: dict[str, CategoryStats] = field(default_factory=dict)
    skipped: bool = False
    skip_reason: str = ""

    @property
    def n(self) -> int:
        return len(self.measurements)

    def quantiles(self, attr: str) -> dict[str, int]:
        values = [getattr(m, attr) for m in self.measurements]
        if not values:
            return {"min": 0, "median": 0, "p75": 0, "p90": 0, "max": 0}
        values_sorted = sorted(values)
        return {
            "min": values_sorted[0],
            "median": int(statistics.median(values_sorted)),
            "p75": _percentile(values_sorted, 75),
            "p90": _percentile(values_sorted, 90),
            "max": values_sorted[-1],
        }

    def count_over(self, threshold: int) -> int:
        return sum(1 for m in self.measurements if m.effective_tokens > threshold)

    def top_n_longest(self, n: int = 5) -> list[PromptMeasurement]:
        return sorted(self.measurements, key=lambda m: m.effective_tokens, reverse=True)[:n]


def _percentile(sorted_values: list[int], pct: float) -> int:
    if not sorted_values:
        return 0
    k = (len(sorted_values) - 1) * pct / 100.0
    f, c = int(k), min(int(k) + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    return int(sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f))


def _display_path(p: Path) -> str:
    try:
        return p.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(p)


def measure_dataset(
    layer: str,
    dataset_path: Path,
    prompt_version: str,
    encoder: tiktoken.Encoding,
    output_buffer: int,
    category_prefix: str,
) -> DatasetReport:
    """Measure tokens for every text in a dataset using the given layer's prompt."""
    report = DatasetReport(
        layer=layer,
        dataset_path=_display_path(dataset_path),
        prompt_version=prompt_version,
    )

    if not dataset_path.exists():
        report.skipped = True
        report.skip_reason = f"file does not exist: {_display_path(dataset_path)}"
        return report

    prompt = load_prompt(layer, version=prompt_version)
    system_token_count = len(encoder.encode(prompt.system_prompt))

    dataset = load_dataset(str(dataset_path))

    # iteration_1 special case: only measure for Article9 if any record has article9.*
    # findings. iteration_2/iteration_3 article9 datasets are measured in full
    # (negative examples still go through the layer in production).
    if category_prefix == "article9." and dataset_path.parent.name == "iteration_1":
        has_a9 = any(
            f.category.value.startswith("article9.")
            for lt in dataset for f in lt.expected_findings
        )
        if not has_a9:
            report.skipped = True
            report.skip_reason = (
                f"no article9.* records in {dataset_path.name} "
                "(iteration_1 contains article4/context only)"
            )
            return report

    for idx, lt in enumerate(dataset):
        user_prompt = build_user_prompt(prompt.assembled_prompt, lt.text)
        prompt_tokens = system_token_count + len(encoder.encode(user_prompt))
        effective = prompt_tokens + output_buffer

        cats = sorted({
            f.category.value
            for f in lt.expected_findings
            if f.category.value.startswith(category_prefix)
        })
        m = PromptMeasurement(
            idx=idx,
            prompt_tokens=prompt_tokens,
            effective_tokens=effective,
            categories=cats,
        )
        report.measurements.append(m)

        for cat in cats or ["(no_category)"]:
            entry = report.per_category.setdefault(cat, CategoryStats())
            entry.count += 1
            entry.max_effective = max(entry.max_effective, effective)
            if effective > OVER_LIMIT:
                entry.over_4096 += 1

    return report


def validate_with_qwen(
    article9_reports: list[DatasetReport],
    combination_reports: list[DatasetReport],
    tiktoken_encoder: tiktoken.Encoding,
    skip: bool,
) -> dict:
    """Sample 10 prompts and compare tiktoken cl100k_base vs Qwen2.5 tokenizer."""
    if skip:
        return {"status": "skipped", "reason": "--skip-validation"}

    try:
        from transformers import AutoTokenizer  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"status": "skipped", "reason": f"transformers not available: {exc}"}

    try:
        qwen_tok = AutoTokenizer.from_pretrained(
            "Qwen/Qwen2.5-7B-Instruct", use_fast=True
        )
    except Exception as exc:
        return {"status": "skipped", "reason": f"Qwen2.5 tokenizer load failed: {exc}"}

    rng = random.Random(42)

    def _gather(reports: list[DatasetReport], k: int) -> list[tuple[str, str, str]]:
        """Re-assemble prompts for sample texts (need full prompt string for tokenization)."""
        out = []
        for r in reports:
            if r.skipped or not r.measurements:
                continue
            prompt = load_prompt(r.layer, version=r.prompt_version)
            ds_path = Path(r.dataset_path)
            if not ds_path.is_absolute():
                ds_path = REPO_ROOT / ds_path
            dataset = load_dataset(str(ds_path))
            # Sample by measurement index
            available_indices = [m.idx for m in r.measurements]
            pick = rng.sample(available_indices, min(k, len(available_indices)))
            for idx in pick:
                text = dataset[idx].text
                user_prompt = build_user_prompt(prompt.assembled_prompt, text)
                full = prompt.system_prompt + "\n\n" + user_prompt
                out.append((f"{r.layer}#{idx}", full, prompt.system_prompt))
            if out:
                break  # take from first non-empty report
        return out

    article9_samples = _gather(article9_reports, 5)
    combination_samples = _gather(combination_reports, 5)
    samples = article9_samples + combination_samples

    if not samples:
        return {"status": "skipped", "reason": "no measurable prompts to sample"}

    rows = []
    deviations = []
    for tag, full, _sys in samples:
        tk = len(tiktoken_encoder.encode(full))
        qw = len(qwen_tok.encode(full))
        dev_pct = (tk - qw) / qw * 100.0 if qw else 0.0
        rows.append({"tag": tag, "tiktoken": tk, "qwen2": qw, "deviation_pct": dev_pct})
        deviations.append(dev_pct)

    mean_dev = statistics.mean(deviations) if deviations else 0.0
    # Spec § 1d: "medelavvikelse är över 10 procent uppåt
    # (tiktoken underskattar med mer än 10 procent)" → flag as OTILLRÄCKLIG.
    # tiktoken underestimates ↔ tk < qw ↔ deviation_pct negative.
    # "tiktoken underskattar med mer än 10 %" ↔ mean_dev < -10.
    credibility = "OTILLRÄCKLIG" if mean_dev < -10.0 else "OK"
    return {
        "status": "ok",
        "rows": rows,
        "mean_deviation_pct": mean_dev,
        "credibility": credibility,
    }


def classify_outcome(reports: list[DatasetReport]) -> tuple[str, str]:
    """Return (A/B/C, explanation) per spec Uppgift 2."""
    real = [r for r in reports if not r.skipped and r.measurements]
    if not real:
        return ("?", "Inga mätbara dataset (alla skippade).")

    total = sum(r.n for r in real)
    over_4096 = sum(r.count_over(OVER_LIMIT) for r in real)
    pct_over = (over_4096 / total * 100.0) if total else 0.0

    # Per-category max evaluation
    max_effective_overall = max(
        (max(m.effective_tokens for m in r.measurements) for r in real),
        default=0,
    )
    cat_max = 0
    for r in real:
        for stats in r.per_category.values():
            cat_max = max(cat_max, stats.max_effective)

    # C: > 5 % OR någon kategori har max > 4096
    if pct_over > TRUNCATION_PCT or cat_max > OVER_LIMIT:
        return (
            "C",
            f"Trunkering bekräftad: {over_4096}/{total} texter ({pct_over:.2f}%) "
            f"har effective_tokens > {OVER_LIMIT}; max kategorivärde {cat_max}. "
            f"num_ctx-fix krävs och iteration 2/3:s LLM-baserade utvärdering "
            f"behöver köras om mot fixad provider.",
        )

    # B: 1-5 % OR någon kategori har max i [3800, 4096]
    in_borderline = (
        (BORDERLINE_PCT < pct_over <= TRUNCATION_PCT)
        or (BORDERLINE_MIN <= cat_max <= BORDERLINE_MAX)
    )
    if in_borderline:
        return (
            "B",
            f"Borderline: {over_4096}/{total} texter ({pct_over:.2f}%) över {OVER_LIMIT}, "
            f"max kategorivärde {cat_max} (borderline-intervall {BORDERLINE_MIN}-{BORDERLINE_MAX}). "
            f"num_ctx-fix krävs; behov av omkörning bör diskuteras med arkitekt-instans.",
        )

    # A: 0 över 4096 och ingen borderline
    if over_4096 == 0:
        return (
            "A",
            f"Inga trunkerade prompts: 0/{total} texter över {OVER_LIMIT} effective_tokens "
            f"(max kategorivärde {cat_max}, max overall {max_effective_overall}). "
            f"num_ctx-fix kan göras som arkitekturhärdning utan omkörning.",
        )

    # Edge: 0 < pct_over <= 1 % och ingen kategori i borderline → klassificera som B
    return (
        "B",
        f"Borderline (svag): {over_4096}/{total} texter ({pct_over:.2f}%) över {OVER_LIMIT}. "
        f"Diskutera selektiv omkörning med arkitekt-instans.",
    )


def render_stdout(
    article9_reports: list[DatasetReport],
    combination_reports: list[DatasetReport],
    validation: dict,
    verdict: tuple[str, str],
    output_buffer: int,
) -> str:
    lines: list[str] = []

    def _section(layer_label: str, reports: list[DatasetReport]) -> None:
        lines.append(f"=== Token-mätning: {layer_label} ===")
        for r in reports:
            if r.skipped:
                lines.append(f"Dataset: {r.dataset_path}")
                lines.append(f"  SKIPPED: {r.skip_reason}")
                continue
            pq = r.quantiles("prompt_tokens")
            eq = r.quantiles("effective_tokens")
            over = r.count_over(OVER_LIMIT)
            warn = r.count_over(WARNING_LIMIT)
            pct_over = (over / r.n * 100.0) if r.n else 0.0
            pct_warn = (warn / r.n * 100.0) if r.n else 0.0
            lines.append(f"Dataset: {r.dataset_path}  (prompt version: {r.prompt_version})")
            lines.append(f"Antal texter: {r.n}")
            lines.append(
                f"Prompt-tokens (system + user, utan output-buffert): "
                f"min={pq['min']}, median={pq['median']}, "
                f"p75={pq['p75']}, p90={pq['p90']}, max={pq['max']}"
            )
            lines.append(
                f"Effective-tokens (prompt + {output_buffer}): "
                f"min={eq['min']}, median={eq['median']}, "
                f"p75={eq['p75']}, p90={eq['p90']}, max={eq['max']}"
            )
            lines.append(f"Texter med effective > {OVER_LIMIT}: {over} ({pct_over:.2f}%)")
            lines.append(
                f"Texter med effective > {WARNING_LIMIT} (varning): {warn} ({pct_warn:.2f}%)"
            )
            lines.append("")
        lines.append("")

    _section("Article9Layer", article9_reports)
    _section("CombinationLayer", combination_reports)

    lines.append("=== Validering: tiktoken vs qwen2.5-tokenizer ===")
    if validation["status"] == "skipped":
        lines.append(f"qwen2.5-validering hoppades över: {validation['reason']}")
    else:
        for row in validation["rows"]:
            lines.append(
                f"  {row['tag']}: tiktoken={row['tiktoken']}, qwen2={row['qwen2']}, "
                f"avvikelse={row['deviation_pct']:+.2f}%"
            )
        lines.append(f"Medelavvikelse: {validation['mean_deviation_pct']:+.2f}%")
        lines.append(f"Trovärdighet: {validation['credibility']}")
    lines.append("")

    lines.append("=== Slutsats ===")
    lines.append(f"Utfall {verdict[0]}: {verdict[1]}")
    return "\n".join(lines)


def render_markdown(
    article9_reports: list[DatasetReport],
    combination_reports: list[DatasetReport],
    validation: dict,
    verdict: tuple[str, str],
    output_buffer: int,
) -> str:
    out: list[str] = []
    out.append("# I-6 token-mätning av Article9- och CombinationLayer-prompter")
    out.append("")
    out.append("## Bakgrund")
    out.append("")
    out.append(
        "I-6 (Issue #106) är pausad efter 14/16 fas 1-körningar. Ett av två "
        "pausfynd var att `OllamaProvider.generate_json` inte sätter `num_ctx` "
        "explicit i payloaden, vilket innebär att Ollama defaultar till 4096 "
        "tokens totalt för prompt + output. Hypotesen är att CombinationLayer "
        "v5-prompten plus långa testtexter plus modellens reasoning/JSON-output "
        "kan ha trunkerats tyst under iteration 2 och iteration 3:s "
        "LLM-baserade utvärdering. Se `docs/iteration_3_threshold_calibration.md` "
        "§ \"Pausorsak: num_ctx-flagga (parallell analys)\" för fullständig "
        "kontext."
    )
    out.append("")
    out.append("Detta dokument rapporterar empirisk token-mätning av de prompter "
               "som pipelinen faktiskt skickar till modellen.")
    out.append("")

    out.append("## Metod")
    out.append("")
    out.append(
        "Mätningen återanvänder pipelinens prompt-laddning "
        "(`gdpr_classifier.prompts.loader.load_prompt`) och pipelinens "
        "användarprompt-konstruktion verbatim "
        "(`{prompt.assembled_prompt}\\n\\nText att analysera:\\n<<<\\n{text}\\n>>>\\n`, "
        "exakt som `Article9Layer.detect` och `CombinationLayer.detect`)."
    )
    out.append("")
    out.append(
        f"- **Tokenizer:** tiktoken `cl100k_base` (primär). Token-mätning per "
        f"text räknar `system_prompt` + `user_prompt` separat och summerar "
        f"(motsvarar vad som konsumerar Ollamas kontextfönster).\n"
        f"- **Output-buffer:** {output_buffer} tokens "
        f"(`effective_tokens = prompt_tokens + {output_buffer}`).\n"
        f"- **Prompt-versioner:** Article9 `{ARTICLE9_VERSION}` "
        f"(matchar `Article9Layer` default), Combination `{COMBINATION_VERSION}` "
        f"(matchar `CombinationLayer` iteration 3-pin).\n"
        f"- **Dataset:** se per-layer-sektion nedan. Text-index = position i "
        f"JSON-array (0-indexerad), bevarad eftersom `load_dataset` itererar "
        f"över `json.load`-listan i fil-ordning.\n"
        f"- **Utfallströsklar (uppgift 2 spec):** A = 0 över {OVER_LIMIT} effective; "
        f"B = {BORDERLINE_PCT:.0f}-{TRUNCATION_PCT:.0f}% över ELLER kategori-max i "
        f"[{BORDERLINE_MIN}, {BORDERLINE_MAX}]; C = >{TRUNCATION_PCT:.0f}% över "
        f"ELLER någon kategori har max > {OVER_LIMIT}."
    )
    out.append("")

    def _layer_section(label: str, reports: list[DatasetReport]) -> None:
        out.append(f"## Resultat: {label}")
        out.append("")
        for r in reports:
            out.append(f"### Dataset: `{r.dataset_path}` (prompt {r.prompt_version})")
            out.append("")
            if r.skipped:
                out.append(f"_Skippad: {r.skip_reason}_")
                out.append("")
                continue
            pq = r.quantiles("prompt_tokens")
            eq = r.quantiles("effective_tokens")
            out.append(f"Antal texter mätta: **{r.n}**.")
            out.append("")
            out.append("| Statistik | Prompt tokens | Effective (prompt + buffer) |")
            out.append("|---|---|---|")
            out.append(f"| min | {pq['min']} | {eq['min']} |")
            out.append(f"| median | {pq['median']} | {eq['median']} |")
            out.append(f"| p75 | {pq['p75']} | {eq['p75']} |")
            out.append(f"| p90 | {pq['p90']} | {eq['p90']} |")
            out.append(f"| max | {pq['max']} | {eq['max']} |")
            out.append("")
            over = r.count_over(OVER_LIMIT)
            warn = r.count_over(WARNING_LIMIT)
            pct_over = (over / r.n * 100.0) if r.n else 0.0
            pct_warn = (warn / r.n * 100.0) if r.n else 0.0
            out.append(
                f"Texter med effective > {OVER_LIMIT}: **{over} "
                f"({pct_over:.2f}%)**. Texter med effective > {WARNING_LIMIT} "
                f"(varning): {warn} ({pct_warn:.2f}%)."
            )
            out.append("")
            out.append("**Per-kategori-statistik:**")
            out.append("")
            out.append("| Kategori | Antal texter | Max effective tokens | Antal > 4096 |")
            out.append("|---|---|---|---|")
            for cat in sorted(r.per_category.keys()):
                s = r.per_category[cat]
                out.append(
                    f"| `{cat}` | {s.count} | {s.max_effective} | {s.over_4096} |"
                )
            out.append("")
            out.append("**Topp 5 längsta prompts (text-index i JSON-array):**")
            out.append("")
            out.append("| Rang | Text-index | Prompt tokens | Effective tokens | Kategorier |")
            out.append("|---|---|---|---|---|")
            for rank, m in enumerate(r.top_n_longest(5), start=1):
                cats_str = ", ".join(m.categories) if m.categories else "—"
                out.append(
                    f"| {rank} | {m.idx} | {m.prompt_tokens} | "
                    f"{m.effective_tokens} | {cats_str} |"
                )
            out.append("")

    _layer_section("Article9Layer", article9_reports)
    _layer_section("CombinationLayer", combination_reports)

    out.append("## Validering: tiktoken cl100k_base vs Qwen2.5-tokenizer")
    out.append("")
    if validation["status"] == "skipped":
        out.append(f"_Validering hoppades över: {validation['reason']}_")
    else:
        out.append(
            "Stickprov: 10 prompts (5 Article9 + 5 Combination) valda "
            "deterministiskt med `random.Random(42).sample()`. Båda tokenizers "
            "applicerade på den fullständiga prompten (`system_prompt + \\n\\n + user_prompt`)."
        )
        out.append("")
        out.append("| Prompt | tiktoken | Qwen2.5 | Avvikelse (%) |")
        out.append("|---|---|---|---|")
        for row in validation["rows"]:
            out.append(
                f"| `{row['tag']}` | {row['tiktoken']} | {row['qwen2']} | "
                f"{row['deviation_pct']:+.2f}% |"
            )
        out.append("")
        out.append(
            f"**Medelavvikelse:** {validation['mean_deviation_pct']:+.2f}% "
            f"(negativ = tiktoken underskattar). "
            f"**Trovärdighet:** {validation['credibility']} "
            f"(`OTILLRÄCKLIG` om medelavvikelse < −10 %, annars `OK`)."
        )
    out.append("")

    out.append("## Slutsats")
    out.append("")
    out.append(f"**Utfall {verdict[0]}** — {verdict[1]}")
    out.append("")
    out.append("Klassificeringen är automatiskt beräknad av "
               "`tools/measure_prompt_tokens.py` enligt spec'ens uppgift 2-trösklar "
               "och inte tolkad i efterhand.")
    out.append("")
    out.append("Nästa beslut (num_ctx-fix och eventuell omkörning) tas av "
               "arkitekt-instans baserat på denna rapport.")
    out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Empirical token measurement for Article9Layer "
                    "and CombinationLayer prompts (I-6, issue #106)."
    )
    parser.add_argument(
        "--output-buffer",
        type=int,
        default=800,
        help="Tokens reserved for model output (default: 800).",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip Qwen2.5-tokenizer cross-validation.",
    )
    parser.add_argument(
        "--output-md",
        type=str,
        default="docs/iteration_3_token_measurement.md",
        help="Path to the markdown report output (relative paths resolved against repo root).",
    )
    args = parser.parse_args(argv)

    encoder = tiktoken.get_encoding("cl100k_base")

    article9_paths = [
        REPO_ROOT / "tests" / "data" / "iteration_2" / "article9_dataset.json",
        REPO_ROOT / "tests" / "data" / "iteration_3" / "article9_dataset.json",
        REPO_ROOT / "tests" / "data" / "iteration_1" / "test_dataset.json",
    ]
    combination_paths = [
        REPO_ROOT / "tests" / "data" / "iteration_2" / "combination_dataset.json",
        REPO_ROOT / "tests" / "data" / "iteration_3" / "combination_dataset.json",
    ]

    article9_reports = [
        measure_dataset(
            "article9", p, ARTICLE9_VERSION,
            encoder, args.output_buffer, "article9.",
        )
        for p in article9_paths
    ]
    combination_reports = [
        measure_dataset(
            "combination", p, COMBINATION_VERSION,
            encoder, args.output_buffer, "context.",
        )
        for p in combination_paths
    ]

    validation = validate_with_qwen(
        article9_reports, combination_reports, encoder, args.skip_validation
    )

    verdict = classify_outcome(article9_reports + combination_reports)

    stdout_text = render_stdout(
        article9_reports, combination_reports,
        validation, verdict, args.output_buffer,
    )
    print(stdout_text)

    md_text = render_markdown(
        article9_reports, combination_reports,
        validation, verdict, args.output_buffer,
    )
    out_path = Path(args.output_md)
    if not out_path.is_absolute():
        out_path = REPO_ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md_text, encoding="utf-8")
    print(f"\nMarkdown-rapport skriven: {_display_path(out_path)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
