"""Validates structural integrity of docs/combination_annotation_guidelines.md."""
import re
import sys
from pathlib import Path

GUIDE_PATH = Path(__file__).parent.parent / "docs" / "combination_annotation_guidelines.md"


def main() -> int:
    text = GUIDE_PATH.read_text(encoding="utf-8")

    h2_headings = re.findall(r"^## (\d+)\.", text, re.MULTILINE)
    h3_headings = re.findall(r"^### (\d+\.\d+)", text, re.MULTILINE)

    errors: list[str] = []

    if len(h2_headings) != 10:
        errors.append(f"Expected 10 H2 sections, found {len(h2_headings)}: {h2_headings}")

    sec4_h3 = [h for h in h3_headings if h.startswith("4.")]
    if len(sec4_h3) != 4:
        errors.append(f"Expected 4 H3 under section 4, found {len(sec4_h3)}: {sec4_h3}")

    sec5_h3 = [h for h in h3_headings if h.startswith("5.")]
    if len(sec5_h3) < 3:
        errors.append(f"Expected at least 3 H3 under section 5, found {len(sec5_h3)}: {sec5_h3}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1

    print("OK: docs/combination_annotation_guidelines.md structure is valid\n")
    print("Heading tree:")
    for line in text.splitlines():
        if re.match(r"^#{1,3} ", line):
            depth = len(line) - len(line.lstrip("#"))
            print("  " * (depth - 1) + line)

    return 0


if __name__ == "__main__":
    sys.exit(main())
