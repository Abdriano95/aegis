"""
export_candidates_to_csv.py

Konverterar article9_dataset_candidates.json till en CSV-fil
avsedd för manuell granskning i Google Sheets (FAS B, Issue #71).

Användning:
    python export_candidates_to_csv.py \
        --input tests/data/iteration_2/article9_dataset_candidates.json \
        --output tests/data/iteration_2/fas_b_granskning.csv

Kräver inga externa beroenden utöver Python 3.8+.
"""

import argparse
import csv
import json
import sys
from pathlib import Path


def format_findings(findings: list[dict]) -> str:
    """Formaterar expected_findings till läsbar sträng per kandidat.

    Exempel: [halsodata: "ont i knät" (128-138)] | [halsodata: "arbetsskada" (76-87)]
    """
    if not findings:
        return "(inga fynd — negativ kontroll)"

    parts = []
    for f in findings:
        category = f.get("category", "?").replace("article9.", "")
        span = f.get("text_span", "?")
        start = f.get("start", "?")
        end = f.get("end", "?")
        parts.append(f'[{category}: "{span}" ({start}-{end})]')

    return " | ".join(parts)


def format_categories(findings: list[dict]) -> str:
    """Returnerar unika kategorier per kandidat, kommaseparerade."""
    if not findings:
        return "negativ_kontroll"
    categories = sorted(
        {f.get("category", "?").replace("article9.", "") for f in findings}
    )
    return ", ".join(categories)


def load_candidates(path: Path) -> list[dict]:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Fel: Filen '{path}' hittades inte.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Fel: Ogiltig JSON i '{path}': {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, list):
        print("Fel: JSON-filen ska vara en lista av kandidater.", file=sys.stderr)
        sys.exit(1)

    return data


def build_rows(candidates: list[dict]) -> list[dict]:
    rows = []
    for i, candidate in enumerate(candidates, start=1):
        text = candidate.get("text", "").replace("\n", " ").strip()
        description = candidate.get("description", "").strip()
        findings = candidate.get("expected_findings", [])

        row = {
            "id": i,
            "kategori": format_categories(findings),
            "text": text,
            "description": description,
            "expected_findings": format_findings(findings),
            "antal_fynd": len(findings),
            # Johanna-kolumner
            "J_utfall": "",  # behåll / justera / stryk
            "J_kategori_ok": "",  # ja / nej
            "J_span_ok": "",  # ja / nej
            "J_sprak_ok": "",  # ja / nej / borderline
            "J_kommentar": "",
            # Abdulla-kolumner
            "A_utfall": "",
            "A_kategori_ok": "",
            "A_span_ok": "",
            "A_sprak_ok": "",
            "A_kommentar": "",
            # Konsensus-kolumner (fylls i gemensamt)
            "K_utfall": "",  # behåll / justera / stryk
            "K_justerad_finding": "",  # om justering: ny finding i läsbart format
            "K_kommentar": "",
        }
        rows.append(row)
    return rows


COLUMN_HEADERS = {
    "id": "ID",
    "kategori": "Kategori(er)",
    "text": "Text",
    "description": "Beskrivning",
    "expected_findings": "Förväntade fynd",
    "antal_fynd": "Antal fynd",
    "J_utfall": "J: behåll/justera/stryk",
    "J_kategori_ok": "J: kategori ok?",
    "J_span_ok": "J: span ok?",
    "J_sprak_ok": "J: språk ok?",
    "J_kommentar": "J: kommentar",
    "A_utfall": "A: behåll/justera/stryk",
    "A_kategori_ok": "A: kategori ok?",
    "A_span_ok": "A: span ok?",
    "A_sprak_ok": "A: språk ok?",
    "A_kommentar": "A: kommentar",
    "K_utfall": "K: utfall",
    "K_justerad_finding": "K: justerad finding",
    "K_kommentar": "K: kommentar",
}


def write_csv(rows: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        # utf-8-sig ger BOM som Google Sheets och Excel hanterar korrekt
        writer = csv.DictWriter(
            f,
            fieldnames=list(COLUMN_HEADERS.keys()),
            extrasaction="ignore",
        )
        writer.writerow(COLUMN_HEADERS)  # Skriver läsbara rubriker
        writer.writerows(rows)


def print_summary(candidates: list[dict], output_path: Path) -> None:
    from collections import Counter

    category_counts: Counter = Counter()
    negative = 0

    for c in candidates:
        findings = c.get("expected_findings", [])
        if not findings:
            negative += 1
        for f in findings:
            cat = f.get("category", "okänd").replace("article9.", "")
            category_counts[cat] += 1

    print(f"\nExporterade {len(candidates)} kandidater till '{output_path}'")
    print(f"\nKategorifördelning (antal fynd per kategori):")
    for cat, count in sorted(category_counts.items()):
        print(f"  {cat:<25} {count}")
    print(f"  {'negativa kontroller':<25} {negative}")
    print(f"\nTotalt antal fynd: {sum(category_counts.values())}")
    print(
        "\nImportera CSV-filen i Google Sheets via:\n"
        "  Arkiv → Importera → Ladda upp → Avgränsningstyp: Komma\n"
        "  Välj 'Ersätt aktuellt kalkylark' eller 'Nytt ark'.\n"
        "  Teckenkodning ska vara UTF-8 (BOM inkluderat)."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Konverterar article9-kandidater till CSV för FAS B-granskning."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("tests/data/iteration_2/article9_dataset_candidates.json"),
        help="Sökväg till kandidat-JSON-filen.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tests/data/iteration_2/fas_b_granskning.csv"),
        help="Sökväg till output-CSV-filen.",
    )
    args = parser.parse_args()

    candidates = load_candidates(args.input)
    rows = build_rows(candidates)
    write_csv(rows, args.output)
    print_summary(candidates, args.output)


if __name__ == "__main__":
    main()
