"""Validation script for Issue #77 (I-10): 10 new longer test entries.

Generates and validates test entries with longer, realistic Swedish texts
combining multiple pattern and NER categories. Each text simulates a
realistic document type: emails, HR notes, internal reports, customer
service tickets, meeting minutes.

Method: text.find() with search_from offset (same as #45–#47).
Assertion: text[start:end] == text_span for every finding.

Run: python scripts/build_iteration2_pattern_ner_testdata.py
Output: Validated JSON entries (printed to stdout) ready to insert into
        tests/data/iteration_1/test_dataset.json
"""
import json
import sys

# Category constants
PERSONNUMMER = "article4.personnummer"
EMAIL = "article4.email"
TELEFON = "article4.telefonnummer"
IBAN = "article4.iban"
BETALKORT = "article4.betalkort"
NAMN = "article4.namn"
ADRESS = "article4.adress"
ORGANISATION = "context.organisation"


# --- Luhn check (PNR uses 10-digit form, cards use standard right-to-left) ---

def luhn_pnr(digits_10: str) -> bool:
    """Luhn check for Swedish personnummer (10-digit form YYMMDDXXXX)."""
    assert len(digits_10) == 10, f"Expected 10 digits, got {len(digits_10)}"
    nums = [int(d) for d in digits_10]
    total = 0
    for i, d in enumerate(nums):
        if i % 2 == 0:
            doubled = d * 2
            total += doubled - 9 if doubled > 9 else doubled
        else:
            total += d
    return total % 10 == 0


def luhn_card(card_str: str) -> bool:
    """Standard Luhn check for payment card numbers (right-to-left)."""
    digits = [int(d) for d in card_str if d.isdigit()]
    digits.reverse()
    total = 0
    for i, d in enumerate(digits):
        if i % 2 == 1:
            doubled = d * 2
            total += doubled - 9 if doubled > 9 else doubled
        else:
            total += d
    return total % 10 == 0


def iban_mod97(iban_str: str) -> bool:
    """IBAN mod-97 check (ISO 13616)."""
    iban = iban_str.replace(" ", "")
    rearranged = iban[4:] + iban[:4]
    numeric = ""
    for ch in rearranged:
        if ch.isdigit():
            numeric += ch
        else:
            numeric += str(ord(ch) - ord("A") + 10)
    return int(numeric) % 97 == 1


# --- The 10 new test entries ---
# Format: (text, [(span, category), ...], description)
# Spans listed in order of first appearance for search_from to work.

RAW_ENTRIES = [
    # --- Entry 1: Kundtjänstmejl (namn + personnummer + email + telefon) ---
    (
        "Hej,\n\nJag heter Sofia Ekström och mitt personnummer är 930715-1002. "
        "Jag har ett ärende gällande min senaste faktura som inte stämmer. "
        "Ni kan nå mig på sofia.ekstrom@mail.se eller ringa 073-555 12 34.\n\n"
        "Med vänliga hälsningar,\nSofia Ekström",
        [
            ("Sofia Ekström", NAMN),
            ("930715-1002", PERSONNUMMER),
            ("sofia.ekstrom@mail.se", EMAIL),
            ("073-555 12 34", TELEFON),
        ],
        "Längre: Kundtjänstmejl med namn, personnummer, e-post och telefon",
    ),
    # --- Entry 2: HR-anteckning (namn + personnummer + organisation + adress) ---
    (
        "HR-notat 2026-03-15: Nyanställd Marcus Lindgren, personnummer 880312-1006, "
        "börjar som systemutvecklare på Ericsson AB den 1 april. "
        "Han är bosatt i Linköping och ska arbeta från kontoret på Teknikvägen 8.",
        [
            ("Marcus Lindgren", NAMN),
            ("880312-1006", PERSONNUMMER),
            ("Ericsson AB", ORGANISATION),
            ("Linköping", ADRESS),
            ("Teknikvägen 8", ADRESS),
        ],
        "Längre: HR-anteckning med namn, personnummer, organisation och adresser",
    ),
    # --- Entry 3: Intern rapport med IBAN (organisation + namn + IBAN + email) ---
    (
        "Ekonomirapport Q1 2026\n\n"
        "Handelsbanken har bekräftat att överföringen till leverantören "
        "Anna-Karin Bergström genomfördes den 12 mars. Beloppet krediterades "
        "IBAN SE90 8000 5555 4444 3333 2222. Vid frågor, kontakta ekonomiavdelningen "
        "på ekonomi@foretaget.se.",
        [
            ("Handelsbanken", ORGANISATION),
            ("Anna-Karin Bergström", NAMN),
            ("SE90 8000 5555 4444 3333 2222", IBAN),
            ("ekonomi@foretaget.se", EMAIL),
        ],
        "Längre: Intern ekonomirapport med organisation, namn, IBAN och e-post",
    ),
    # --- Entry 4: Kundtjänstärende med betalkort (namn + betalkort + telefon + email) ---
    (
        "Ärende #4521 – Omtvistad transaktion\n\n"
        "Kund: Henrik Sjöberg\n"
        "Kortnummer: 4532 8901 2345 6785\n"
        "Henrik rapporterar en okänd debitering på 2 450 kr den 28 februari. "
        "Han nås enklast via telefon 070-888 99 11 eller på henrik.sjoberg@example.com. "
        "Ärendet eskaleras till bedrägerienheten.",
        [
            ("Henrik Sjöberg", NAMN),
            ("4532 8901 2345 6785", BETALKORT),
            ("070-888 99 11", TELEFON),
            ("henrik.sjoberg@example.com", EMAIL),
        ],
        "Längre: Kundtjänstärende med namn, betalkort, telefon och e-post",
    ),
    # --- Entry 5: Mötesprotokoll (namn x3 + organisation + adress) ---
    (
        "Protokoll från styrelsemöte 2026-04-10\n\n"
        "Närvarande: Eva Nilsson (ordförande), Karl Hedlund (ledamot) och "
        "Fatima Al-Hassan (sekreterare).\n\n"
        "Mötet hölls i Göteborgs lokaler hos Sigma IT. "
        "Eva Nilsson öppnade mötet och noterade att samtliga ledamöter var närvarande. "
        "Nästa möte planeras till den 8 maj.",
        [
            ("Eva Nilsson", NAMN),
            ("Karl Hedlund", NAMN),
            ("Fatima Al-Hassan", NAMN),
            ("Göteborg", ADRESS),
            ("Sigma IT", ORGANISATION),
        ],
        "Längre: Mötesprotokoll med tre namn, organisation och adress",
    ),
    # --- Entry 6: Flerstyckes-mejl med personnummer + IBAN + namn + organisation ---
    (
        "Hej Lena,\n\n"
        "Jag skriver angående utbetalningen till Jonas Wikström. "
        "Hans personnummer är 760924-1000 och beloppet ska sättas in på "
        "kontot med IBAN SE84 1200 3456 7890 1234 5678.\n\n"
        "Swedbank har bekräftat att kontot är aktivt. "
        "Kan du verifiera uppgifterna och genomföra överföringen?\n\n"
        "Tack på förhand,\nLena",
        [
            ("Jonas Wikström", NAMN),
            ("760924-1000", PERSONNUMMER),
            ("SE84 1200 3456 7890 1234 5678", IBAN),
            ("Swedbank", ORGANISATION),
        ],
        "Längre: Flerstyckes-mejl med namn, personnummer, IBAN och organisation",
    ),
    # --- Entry 7: Incidentrapport (namn + email + telefon + organisation + adress) ---
    (
        "Incidentrapport – IT-säkerhet 2026-04-22\n\n"
        "Rapportör: Björn Axelsson, bjorn.axelsson@teknikab.se, telefon 08-123 45 67.\n"
        "Incidenten upptäcktes av Teknik AB:s driftteam i Uppsala. "
        "En obehörig inloggning registrerades från en extern IP-adress kl. 03:14. "
        "Åtkomsten spärrades omedelbart och ärendet har rapporterats till CERT-SE.",
        [
            ("Björn Axelsson", NAMN),
            ("bjorn.axelsson@teknikab.se", EMAIL),
            ("08-123 45 67", TELEFON),
            ("Teknik AB", ORGANISATION),
            ("Uppsala", ADRESS),
            ("CERT-SE", ORGANISATION),
        ],
        "Längre: IT-incidentrapport med namn, e-post, telefon, organisation och adress",
    ),
    # --- Entry 8: Avtalsdokument med betalkort + namn + organisation (kort text med 3 kat) ---
    (
        "Betalningsbekräftelse\n\n"
        "Kund: Petra Forsberg, anställd vid SEB Kort AB.\n"
        "Betalning mottagen via kort 4012 8888 8888 8811 den 15 april 2026. "
        "Beloppet 12 500 kr har bokförts. Kvitto skickas till petra.forsberg@seb.se.",
        [
            ("Petra Forsberg", NAMN),
            ("SEB Kort AB", ORGANISATION),
            ("4012 8888 8888 8811", BETALKORT),
            ("petra.forsberg@seb.se", EMAIL),
        ],
        "Längre: Betalningsbekräftelse med namn, organisation, betalkort och e-post",
    ),
    # --- Entry 9: Ärendelogg med personnummer + namn + telefon + adress + organisation ---
    (
        "Ärendelogg – Socialförvaltningen Malmö kommun\n\n"
        "Ärende öppnat: 2026-02-20\n"
        "Klient: Amira Hassan, personnummer 950503-1006, boende Rosengård.\n"
        "Kontaktuppgifter: 076-200 33 44.\n\n"
        "Anteckning: Klienten har begärt stödinsats enligt SoL kap. 4 §1. "
        "Handläggare tilldelad. Uppföljningsmöte planeras inom två veckor.",
        [
            ("Socialförvaltningen", ORGANISATION),
            ("Malmö kommun", ORGANISATION),
            ("Amira Hassan", NAMN),
            ("950503-1006", PERSONNUMMER),
            ("Rosengård", ADRESS),
            ("076-200 33 44", TELEFON),
        ],
        "Längre: Ärendelogg med personnummer, namn, telefon, adress och organisationer",
    ),
    # --- Entry 10: Faktura-mejl med IBAN + namn + email + organisation + adress ---
    (
        "Faktura #2026-0891\n\n"
        "Från: Nordström Consulting AB, Vasagatan 12, Stockholm\n"
        "Till: Oskar Blom, oskar.blom@kund.se\n\n"
        "Belopp: 45 000 kr exkl. moms.\n"
        "Betalning sker till IBAN SE69 3000 1234 5678 9012 3456 senast 2026-05-15.\n\n"
        "Vid frågor, kontakta oss på faktura@nordstromconsulting.se.",
        [
            ("Nordström Consulting AB", ORGANISATION),
            ("Vasagatan 12", ADRESS),
            ("Stockholm", ADRESS),
            ("Oskar Blom", NAMN),
            ("oskar.blom@kund.se", EMAIL),
            ("SE69 3000 1234 5678 9012 3456", IBAN),
            ("faktura@nordstromconsulting.se", EMAIL),
        ],
        "Längre: Faktura-mejl med IBAN, namn, e-post, organisation och adresser",
    ),
]


def build_findings(text: str, span_category_pairs: list[tuple[str, str]]) -> list[dict]:
    """Build findings with machine-computed indices via text.find() + search_from."""
    findings = []
    search_from = 0
    for span, category in span_category_pairs:
        start = text.find(span, search_from)
        assert start != -1, (
            f"Span {span!r} not found in text (searching from {search_from}):\n{text!r}"
        )
        end = start + len(span)
        # Critical assertion: verify that slice matches span exactly
        assert text[start:end] == span, (
            f"Index mismatch: text[{start}:{end}]={text[start:end]!r} != {span!r}"
        )
        findings.append({
            "category": category,
            "start": start,
            "end": end,
            "text_span": span,
        })
        search_from = end
    return findings


def validate_checksums(entries: list[dict]) -> None:
    """Validate Luhn (PNR, cards) and mod-97 (IBAN) for all findings."""
    for i, entry in enumerate(entries):
        for finding in entry["expected_findings"]:
            span = finding["text_span"]
            cat = finding["category"]

            if cat == PERSONNUMMER:
                # Extract 10-digit form for Luhn
                digits = span.replace("-", "").replace("+", "")
                digits_10 = digits[-10:]
                assert luhn_pnr(digits_10), (
                    f"Entry {i}: PNR {span!r} fails Luhn (10-digit: {digits_10})"
                )
                print(f"  ✓ PNR {span} Luhn OK")

            elif cat == IBAN:
                assert iban_mod97(span), (
                    f"Entry {i}: IBAN {span!r} fails mod-97"
                )
                print(f"  ✓ IBAN {span} mod-97 OK")

            elif cat == BETALKORT:
                assert luhn_card(span), (
                    f"Entry {i}: Card {span!r} fails Luhn"
                )
                print(f"  ✓ Card {span} Luhn OK")


def main() -> None:
    entries = []
    errors = 0

    print("=" * 60)
    print("Validating 10 new test entries for Issue #77 (I-10)")
    print("=" * 60)

    for i, (text, span_category_pairs, description) in enumerate(RAW_ENTRIES):
        print(f"\nEntry {i + 1}: {description}")
        try:
            findings = build_findings(text, span_category_pairs)
            entry = {
                "text": text,
                "description": description,
                "expected_findings": findings,
            }
            entries.append(entry)
            for f in findings:
                print(f"  [{f['category']}] {f['start']}:{f['end']} = {f['text_span']!r}")
        except AssertionError as e:
            print(f"  ✗ ASSERTION FAILED: {e}")
            errors += 1

    print("\n" + "=" * 60)
    print("Checksum validation (Luhn / mod-97)")
    print("=" * 60)

    try:
        validate_checksums(entries)
    except AssertionError as e:
        print(f"  ✗ CHECKSUM ASSERTION FAILED: {e}")
        errors += 1

    print("\n" + "=" * 60)

    if errors > 0:
        print(f"FAILED: {errors} error(s) found.")
        sys.exit(1)

    # Summary statistics
    categories_per_entry = [
        len(set(f["category"] for f in e["expected_findings"]))
        for e in entries
    ]
    multi_category = sum(1 for c in categories_per_entry if c >= 3)
    multiline = sum(1 for e in entries if "\n" in e["text"])
    has_iban = sum(1 for e in entries if any(
        f["category"] == IBAN for f in e["expected_findings"]
    ))
    has_card = sum(1 for e in entries if any(
        f["category"] == BETALKORT for f in e["expected_findings"]
    ))
    has_pnr = sum(1 for e in entries if any(
        f["category"] == PERSONNUMMER for f in e["expected_findings"]
    ))
    total_findings = sum(len(e["expected_findings"]) for e in entries)

    print(f"ALL {len(entries)} entries validated OK – 0 AssertionErrors")
    print(f"Total findings: {total_findings}")
    print(f"Entries with ≥3 categories: {multi_category} (krav: ≥5)")
    print(f"Multiline entries (\\n): {multiline} (krav: ≥2)")
    print(f"Entries with IBAN: {has_iban} (krav: ≥1)")
    print(f"Entries with betalkort: {has_card} (krav: ≥1)")
    print(f"Entries with personnummer: {has_pnr} (krav: ≥1)")
    print("=" * 60)

    # Print JSON for manual insertion
    print("\n--- JSON output (for manual insertion into test_dataset.json) ---\n")
    print(json.dumps(entries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
