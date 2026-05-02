#!/usr/bin/env python3
"""Validate the Article 9 test dataset schema.

Checks that the dataset file conforms to the required JSON schema,
verifies text spans, and checks for valid Category values.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

# Add the project root to sys.path so we can import from gdpr_classifier
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from gdpr_classifier.core.category import Category
except ImportError as e:
    print(f"Error importing Category: {e}", file=sys.stderr)
    print("Are you running this from the project root?", file=sys.stderr)
    sys.exit(1)


def validate_dataset(filepath: str) -> bool:
    """Validate a dataset file.
    
    Returns:
        True if valid, False if invalid.
    """
    path = Path(filepath)
    if not path.is_file():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        return False

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        return False
        
    if not isinstance(data, list):
        print("Error: Top-level JSON must be a list.", file=sys.stderr)
        return False
        
    errors = 0
    warnings = 0
    category_counts = Counter()
    
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            print(f"Error [Item {i}]: Item is not a dictionary.", file=sys.stderr)
            errors += 1
            continue
            
        text = item.get("text")
        if text is None or not isinstance(text, str):
            print(f"Error [Item {i}]: Missing or invalid 'text' field.", file=sys.stderr)
            errors += 1
            continue
            
        description = item.get("description")
        if description is None or not isinstance(description, str):
            print(f"Error [Item {i}]: Missing or invalid 'description' field.", file=sys.stderr)
            errors += 1
            continue
            
        expected_findings = item.get("expected_findings")
        if expected_findings is None or not isinstance(expected_findings, list):
            print(f"Error [Item {i}]: Missing or invalid 'expected_findings' list.", file=sys.stderr)
            errors += 1
            continue
            
        # Check for overlaps
        spans = []
            
        for j, finding in enumerate(expected_findings):
            if not isinstance(finding, dict):
                print(f"Error [Item {i}, Finding {j}]: Finding is not a dictionary.", file=sys.stderr)
                errors += 1
                continue
                
            cat_str = finding.get("category")
            if cat_str is None:
                print(f"Error [Item {i}, Finding {j}]: Missing 'category'.", file=sys.stderr)
                errors += 1
                continue
            
            try:
                cat = Category(cat_str)
                category_counts[cat.value] += 1
            except ValueError:
                print(f"Error [Item {i}, Finding {j}]: Invalid category '{cat_str}'.", file=sys.stderr)
                errors += 1
                continue
                
            start = finding.get("start")
            end = finding.get("end")
            text_span = finding.get("text_span")
            
            if not isinstance(start, int) or not isinstance(end, int):
                print(f"Error [Item {i}, Finding {j}]: 'start' and 'end' must be integers.", file=sys.stderr)
                errors += 1
                continue
                
            if start < 0 or end < 0:
                print(f"Error [Item {i}, Finding {j}]: 'start' and 'end' must be >= 0.", file=sys.stderr)
                errors += 1
                continue
                
            if start >= end:
                print(f"Error [Item {i}, Finding {j}]: 'start' must be < 'end'.", file=sys.stderr)
                errors += 1
                continue
                
            if end > len(text):
                print(f"Error [Item {i}, Finding {j}]: 'end' exceeds text length.", file=sys.stderr)
                errors += 1
                continue
                
            if text_span is None or not isinstance(text_span, str):
                print(f"Error [Item {i}, Finding {j}]: Missing or invalid 'text_span'.", file=sys.stderr)
                errors += 1
                continue
                
            actual_span = text[start:end]
            if actual_span != text_span:
                print(f"Error [Item {i}, Finding {j}]: text_span mismatch. Expected '{text_span}', got '{actual_span}'.", file=sys.stderr)
                errors += 1
                continue
                
            spans.append((start, end, cat_str))
            
        # Check for overlaps
        spans.sort(key=lambda x: x[0])
        for idx in range(len(spans) - 1):
            s1_start, s1_end, s1_cat = spans[idx]
            s2_start, s2_end, s2_cat = spans[idx + 1]
            if s1_end > s2_start:
                print(f"Warning [Item {i}]: Overlapping findings: '{s1_cat}' [{s1_start}:{s1_end}] and '{s2_cat}' [{s2_start}:{s2_end}].")
                warnings += 1
                
    # Print summary
    print("\n" + "="*50)
    print("VALIDATION SUMMARY")
    print("="*50)
    print(f"Total texts: {len(data)}")
    print(f"Total findings: {sum(category_counts.values())}")
    print(f"Errors found: {errors}")
    print(f"Warnings: {warnings}")
    
    if category_counts:
        print("\nCategory Distribution:")
        print("-" * 30)
        for cat, count in sorted(category_counts.items()):
            print(f"  {cat}: {count}")
    
    print("="*50)
            
    return errors == 0


def main():
    parser = argparse.ArgumentParser(description="Validate an Article 9 dataset file.")
    parser.add_argument("dataset_path", help="Path to the JSON dataset file to validate.")
    args = parser.parse_args()
    
    is_valid = validate_dataset(args.dataset_path)
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
