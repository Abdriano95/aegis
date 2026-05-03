"""Test fixture: StubCombinationLayer.

This module is a test fixture, not a production layer. Its purpose is to
provide empirical evidence for Design Principle 2 (Issue #79): that the Layer
protocol schema contract (name property + detect(text) -> list[Finding]) is
sufficient to substitute one Layer implementation for another without modifying
Pipeline, Aggregator, or any core module.

The stub detects context signals via case-insensitive substring matching against
a hardcoded wordlist derived from tests/data/iteration_2/combination_dataset.json.
It produces output schema-identical to CombinationLayer: individual signal findings
with source "context.{yrke|plats|organisation}" plus an aggregate finding with
source "context.kombination".
"""

from __future__ import annotations

from gdpr_classifier.core.category import Category
from gdpr_classifier.core.finding import Finding

# Confidence for the aggregate finding. Must be >= 0.85 to trigger the
# Aggregator's high-confidence bypass (Beslut 21, GDPR art. 25), so the
# demonstration produces MEDIUM sensitivity without requiring Mechanism 3
# evidence from Layer 1/2. Chosen at 0.90 for a clear margin above the threshold.
_AGGREGATE_CONFIDENCE = 0.90

_SIGNAL_CONFIDENCE = 0.75

# Wordlist: (lowercase search term, Category, source tag).
# Words chosen based on vocabulary verified in combination_dataset.json:
# - "sjuksköterska" matches "Sjuksköterskan" / "sjuksköterskan" (prefix match)
# - "sahlgrenska" matches "Sahlgrenska Universitetssjukhuset" (partial name)
# - "hvitfeldtska" matches "Hvitfeldtska gymnasiet" (partial name)
_WORDLIST: list[tuple[str, Category, str]] = [
    # Yrken (occupations)
    ("sjuksköterska", Category.YRKE,         "context.yrke"),
    ("lärare",        Category.YRKE,         "context.yrke"),
    ("tandläkare",    Category.YRKE,         "context.yrke"),
    # Platser (places)
    ("stockholm",     Category.PLATS,        "context.plats"),
    ("göteborg",      Category.PLATS,        "context.plats"),
    ("malmö",         Category.PLATS,        "context.plats"),
    # Organisationer (organisations)
    ("volvo cars",    Category.ORGANISATION, "context.organisation"),
    ("sahlgrenska",   Category.ORGANISATION, "context.organisation"),
    ("hvitfeldtska",  Category.ORGANISATION, "context.organisation"),
]


class StubCombinationLayer:
    """Deterministic stub that mimics CombinationLayer's output schema.

    Uses a hardcoded wordlist and case-insensitive substring search instead of
    LLM inference. Returns individual signal findings for each match and an
    aggregate KOMBINATION finding (confidence=0.90) when >= 2 signals are found.
    Returns [] when < 2 signals are found, matching CombinationLayer's behavior
    when is_identifiable is false.

    Implements the Layer protocol: @property name + detect(text) -> list[Finding].
    """

    @property
    def name(self) -> str:
        return "combination"

    def detect(self, text: str) -> list[Finding]:
        """Detect wordlist matches and build schema-compatible findings.

        Span integrity is verified via assertion before return: every returned
        finding satisfies text[f.start:f.end] == f.text_span.
        """
        if not text:
            return []

        signal_findings: list[Finding] = []
        text_lower = text.lower()

        for word, category, source in _WORDLIST:
            search_start = 0
            while True:
                pos = text_lower.find(word, search_start)
                if pos == -1:
                    break
                end = pos + len(word)
                actual_span = text[pos:end]  # preserve original casing from text
                signal_findings.append(
                    Finding(
                        category=category,
                        start=pos,
                        end=end,
                        text_span=actual_span,
                        confidence=_SIGNAL_CONFIDENCE,
                        source=source,
                    )
                )
                search_start = pos + 1  # advance past current match to find next

        if len(signal_findings) < 2:
            return []

        # Build aggregate with mechanical min/max span over all signal findings
        # (matches combination_annotation_guidelines.md section 5.3)
        agg_start = min(f.start for f in signal_findings)
        agg_end = max(f.end for f in signal_findings)
        aggregate = Finding(
            category=Category.KOMBINATION,  # matches actual CombinationLayer output
            start=agg_start,
            end=agg_end,
            text_span=text[agg_start:agg_end],
            confidence=_AGGREGATE_CONFIDENCE,
            source="context.kombination",
        )

        all_findings = signal_findings + [aggregate]

        # Verify all spans exist in text at stated positions
        for f in all_findings:
            assert text[f.start:f.end] == f.text_span, (
                f"Span mismatch at [{f.start}:{f.end}]: "
                f"text gives {text[f.start:f.end]!r} but text_span is {f.text_span!r}"
            )

        return all_findings
