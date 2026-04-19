"""Temporary helper: generate + assert-validate test entries for issues #46 and #47.

Issue #46: locations (article4.adress) and organisations (context.organisation)
Issue #47: mixed texts with both NER entities and regex patterns

Run: python scripts/build_locations_orgs_mixed_testdata.py
Output: validated JSON entries ready to append to tests/data/iteration_1/test_dataset.json
"""
import json

ADRESS = "article4.adress"
ORGANISATION = "context.organisation"
NAMN = "article4.namn"
EMAIL = "article4.email"
TELEFON = "article4.telefonnummer"
PERSONNUMMER = "article4.personnummer"
IBAN = "article4.iban"

# (text, [(span, category), ...], description)
RAW_LOCATIONS = [
    (
        "Mötet hölls i Stockholm den tredje mars.",
        [("Stockholm", ADRESS)],
        "NER LOC: stadsnamn i möteskontext",
    ),
    (
        "Paketet levereras till Sveavägen 44 på fredag.",
        [("Sveavägen 44", ADRESS)],
        "NER LOC: gatuadress i leveransnotis",
    ),
    (
        "Kundbesöket är inbokat i Göteborg nästa vecka.",
        [("Göteborg", ADRESS)],
        "NER LOC: stad i kalenderpost",
    ),
    (
        "Tåget avgår från Malmö C kl. 08:15.",
        [("Malmö C", ADRESS)],
        "NER LOC: stationsnamn i resebokning",
    ),
    (
        "Lagret finns i Örebro och hanterar norra regionen.",
        [("Örebro", ADRESS)],
        "NER LOC: stad i verksamhetsbeskrivning",
    ),
]

RAW_ORGS = [
    (
        "Avtalet skrevs under av Volvo AB.",
        [("Volvo AB", ORGANISATION)],
        "NER ORG: bolagsnamn i avtalstext",
    ),
    (
        "Skatteverket har begärt in kompletterande uppgifter.",
        [("Skatteverket", ORGANISATION)],
        "NER ORG: myndighet i formell notis",
    ),
    (
        "Vi samarbetar med Acme Corp sedan 2018.",
        [("Acme Corp", ORGANISATION)],
        "NER ORG: bolagsnamn i samarbetstext",
    ),
    (
        "Fakturan gäller tjänster utförda åt Nordea Bank.",
        [("Nordea Bank", ORGANISATION)],
        "NER ORG: banknamn i fakturareferens",
    ),
    (
        "Kontraktet löper ut och Region Skåne har inte förlängt.",
        [("Region Skåne", ORGANISATION)],
        "NER ORG: regionnamn i kontraktstext",
    ),
]

RAW_MIXED = [
    (
        "Kontakta Anna Svensson på anna.svensson@foretag.se angående ärendet.",
        [("Anna Svensson", NAMN), ("anna.svensson@foretag.se", EMAIL)],
        "Blandad: NER namn + regex e-post",
    ),
    (
        "Erik Johansson, 820415-3421, är bosatt i Göteborg.",
        [("Erik Johansson", NAMN), ("820415-3421", PERSONNUMMER), ("Göteborg", ADRESS)],
        "Blandad: NER namn + regex personnummer + NER plats",
    ),
    (
        "Volvo AB har registrerat IBAN SE35 5000 0000 0549 1000 0003.",
        [("Volvo AB", ORGANISATION), ("SE35 5000 0000 0549 1000 0003", IBAN)],
        "Blandad: NER organisation + regex IBAN",
    ),
    (
        "Ring Karin Holm på 070-123 45 67 för mer info om projektet i Malmö.",
        [("Karin Holm", NAMN), ("070-123 45 67", TELEFON), ("Malmö", ADRESS)],
        "Blandad: NER namn + regex telefon + NER plats",
    ),
    (
        "Skatteverket kontaktade Lars Berg (lars.berg@privat.se) gällande deklarationen.",
        [("Skatteverket", ORGANISATION), ("Lars Berg", NAMN), ("lars.berg@privat.se", EMAIL)],
        "Blandad: NER organisation + NER namn + regex e-post",
    ),
]


def build_findings(text: str, span_category_pairs: list[tuple[str, str]]) -> list[dict]:
    findings = []
    search_from = 0
    for span, category in span_category_pairs:
        start = text.find(span, search_from)
        assert start != -1, f"Span {span!r} not found in text {text!r} (searching from {search_from})"
        end = start + len(span)
        assert text[start:end] == span, (
            f"Index mismatch: text[{start}:{end}]={text[start:end]!r} != {span!r}"
        )
        findings.append({"category": category, "start": start, "end": end, "text_span": span})
        search_from = end
    return findings


def main() -> None:
    entries = []
    for raw_list in (RAW_LOCATIONS, RAW_ORGS, RAW_MIXED):
        for text, span_category_pairs, description in raw_list:
            findings = build_findings(text, span_category_pairs)
            entries.append({"text": text, "description": description, "expected_findings": findings})

    print(json.dumps(entries, ensure_ascii=False, indent=2))
    print(f"\n# {len(entries)} entries validated OK", flush=True)


if __name__ == "__main__":
    main()
