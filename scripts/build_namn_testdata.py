"""Temporary helper: generate + assert-validate NER name test entries for issue #45.

Run: python scripts/build_namn_testdata.py
Output: validated JSON entries ready to append to tests/data/iteration_1/test_dataset.json
"""
import json

CATEGORY = "article4.namn"

RAW = [
    (
        "Hej Anna Svensson, tack för att du hörde av dig angående ärendet.",
        ["Anna Svensson"],
        "NER: enkelt förnamn + efternamn i hälsningsfras",
    ),
    (
        "Mötet den 14 mars leddes av Lars-Göran Berg och protokollfördes av Maria Lindqvist.",
        ["Lars-Göran Berg", "Maria Lindqvist"],
        "NER: två namn i mötesanteckning, bindestreck i förnamn",
    ),
    (
        "Vi har tagit emot en förfrågan från Erik Johansson gällande tjänsten.",
        ["Erik Johansson"],
        "NER: namn i kundtjänstnotat",
    ),
    (
        "Enligt överenskommelse med Karin Holm ska leveransen ske nästa vecka.",
        ["Karin Holm"],
        "NER: namn i affärskorrespondens",
    ),
    (
        "Björn Petersson och Cecilia Norström deltog i workshopen om hållbarhet.",
        ["Björn Petersson", "Cecilia Norström"],
        "NER: två namn i verksamhetstext",
    ),
    (
        "Projektledare: Gunnar Strand. Ansvarig tekniker: Sofia Lund.",
        ["Gunnar Strand", "Sofia Lund"],
        "NER: namn i strukturerad projektbeskrivning",
    ),
    (
        "Chattlogg: Hej, jag heter Maja Hellström och undrar om ni kan hjälpa mig.",
        ["Maja Hellström"],
        "NER: namn i chattmeddelande, självpresentation",
    ),
    (
        "HR-notat: Anställd Per-Olof Lindberg påbörjar sin tjänst den första i månaden.",
        ["Per-Olof Lindberg"],
        "NER: namn i HR-dokument, bindestreck i förnamn",
    ),
    (
        "Undertecknad Therese Magnusson intygar att uppgifterna är korrekta.",
        ["Therese Magnusson"],
        "NER: namn i intyg",
    ),
    (
        "Enligt protokollet framförde Ingrid Karlsson synpunkter, vilket Fredrik Ek noterade.",
        ["Ingrid Karlsson", "Fredrik Ek"],
        "NER: två namn i formellt protokoll",
    ),
]


def build_findings(text: str, spans: list[str]) -> list[dict]:
    findings = []
    search_from = 0
    for span in spans:
        start = text.find(span, search_from)
        assert start != -1, f"Span {span!r} not found in text {text!r}"
        end = start + len(span)
        assert text[start:end] == span, (
            f"Index mismatch: text[{start}:{end}]={text[start:end]!r} != {span!r}"
        )
        findings.append({"category": CATEGORY, "start": start, "end": end, "text_span": span})
        search_from = end
    return findings


def main() -> None:
    entries = []
    for text, spans, description in RAW:
        findings = build_findings(text, spans)
        entries.append({"text": text, "description": description, "expected_findings": findings})

    print(json.dumps(entries, ensure_ascii=False, indent=2))
    print(f"\n# {len(entries)} entries validated OK", flush=True)


if __name__ == "__main__":
    main()
