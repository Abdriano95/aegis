#!/usr/bin/env python3
"""
Validate combination-layer dataset (FAS A candidates or FAS B final dataset)
for Issue #73.

Two-role design:
  Pre-FAS-B:  Validate candidate file directly after FAS A generation to
              catch hallucinated spans before manual review.
  Post-FAS-B: Validate final dataset to confirm reviewers did not introduce
              schema errors during consensus work.

Strict consistency check: If a context.kombination aggregate finding is
present, its start/end must equal min(starts)/max(ends) of the individual
findings in the same entry.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ALLOWED_INDIVIDUAL_CATEGORIES = {
    "context.yrke",
    "context.plats",
    "context.organisation",
}
AGGREGATE_CATEGORY = "context.kombination"
ALLOWED_SPECIFICITY = {"låg", "mellan", "hög"}


def validate_entry(entry: dict, entry_index: int) -> list[str]:
    """Validate a single dataset entry. Returns a list of error messages."""
    errors: list[str] = []

    if not isinstance(entry, dict):
        return [f"Entry {entry_index}: not a dict."]

    text = entry.get("text")
    if not isinstance(text, str):
        errors.append(f"Entry {entry_index}: 'text' must be a string.")
        return errors
    if len(text) < 30:
        errors.append(
            f"Entry {entry_index}: 'text' has {len(text)} chars, minimum is 30."
        )

    if not isinstance(entry.get("description"), str):
        errors.append(f"Entry {entry_index}: 'description' must be a string.")

    findings = entry.get("expected_findings")
    if not isinstance(findings, list):
        errors.append(f"Entry {entry_index}: 'expected_findings' must be a list.")
        return errors

    individual: list[dict] = []
    aggregates: list[dict] = []

    for j, finding in enumerate(findings):
        loc = f"Entry {entry_index}, finding {j}"

        if not isinstance(finding, dict):
            errors.append(f"{loc}: not a dict.")
            continue

        category = finding.get("category")
        if category not in ALLOWED_INDIVIDUAL_CATEGORIES and category != AGGREGATE_CATEGORY:
            errors.append(
                f"{loc}: invalid category '{category}'. "
                f"Must be one of {sorted(ALLOWED_INDIVIDUAL_CATEGORIES | {AGGREGATE_CATEGORY})}."
            )
            continue

        text_span = finding.get("text_span")
        if not isinstance(text_span, str) or len(text_span) < 5:
            errors.append(
                f"{loc}: 'text_span' must be a string of at least 5 characters."
            )
            continue

        start = finding.get("start")
        end = finding.get("end")
        if not isinstance(start, int) or not isinstance(end, int):
            errors.append(f"{loc}: 'start' and 'end' must be integers.")
            continue
        if not (0 <= start < end <= len(text)):
            errors.append(
                f"{loc}: invalid offsets start={start}, end={end} "
                f"(text length={len(text)})."
            )
            continue
        if text[start:end] != text_span:
            errors.append(
                f"{loc}: text_span '{text_span}' not found at "
                f"start={start}, end={end}. Got '{text[start:end]}'."
            )
            continue

        if category == AGGREGATE_CATEGORY:
            is_identifiable = finding.get("is_identifiable")
            if is_identifiable is not True:
                errors.append(
                    f"{loc}: aggregate finding must have is_identifiable=True."
                )
            aggregates.append(finding)
        else:
            specificity = finding.get("specificity_level")
            if specificity not in ALLOWED_SPECIFICITY:
                errors.append(
                    f"{loc}: invalid specificity_level '{specificity}' "
                    f"(must be {' | '.join(sorted(ALLOWED_SPECIFICITY))})."
                )
            individual.append(finding)

    if len(aggregates) > 1:
        errors.append(
            f"Entry {entry_index}: only one aggregate finding allowed, "
            f"found {len(aggregates)}."
        )

    if len(aggregates) == 1:
        if len(individual) < 2:
            errors.append(
                f"Entry {entry_index}: aggregate finding requires at least 2 "
                f"individual findings, found {len(individual)}."
            )
        else:
            agg = aggregates[0]
            expected_start = min(f["start"] for f in individual)
            expected_end = max(f["end"] for f in individual)
            if agg.get("start") != expected_start:
                errors.append(
                    f"Entry {entry_index}: aggregate start={agg.get('start')}, "
                    f"expected min(starts)={expected_start}."
                )
            if agg.get("end") != expected_end:
                errors.append(
                    f"Entry {entry_index}: aggregate end={agg.get('end')}, "
                    f"expected max(ends)={expected_end}."
                )

    return errors


def generate_summary(
    entries: list[dict], errors: dict[int, list[str]]
) -> dict:
    total = len(entries)
    invalid_indices = set(errors.keys())
    valid = total - len(invalid_indices)

    individual_counts: Counter = Counter()
    agg_count = 0
    entries_without_findings = 0
    entries_with_aggregate = 0
    entries_with_signals_no_aggregate = 0

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        findings = entry.get("expected_findings", [])
        if not isinstance(findings, list):
            continue

        has_aggregate = any(
            f.get("category") == AGGREGATE_CATEGORY for f in findings if isinstance(f, dict)
        )
        has_individual = any(
            f.get("category") in ALLOWED_INDIVIDUAL_CATEGORIES
            for f in findings
            if isinstance(f, dict)
        )

        if not findings:
            entries_without_findings += 1
        elif has_aggregate:
            entries_with_aggregate += 1
        elif has_individual:
            entries_with_signals_no_aggregate += 1

        for f in findings:
            if not isinstance(f, dict):
                continue
            cat = f.get("category")
            if cat == AGGREGATE_CATEGORY:
                agg_count += 1
            elif cat in ALLOWED_INDIVIDUAL_CATEGORIES:
                signal = cat.split(".")[-1]
                individual_counts[signal] += 1

    total_individual = sum(individual_counts.values())
    return {
        "total_entries": total,
        "valid_entries": valid,
        "invalid_entries": len(invalid_indices),
        "total_findings": total_individual + agg_count,
        "individual_findings": total_individual,
        "individual_counts": dict(individual_counts),
        "aggregate_findings": agg_count,
        "entries_without_findings": entries_without_findings,
        "entries_with_aggregate": entries_with_aggregate,
        "entries_with_signals_no_aggregate": entries_with_signals_no_aggregate,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a combination-layer dataset JSON (FAS A candidates or "
            "FAS B final dataset)."
        )
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to dataset JSON (candidates or final).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any entry has errors. Default behavior.",
    )
    args = parser.parse_args()

    input_path: Path = args.input
    if not input_path.is_file():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(input_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        print(f"Error: Invalid JSON: {exc}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, list):
        print("Error: Top-level JSON must be a list.", file=sys.stderr)
        sys.exit(1)

    all_errors: dict[int, list[str]] = {}
    for i, entry in enumerate(data):
        entry_errors = validate_entry(entry, i)
        if entry_errors:
            all_errors[i] = entry_errors

    summary = generate_summary(data, all_errors)

    if all_errors:
        print("=== VALIDATION FAILED ===", file=sys.stderr)
        for entry_errors in all_errors.values():
            for msg in entry_errors:
                print(msg, file=sys.stderr)
        print(
            f"\n{summary['invalid_entries']} entries failed validation.",
            file=sys.stderr,
        )
        sys.exit(1)

    ic = summary["individual_counts"]
    yrke = ic.get("yrke", 0)
    plats = ic.get("plats", 0)
    org = ic.get("organisation", 0)

    print("=== VALIDATION OK ===")
    print(f"Input: {input_path}")
    print()
    print(
        f"Entries: {summary['total_entries']} "
        f"({summary['valid_entries']} valid, {summary['invalid_entries']} invalid)"
    )
    print()
    print(f"Findings: {summary['total_findings']} totala")
    print(
        f"  Individuella signaler:  {summary['individual_findings']} "
        f"(yrke: {yrke}, plats: {plats}, organisation: {org})"
    )
    print(
        f"  Aggregat-fynd:          {summary['aggregate_findings']} "
        f"(context.kombination)"
    )
    print()
    print("Fördelning:")
    print(
        f"  Entries med aggregat:                    "
        f"{summary['entries_with_aggregate']}  (Cell 1 + del av Cell 2)"
    )
    print(
        f"  Entries med signaler men inget aggregat: "
        f"{summary['entries_with_signals_no_aggregate']}  (Cell 4 + del av Cell 2)"
    )
    print(
        f"  Entries utan findings:                   "
        f"{summary['entries_without_findings']}   (Cell 3)"
    )
    print()
    print("OK — datasetet är schema-giltigt och konsistent.")
    sys.exit(0)


if __name__ == "__main__":
    main()
