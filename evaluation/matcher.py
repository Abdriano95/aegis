"""Matcher module for evaluation.

Handles matching of predicted findings against ground-truth labeled findings
on a span-level basis, factoring in overlap and confidence.
"""

from __future__ import annotations

from dataclasses import dataclass

from evaluation.dataset.labeled_finding import LabeledFinding
from gdpr_classifier.core.category import Category
from gdpr_classifier.core.finding import Finding


CATEGORY_ALIASES: frozenset[frozenset[Category]] = frozenset({
    frozenset({Category.ADRESS, Category.PLATS}),
})


def _are_aliased(a: Category, b: Category) -> bool:
    """Return True if a and b belong to the same alias group.

    Self-aliasing returns False; exact category equality is handled by Pass 1
    in match() and should not pass through the alias path.
    """
    if a == b:
        return False
    return frozenset({a, b}) in CATEGORY_ALIASES


@dataclass(frozen=True)
class MatchResult:
    true_positives: list[tuple[Finding, LabeledFinding]]
    false_positives: list[Finding]
    false_negatives: list[LabeledFinding]


def match(predicted: list[Finding], expected: list[LabeledFinding]) -> MatchResult:
    """Matches predicted findings against expected findings.

    Rules:
      1. Same category.
      1b. Category aliasing: pairs in CATEGORY_ALIASES match each other if Pass 1
          (exact category) found no match for the prediction. Exact match always
          takes priority per prediction.
      2. Overlapping text position: predicted.start < expected.end and expected.start < predicted.end.
      3. Each expected LabeledFinding can only match one predicted Finding.
      4. Overlap resolution: the Finding with the highest confidence claims the expected finding.
      5. Unmatched expected = false negative. Unmatched predicted = false positive.
    """
    sorted_predictions = sorted(predicted, key=lambda p: p.confidence, reverse=True)
    matched_expected_ids: set[int] = set()

    true_positives: list[tuple[Finding, LabeledFinding]] = []
    false_positives: list[Finding] = []

    for p in sorted_predictions:
        match_found = False

        # Pass 1: exact category match
        for e in expected:
            if id(e) not in matched_expected_ids:
                if p.category == e.category and p.start < e.end and e.start < p.end:
                    true_positives.append((p, e))
                    matched_expected_ids.add(id(e))
                    match_found = True
                    break  # p is matched, stop searching expected list for this specific p

        # Pass 2: alias category match (only if Pass 1 found nothing)
        if not match_found:
            for e in expected:
                if id(e) not in matched_expected_ids:
                    if _are_aliased(p.category, e.category) and p.start < e.end and e.start < p.end:
                        true_positives.append((p, e))
                        matched_expected_ids.add(id(e))
                        match_found = True
                        break

        if not match_found:
            false_positives.append(p)

    false_negatives = [e for e in expected if id(e) not in matched_expected_ids]

    return MatchResult(
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
    )
